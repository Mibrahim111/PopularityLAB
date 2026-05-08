import argparse
import __main__
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

from save_reg_preprocessor import RegressionPreprocessor, TARGET_COLUMN, engineer_features


def evaluate_regression(
    data_path: Path,
    artifacts_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> float:
    df = pd.read_csv(data_path)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing required target column: {TARGET_COLUMN}")

    y = df[TARGET_COLUMN].copy()
    y_log = np.log1p(y)
    df_engineered = engineer_features(df)
    # Match notebook flow: only drop the regression target.
    X = df_engineered.drop(columns=[TARGET_COLUMN], errors="ignore")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_log,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )

    # `reg_preprocessor.pkl` was serialized from script scope (`__main__`).
    # Register class name here so the pickle can be loaded reliably.
    setattr(__main__, "RegressionPreprocessor", RegressionPreprocessor)

    model = joblib.load(artifacts_dir / "stacking_reg.pkl")
    preprocessor = joblib.load(artifacts_dir / "reg_preprocessor.pkl")

    X_test_t = preprocessor.transform(X_test)
    y_pred = np.asarray(model.predict(X_test_t), dtype=float)

    r2 = r2_score(y_test.to_numpy(), y_pred)
    # Optional: also show raw-space R2 for debugging comparability.
    y_test_raw = np.expm1(y_test.to_numpy())
    y_pred_raw = np.clip(np.expm1(y_pred), a_min=0.0, a_max=None)
    r2_raw = r2_score(y_test_raw, y_pred_raw)

    print(f"Regression R2 (test_size={test_size}): {r2:.6f}")
    print(f"Rows -> train: {len(X_train)}, test: {len(X_test)}")
    return float(r2)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate saved regression artifacts on a 20% test split."
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path("Data/regression/train_data.csv"),
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("ml/artifacts/regression"),
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    evaluate_regression(
        data_path=args.data_path,
        artifacts_dir=args.artifacts_dir,
        test_size=args.test_size,
        random_state=args.random_state,
    )
