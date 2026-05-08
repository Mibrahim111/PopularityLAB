import argparse
import json
import logging
from pathlib import Path
from typing import Any

import catboost as cb
import joblib
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import StackingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

LOGGER = logging.getLogger(__name__)
DEFAULT_ARTIFACTS_DIR = Path("ml/artifacts")
DEFAULT_TRAIN_DATA = Path("data/classification/train_data.csv")
TARGET_COLUMN = "GamePopularity"
RANDOM_STATE = 42

# ==========================================
# 1. DATA ENGINEERING & PREPROCESSING
# ==========================================
def engineer_features(df):
    """
    Applies the exact feature engineering steps from the notebook/script,
    adapted for the classification task.
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
        df_processed['has_website'] = (
            df_processed.get('Website', pd.Series(index=df.index)).fillna('') != ''
        ).astype(int)

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
    id_url_cols = [
        col for col in df_processed.columns
        if any(x in col.lower() for x in ['id', 'url', 'email', 'image', 'background', 'header'])
    ]
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


def _tune_base_models(
    X_train_t: Any,
    y_train: np.ndarray,
    X_val_t: Any,
    y_val: np.ndarray,
    num_classes: int,
    n_trials: int,
) -> dict[str, dict[str, Any]]:
    def tune_xgb() -> dict[str, Any]:
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 120, 320),
                "max_depth": trial.suggest_int("max_depth", 4, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 8),
            }
            model = xgb.XGBClassifier(
                objective="multi:softprob",
                eval_metric="mlogloss",
                num_class=num_classes,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                **params,
            )
            model.fit(X_train_t, y_train)
            pred = model.predict(X_val_t)
            return float(f1_score(y_val, pred, average="macro", zero_division=0))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def tune_lgbm() -> dict[str, Any]:
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 120, 320),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 24, 128),
                "max_depth": trial.suggest_int("max_depth", 4, 12),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
            }
            model = lgb.LGBMClassifier(
                objective="multiclass",
                random_state=RANDOM_STATE,
                n_jobs=-1,
                verbose=-1,
                **params,
            )
            model.fit(X_train_t, y_train)
            pred = model.predict(X_val_t)
            return float(f1_score(y_val, pred, average="macro", zero_division=0))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def tune_catboost() -> dict[str, Any]:
        X_train_dense = X_train_t.toarray() if hasattr(X_train_t, "toarray") else X_train_t
        X_val_dense = X_val_t.toarray() if hasattr(X_val_t, "toarray") else X_val_t

        def objective(trial: optuna.Trial) -> float:
            params = {
                "iterations": trial.suggest_int("iterations", 120, 320),
                "depth": trial.suggest_int("depth", 4, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-3, 10.0, log=True),
            }
            model = cb.CatBoostClassifier(
                loss_function="MultiClass",
                random_seed=RANDOM_STATE,
                verbose=0,
                **params,
            )
            model.fit(X_train_dense, y_train)
            pred = model.predict(X_val_dense).reshape(-1)
            return float(f1_score(y_val, pred, average="macro", zero_division=0))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    return {"xgb": tune_xgb(), "lgbm": tune_lgbm(), "catboost": tune_catboost()}


def _tune_meta_model(
    base_estimators: list[tuple[str, Any]],
    X_train_t: Any,
    y_train: np.ndarray,
    X_val_t: Any,
    y_val: np.ndarray,
    n_trials: int,
) -> tuple[StackingClassifier, dict[str, Any], float]:
    best_model: StackingClassifier | None = None
    best_params: dict[str, Any] = {}
    best_score = -np.inf

    def objective(trial: optuna.Trial) -> float:
        nonlocal best_model, best_params, best_score
        meta_params = {
            "C": trial.suggest_float("C", 1e-3, 10.0, log=True),
            "max_iter": 4000,
            "random_state": RANDOM_STATE,
        }
        stack = StackingClassifier(
            estimators=base_estimators,
            final_estimator=LogisticRegression(**meta_params),
            cv=3,
            n_jobs=-1,
        )
        stack.fit(X_train_t, y_train)
        pred = stack.predict(X_val_t)
        score = float(f1_score(y_val, pred, average="macro", zero_division=0))
        if score > best_score:
            best_score = score
            best_params = meta_params
            best_model = stack
        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    if best_model is None:
        raise RuntimeError("Failed to tune stacking meta-model.")
    return best_model, best_params, best_score


def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    precision, recall, _, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
    }


def _extract_top_features(model: Any, feature_names: list[str], top_k: int = 12) -> list[dict[str, float]]:
    if hasattr(model, "feature_importances_"):
        raw_importance = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "estimators_"):
        # Stacking model fallback: use average importance from tree-based base models.
        importances = []
        for estimator in model.estimators_:
            if hasattr(estimator, "feature_importances_"):
                importances.append(np.asarray(estimator.feature_importances_, dtype=float))
        if not importances:
            return []
        raw_importance = np.mean(importances, axis=0)
    else:
        return []

    if raw_importance.shape[0] != len(feature_names):
        return []

    order = np.argsort(raw_importance)[::-1][:top_k]
    return [
        {"feature": feature_names[idx], "importance": float(raw_importance[idx])}
        for idx in order
    ]


# ==========================================
# 4. PIPELINE EXECUTION & ARTIFACT SAVING
# ==========================================
def train_pipeline(
    data_path: Path = DEFAULT_TRAIN_DATA,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    n_trials: int = 20,
):
    df = pd.read_csv(data_path)

    # Target definition
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing required target column: {TARGET_COLUMN}")
    y = df[TARGET_COLUMN].copy()

    # Feature Engineering
    df_engineered = engineer_features(df)

    # Drop classification target and old regression target if exists
    drop_cols = [TARGET_COLUMN]
    if 'RecommendationCount' in df_engineered.columns:
        drop_cols.append('RecommendationCount')
    if 'RecommenderCount' in df_engineered.columns:
        drop_cols.append('RecommenderCount')

    X = df_engineered.drop(columns=drop_cols, errors='ignore')

    # Encode target
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y)

    # Leakage-safe train/val/test split
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X,
        y_encoded,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_holdout,
        y_holdout,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=y_holdout,
    )

    preprocessor = _build_preprocessor(X_train)
    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t = preprocessor.transform(X_val)
    X_test_t = preprocessor.transform(X_test)

    LOGGER.info("Tuning base models with Optuna (n_trials=%d)", n_trials)
    # tuned_base = _tune_base_models(
    #     X_train_t=X_train_t,
    #     y_train=y_train,
    #     X_val_t=X_val_t,
    #     y_val=y_val,
    #     num_classes=len(target_encoder.classes_),
    #     n_trials=n_trials,
    # )

    xgb_model = xgb.XGBClassifier(
        objective="multi:softprob",
        eval_metric="mlogloss",
        num_class=len(target_encoder.classes_),
        random_state=RANDOM_STATE,
        n_jobs=-1,
        # **tuned_base["xgb"],
    )
    lgbm_model = lgb.LGBMClassifier(
        objective="multiclass",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
        # **tuned_base["lgbm"],
    )
    cb_model = cb.CatBoostClassifier(
        loss_function="MultiClass",
        random_seed=RANDOM_STATE,
        verbose=0,
        # **tuned_base["catboost"],
    )
    base_estimators = [("xgb", xgb_model), ("lgbm", lgbm_model), ("catboost", cb_model)]

    LOGGER.info("Tuning stacking meta-model with Optuna (n_trials=%d)", n_trials)
    # best_model, tuned_meta, val_macro_f1 = _tune_meta_model(
    #     base_estimators=base_estimators,
    #     X_train_t=X_train_t,
    #     y_train=y_train,
    #     X_val_t=X_val_t,
    #     y_val=y_val,
    #     n_trials=n_trials,
    # )
    tuned_meta = {
        "C": 1.0,
        "max_iter": 4000,
        "random_state": RANDOM_STATE,
    }
    best_model = StackingClassifier(
        estimators=base_estimators,
        final_estimator=LogisticRegression(**tuned_meta),
        cv=5,
        n_jobs=1,
    )

    best_model.fit(X_train_t, y_train)

    val_pred = best_model.predict(X_val_t)
    val_macro_f1 = float(f1_score(y_val, val_pred, average="macro", zero_division=0))

    test_pred = best_model.predict(X_test_t)
    test_metrics = _compute_metrics(y_test, test_pred)
    test_confusion_matrix = confusion_matrix(y_test, test_pred).tolist()

    per_class = precision_recall_fscore_support(y_test, test_pred, average=None, zero_division=0)
    per_class_metrics = {
        cls: {
            "precision": float(per_class[0][idx]),
            "recall": float(per_class[1][idx]),
            "f1": float(per_class[2][idx]),
        }
        for idx, cls in enumerate(target_encoder.classes_)
    }

    roc_auc_ovr = None
    if hasattr(best_model, "predict_proba"):
        probs = best_model.predict_proba(X_test_t)
        try:
            roc_auc_ovr = float(roc_auc_score(y_test, probs, multi_class="ovr"))
        except ValueError:
            roc_auc_ovr = None

    # Save Model and Preprocessing Artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    clf_path = artifacts_dir / "stacking_clf.pkl"
    preprocessor_path = artifacts_dir / "preprocessor.pkl"
    encoder_path = artifacts_dir / "label_encoder.pkl"
    metrics_path = artifacts_dir / "classification_metrics.json"
    importance_path = artifacts_dir / "feature_importance.json"

    joblib.dump(best_model, clf_path)
    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(target_encoder, encoder_path)

    feature_names = preprocessor.get_feature_names_out().tolist()
    top_features = _extract_top_features(best_model, feature_names)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "best_model": "stacking_tuned",
                "validation_macro_f1": val_macro_f1,
                # "tuned_params": {"xgb": tuned_base["xgb"], "lgbm": tuned_base["lgbm"], "catboost": tuned_base["catboost"], "meta": tuned_meta},
                "test_metrics": test_metrics,
                "test_confusion_matrix": test_confusion_matrix,
                "test_per_class": per_class_metrics,
                "test_roc_auc_ovr": roc_auc_ovr,
            },
            handle,
            indent=2,
        )
    with importance_path.open("w", encoding="utf-8") as handle:
        json.dump({"top_features": top_features}, handle, indent=2)

    LOGGER.info("Saved classifier artifact (stacking_tuned): %s", clf_path)
    LOGGER.info("Saved preprocessor artifact: %s", preprocessor_path)
    LOGGER.info("Saved label encoder artifact: %s", encoder_path)
    LOGGER.info("Saved classification metrics: %s", metrics_path)
    LOGGER.info("Saved feature importance: %s", importance_path)

    return test_metrics, {"best_model": "stacking_tuned", "roc_auc_ovr": roc_auc_ovr}


# ==========================================
# 5. PREDICTION ON UNSEEN TEST DATA
# ==========================================
def predict_pipeline(
    test_data_path: Path,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    output_path: Path = Path("classification_predictions.csv")
):
    df = pd.read_csv(test_data_path)

    model = joblib.load(artifacts_dir / "stacking_clf.pkl")
    preprocessor = joblib.load(artifacts_dir / "preprocessor.pkl")
    target_encoder = joblib.load(artifacts_dir / "label_encoder.pkl")

    # Feature engineering
    df_engineered = engineer_features(df)

    # Remove target columns if accidentally present
    df_engineered = df_engineered.drop(columns=['GamePopularity', 'RecommendationCount', 'RecommenderCount'], errors='ignore')

    transformed = preprocessor.transform(df_engineered)
    preds_encoded = model.predict(transformed)
    preds_labels = target_encoder.inverse_transform(preds_encoded)

    output_df = df.copy()
    output_df['PredictedGamePopularity'] = preds_labels
    output_df.to_csv(output_path, index=False)
    LOGGER.info("Saved predictions to %s", output_path)

    return output_df


# ==========================================
# 6. EXAMPLE USAGE
# ==========================================
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train or run the classification model pipeline.")
    parser.add_argument("--mode", choices=["train", "predict"], default="train")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_TRAIN_DATA)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    parser.add_argument("--n-trials", type=int, default=20)
    parser.add_argument("--output-path", type=Path, default=Path("classification_predictions.csv"))
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _parse_args()

    if args.mode == "train":
        LOGGER.info("Starting classification training from %s", args.data_path)
        test_metrics, info = train_pipeline(
            data_path=args.data_path,
            artifacts_dir=args.artifacts_dir,
            n_trials=args.n_trials,
        )
        LOGGER.info("Selected model: %s", info["best_model"])
        LOGGER.info("Test metrics: %s", test_metrics)
        LOGGER.info("Test ROC-AUC OVR: %s", info["roc_auc_ovr"])
    else:
        LOGGER.info("Running classification prediction from %s", args.data_path)
        predict_pipeline(
            test_data_path=args.data_path,
            artifacts_dir=args.artifacts_dir,
            output_path=args.output_path,
        )