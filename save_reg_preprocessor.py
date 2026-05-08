import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder

TARGET_COLUMN = "RecommendationCount"
DEFAULT_DATA_PATH = Path("data/regression/train_data.csv")
DEFAULT_ARTIFACT_PATH = Path("ml/artifacts/reg_preprocessor.pkl")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df_processed = df.copy()

    text_cols = ["ShortDescrip", "DetailedDescrip", "AboutText"]
    text_cols = [col for col in text_cols if col in df_processed.columns]

    if text_cols:
        for col in text_cols:
            df_processed[f"{col}_length"] = df_processed[col].fillna("").astype(str).str.len()
            df_processed[f"{col}_word_count"] = (
                df_processed[col].fillna("").astype(str).str.split().str.len()
            )

        combined_text = df_processed[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
        df_processed["total_text_length"] = combined_text.str.len()
        df_processed["total_word_count"] = combined_text.str.split().str.len()
        df_processed["has_website"] = (df_processed.get("Website", "").fillna("") != "").astype(int)

        df_processed = df_processed.drop(columns=text_cols)

    interaction_pairs = [
        ("SteamSpyOwners", "SteamSpyPlayersEstimate"),
        ("PriceFinal", "Metacritic"),
        ("DLCCount", "AchievementCount"),
        ("DeveloperCount", "PublisherCount"),
    ]

    for feat1, feat2 in interaction_pairs:
        if feat1 in df_processed.columns and feat2 in df_processed.columns:
            df_processed[f"{feat1}_x_{feat2}"] = df_processed[feat1] * df_processed[feat2]
            df_processed[f"{feat1}_div_{feat2}"] = np.where(
                df_processed[feat2] != 0,
                np.log1p(df_processed[feat1]) / (np.log1p(df_processed[feat2]) + 1e-6),
                0,
            )

    category_cols = [col for col in df_processed.columns if col.startswith("Category")]
    genre_cols = [col for col in df_processed.columns if col.startswith("Genre")]
    platform_cols = [col for col in df_processed.columns if col.startswith("Platform")]

    df_processed["num_categories"] = (
        df_processed[category_cols].sum(axis=1) if category_cols else 0
    )
    df_processed["num_genres"] = df_processed[genre_cols].sum(axis=1) if genre_cols else 0
    df_processed["num_platforms"] = (
        df_processed[platform_cols].sum(axis=1) if platform_cols else 0
    )

    skewed_features = ["SteamSpyOwners", "SteamSpyPlayersEstimate", "ScreenshotCount", "DLCCount"]
    for feat in skewed_features:
        if feat in df_processed.columns:
            df_processed[f"{feat}_log"] = np.log1p(df_processed[feat])

    id_url_cols = [
        col
        for col in df_processed.columns
        if any(x in col.lower() for x in ["id", "url", "email", "image", "background", "header"])
    ]
    df_processed = df_processed.drop(columns=id_url_cols, errors="ignore")

    return df_processed


class RegressionPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self) -> None:
        self.numeric_features_: list[str] = []
        self.categorical_features_: list[str] = []
        self.numeric_imputer_: SimpleImputer | None = None
        self.categorical_imputer_: SimpleImputer | None = None
        self.label_encoders_: dict[str, LabelEncoder] = {}
        self.feature_order_: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "RegressionPreprocessor":
        X_work = X.copy()
        self.numeric_features_ = X_work.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_features_ = X_work.select_dtypes(include=["object", "string"]).columns.tolist()

        if self.numeric_features_:
            self.numeric_imputer_ = SimpleImputer(strategy="median")
            X_work.loc[:, self.numeric_features_] = self.numeric_imputer_.fit_transform(
                X_work[self.numeric_features_]
            )

        if self.categorical_features_:
            self.categorical_imputer_ = SimpleImputer(strategy="most_frequent")
            X_work.loc[:, self.categorical_features_] = self.categorical_imputer_.fit_transform(
                X_work[self.categorical_features_]
            )

            for col in self.categorical_features_:
                le = LabelEncoder()
                X_work[col] = le.fit_transform(X_work[col].astype(str))
                self.label_encoders_[col] = le

        self.feature_order_ = X_work.columns.tolist()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_work = X.copy()

        for col in self.feature_order_:
            if col not in X_work.columns:
                X_work[col] = np.nan
        X_work = X_work[self.feature_order_]

        if self.numeric_features_ and self.numeric_imputer_ is not None:
            X_work.loc[:, self.numeric_features_] = self.numeric_imputer_.transform(
                X_work[self.numeric_features_]
            )

        if self.categorical_features_:
            if self.categorical_imputer_ is not None:
                X_work.loc[:, self.categorical_features_] = self.categorical_imputer_.transform(
                    X_work[self.categorical_features_]
                )
            for col in self.categorical_features_:
                le = self.label_encoders_[col]
                known_classes = set(le.classes_)
                values = X_work[col].astype(str)
                values = values.where(values.isin(known_classes), "unknown")
                if "unknown" not in known_classes:
                    le.classes_ = np.append(le.classes_, "unknown")
                X_work[col] = le.transform(values)

        return X_work


def build_and_save_preprocessor(
    data_path: Path = DEFAULT_DATA_PATH, artifact_path: Path = DEFAULT_ARTIFACT_PATH
) -> Path:
    df = pd.read_csv(data_path)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing required target column: {TARGET_COLUMN}")

    df_processed = engineer_features(df)
    X = df_processed.drop(columns=[TARGET_COLUMN], errors="ignore")
    y = df_processed[TARGET_COLUMN].copy()
    _ = np.log1p(y)

    preprocessor = RegressionPreprocessor()
    preprocessor.fit(X)

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, artifact_path)
    return artifact_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and save regression preprocessor artifact."
    )
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--artifact-path", type=Path, default=DEFAULT_ARTIFACT_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    saved_path = build_and_save_preprocessor(
        data_path=args.data_path, artifact_path=args.artifact_path
    )
    print(f"Saved regression preprocessor to: {saved_path}")
