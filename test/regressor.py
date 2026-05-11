import argparse
import json
import logging
from pathlib import Path

import catboost as cb
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import StackingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

LOGGER = logging.getLogger(__name__)
DEFAULT_ARTIFACTS_DIR = Path("ml/artifacts")
DEFAULT_TRAIN_DATA = Path("data/regression/train_data.csv")
TARGET_COLUMN = "RecommendationCount"
RANDOM_STATE = 42

# ==========================================
# 1. DATA ENGINEERING & PREPROCESSING
# ==========================================
def engineer_features(df):
    """
    Applies the exact feature engineering steps from the notebook.
    """
    df_processed = df.copy()

    # Text features
    text_cols = ['ShortDescrip', 'DetailedDescrip', 'AboutText']
    text_cols = [col for col in text_cols if col in df_processed.columns]

    if text_cols:
        for col in text_cols:
            df_processed[f'{col}_length'] = df_processed[col].fillna('').astype(str).str.len()
            df_processed[f'{col}_word_count'] = df_processed[col].fillna('').astype(str).str.split().str.len()
        
        combined_text = df_processed[text_cols].fillna('').astype(str).agg(' '.join, axis=1)
        df_processed['total_text_length'] = combined_text.str.len()
        df_processed['total_word_count'] = combined_text.str.split().str.len()
        df_processed['has_website'] = (df_processed.get('Website', pd.Series(index=df.index)).fillna('') != '').astype(int)
        
        df_processed = df_processed.drop(columns=text_cols)

    # Interaction features
    interaction_pairs = [
        ('SteamSpyOwners', 'SteamSpyPlayersEstimate'),
        ('PriceFinal', 'Metacritic'),
        ('DLCCount', 'AchievementCount'),
        ('DeveloperCount', 'PublisherCount'),
    ]

    for feat1, feat2 in interaction_pairs:
        if feat1 in df_processed.columns and feat2 in df_processed.columns:
            df_processed[f'{feat1}_x_{feat2}'] = df_processed[feat1] * df_processed[feat2]
            df_processed[f'{feat1}_div_{feat2}'] = np.where(
                df_processed[feat2] != 0, 
                np.log1p(df_processed[feat1]) / (np.log1p(df_processed[feat2]) + 1e-6),
                0
            )

    # Count features
    category_cols = [col for col in df_processed.columns if col.startswith('Category')]
    genre_cols = [col for col in df_processed.columns if col.startswith('Genre')]
    platform_cols = [col for col in df_processed.columns if col.startswith('Platform')]

    df_processed['num_categories'] = df_processed[category_cols].sum(axis=1) if category_cols else 0
    df_processed['num_genres'] = df_processed[genre_cols].sum(axis=1) if genre_cols else 0
    df_processed['num_platforms'] = df_processed[platform_cols].sum(axis=1) if platform_cols else 0

    # Skewed features
    skewed_features = ['SteamSpyOwners', 'SteamSpyPlayersEstimate', 'ScreenshotCount', 'DLCCount']
    for feat in skewed_features:
        if feat in df_processed.columns:
            df_processed[f'{feat}_log'] = np.log1p(df_processed[feat])

    # Drop ID/URL columns
    id_url_cols = [col for col in df_processed.columns if any(x in col.lower() for x in ['id', 'url', 'email', 'image', 'background', 'header'])]
    df_processed = df_processed.drop(columns=id_url_cols, errors='ignore')

    return df_processed

def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=[np.number, bool]).columns.tolist()
    categorical_cols = [col for col in X.columns if col not in numeric_cols]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ]
    )

