import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from classification import TARGET_COLUMN, engineer_features


def evaluate_classification(
    data_path: Path,
    artifacts_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> float:
    df = pd.read_csv(data_path)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing required target column: {TARGET_COLUMN}")

    y = df[TARGET_COLUMN].copy()
    df_engineered = engineer_features(df)
    X = df_engineered.drop(
        columns=[TARGET_COLUMN, "RecommendationCount", "RecommenderCount"],
        errors="ignore",
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = joblib.load(artifacts_dir / "stacking_clf.pkl")
    preprocessor = joblib.load(artifacts_dir / "preprocessor.pkl")
    label_encoder = joblib.load(artifacts_dir / "label_encoder.pkl")

    X_test_t = preprocessor.transform(X_test)
    y_pred_encoded = model.predict(X_test_t)
    y_pred = label_encoder.inverse_transform(y_pred_encoded)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Classification accuracy (test_size={test_size}): {accuracy:.6f}")
    print(f"Rows -> train: {len(X_train)}, test: {len(X_test)}")
    return float(accuracy)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate saved classification artifacts on a 20% test split."
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path("Data/classification/train_data.csv"),
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("ml/artifacts/classification"),
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    evaluate_classification(
        data_path=args.data_path,
        artifacts_dir=args.artifacts_dir,
        test_size=args.test_size,
        random_state=args.random_state,
    )