def _build_reference_stacking_model() -> tuple[StackingRegressor, dict[str, dict[str, float | int | str]]]:
    
    xgb_params = {
        "n_estimators": 800,
        "max_depth": 9,
        "learning_rate": 0.04,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 2,
        "gamma": 0.5,
        "reg_alpha": 0.6,
        "reg_lambda": 1.3,
        "objective": "reg:squarederror",
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": 0,
    }
    cb_params = {
        "iterations": 800,
        "learning_rate": 0.04,
        "depth": 8,
        "l2_leaf_reg": 3,
        "subsample": 0.85,
        "colsample_bylevel": 0.85,
        "bagging_temperature": 0.8,
        "random_strength": 0.5,
        "random_seed": RANDOM_STATE,
        "verbose": 0,
        "task_type": "CPU",
    }
    lgb_params = {
        "n_estimators": 800,
        "max_depth": 9,
        "learning_rate": 0.04,
        "num_leaves": 100,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_samples": 20,
        "lambda_l1": 0.1,
        "lambda_l2": 1.0,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": -1,
    }
    base_models = [
        ("xgb", xgb.XGBRegressor(**xgb_params)),
        ("cb", cb.CatBoostRegressor(**cb_params)),
        ("lgb", lgb.LGBMRegressor(**lgb_params)),
    ]
    meta_learner = Ridge(alpha=1.0, random_state=RANDOM_STATE)
    model = StackingRegressor(estimators=base_models, final_estimator=meta_learner, cv=5, n_jobs=1)
    return model, {"xgb": xgb_params, "catboost": cb_params, "lgbm": lgb_params, "meta": {"alpha": 1.0}}


def _regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    nonzero_mask = np.abs(y_true) > 1e-8
    if np.any(nonzero_mask):
        mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100.0)
    else:
        mape = None
    return {"rmse": rmse, "mae": mae, "r2": r2, "mape_nonzero": mape}

# ==========================================
# 3. PIPELINE EXECUTION & ARTIFACT SAVING
# ==========================================
def train_pipeline(
    data_path: Path = DEFAULT_TRAIN_DATA,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
):
    df = pd.read_csv(data_path)
    
    # Target definition
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing required target column: {TARGET_COLUMN}")
    y = df[TARGET_COLUMN].copy()
    y_log = np.log1p(y)
    
    # Feature Engineering
    df_engineered = engineer_features(df)
    X = df_engineered.drop(columns=[TARGET_COLUMN, 'GamePopularity'], errors='ignore')
    
    X_train, X_test, y_train_log, y_test_log = train_test_split(
        X, y_log, test_size=0.2, random_state=RANDOM_STATE, shuffle=True
    )

    preprocessor = _build_preprocessor(X_train)
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    model, model_params = _build_reference_stacking_model()
    model.fit(X_train_t, y_train_log.to_numpy())

    pred_log = model.predict(X_test_t)
    y_test_raw = np.expm1(y_test_log.to_numpy())
    test_pred_raw = np.clip(np.expm1(pred_log), a_min=0, a_max=None)
    test_metrics = _regression_metrics(y_test_raw, test_pred_raw)
    residuals = y_test_raw - test_pred_raw
    log_space_rmse = float(np.sqrt(mean_squared_error(y_test_log.to_numpy(), pred_log)))
    
    # Save Model and Preprocessing Artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    reg_path = artifacts_dir / "stacking_reg.pkl"
    preprocessor_path = artifacts_dir / "preprocessor.pkl"
    metrics_path = artifacts_dir / "regression_metrics.json"

    joblib.dump(model, reg_path)
    joblib.dump(preprocessor, preprocessor_path)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "best_model": "stacking_reference_notebook",
                "log_space_rmse": log_space_rmse,
                "model_params": model_params,
                "test_metrics": test_metrics,
                "prediction_summary": {
                    "prediction_min": float(np.min(test_pred_raw)),
                    "prediction_max": float(np.max(test_pred_raw)),
                    "prediction_mean": float(np.mean(test_pred_raw)),
                },
                "residual_summary": {
                    "residual_mean": float(np.mean(residuals)),
                    "residual_std": float(np.std(residuals)),
                    "residual_p95_abs": float(np.percentile(np.abs(residuals), 95)),
                },
            },
            handle,
            indent=2,
        )

    LOGGER.info("Saved regressor artifact (stacking_reference_notebook): %s", reg_path)
    LOGGER.info("Saved preprocessor artifact: %s", preprocessor_path)
    LOGGER.info("Saved regression metrics: %s", metrics_path)
        
    return test_metrics, "stacking_reference_notebook"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the regression model pipeline.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_TRAIN_DATA)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _parse_args()
    LOGGER.info("Starting regression training from %s", args.data_path)
    test_metrics, best_model = train_pipeline(data_path=args.data_path, artifacts_dir=args.artifacts_dir)
    LOGGER.info("Selected model: %s", best_model)
    LOGGER.info("Regression test metrics: %s", test_metrics)
