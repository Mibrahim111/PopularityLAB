import __main__
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from classification import engineer_features as classify_engineer_features
from test.save_reg_preprocessor import RegressionPreprocessor, engineer_features as reg_engineer_features

LOGGER = logging.getLogger(__name__)


class InferenceEngine:
    """Loads artifacts once and serves single-row inference."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.classification_dir = artifacts_dir / "classification"
        self.regression_dir = artifacts_dir / "regression"

        self.feature_importance = self._load_feature_importance(
            self.classification_dir / "feature_importance.json"
        )
        self.top_features: set[str] = {
            item["feature"]
            for item in self.feature_importance.get("top_features", [])
            if isinstance(item, dict) and "feature" in item
        }
        self._load_artifacts()
        LOGGER.info("Inference engine loaded artifacts successfully from %s", artifacts_dir)

    def _load_artifacts(self) -> None:
        self._assert_exists(self.classification_dir, "classification artifacts directory")
        self._assert_exists(self.regression_dir, "regression artifacts directory")

        classification_model_path = self.classification_dir / "stacking_clf.pkl"
        classification_preprocessor_path = self.classification_dir / "preprocessor.pkl"
        classification_label_encoder_path = self.classification_dir / "label_encoder.pkl"
        regression_model_path = self.regression_dir / "stacking_reg.pkl"
        regression_preprocessor_path = self.regression_dir / "reg_preprocessor.pkl"

        for path in (
            classification_model_path,
            classification_preprocessor_path,
            classification_label_encoder_path,
            regression_model_path,
            regression_preprocessor_path,
        ):
            self._assert_exists(path, "artifact")

        # reg_preprocessor.pkl may have been serialized from script (__main__) scope.
        setattr(__main__, "RegressionPreprocessor", RegressionPreprocessor)

        self.stacking_clf = joblib.load(classification_model_path)
        self.classification_preprocessor = joblib.load(classification_preprocessor_path)
        self.label_encoder = joblib.load(classification_label_encoder_path)
        self.stacking_reg = joblib.load(regression_model_path)
        self.regression_preprocessor = joblib.load(regression_preprocessor_path)

        self.classification_expected_columns = self._expected_columns(self.classification_preprocessor)
        self.regression_expected_columns = self._expected_columns(self.regression_preprocessor)
        self.regression_uses_log_target = self._load_regression_log_target_flag(
            self.regression_dir / "regression_metrics.json"
        )

        if not self.classification_expected_columns:
            raise RuntimeError("Classification preprocessor does not expose expected input columns.")
        if not self.regression_expected_columns:
            raise RuntimeError("Regression preprocessor does not expose expected input columns.")

    def predict_classification(self, features: dict[str, Any]) -> dict[str, Any]:
        frame = self._to_dataframe(features)
        engineered = classify_engineer_features(frame)
        aligned = self._align_columns(engineered, self.classification_expected_columns)
        transformed = self.classification_preprocessor.transform(aligned)
        label_idx = self.stacking_clf.predict(transformed)[0]
        probabilities = self.stacking_clf.predict_proba(transformed)[0]
        prediction = self.label_encoder.inverse_transform([label_idx])[0]

        return {
            "prediction": prediction,
            "probabilities": {
                cls: float(prob)
                for cls, prob in zip(self.label_encoder.classes_, probabilities, strict=True)
            },
        }

    def predict_regression(self, features: dict[str, Any]) -> dict[str, float]:
        frame = self._to_dataframe(features)
        engineered = reg_engineer_features(frame)
        aligned = self._align_columns(
            engineered,
            self.regression_expected_columns,
            categorical_columns=set(getattr(self.regression_preprocessor, "categorical_features_", [])),
        )
        transformed = self.regression_preprocessor.transform(aligned)
        raw_prediction = float(self.stacking_reg.predict(transformed)[0])
        value = float(np.clip(np.expm1(raw_prediction), a_min=0.0, a_max=None)) if self.regression_uses_log_target else raw_prediction
        # if self.regression_uses_log_target :
            # print("YESSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
        return {"prediction": value}

    def _to_dataframe(self, features: dict[str, Any]) -> pd.DataFrame:
        row: dict[str, Any] = {}
        for key, value in features.items():
            row[key] = value
        return pd.DataFrame([row])

    @staticmethod
    def _align_columns(
        frame: pd.DataFrame,
        expected_columns: list[str],
        categorical_columns: set[str] | None = None,
    ) -> pd.DataFrame:
        aligned = frame.copy()
        categorical_columns = categorical_columns or set()
        missing_columns = [col for col in expected_columns if col not in aligned.columns]
        if missing_columns:
            LOGGER.warning("Input is missing %d expected columns. Filling with NaN.", len(missing_columns))
        for column in missing_columns:
            aligned[column] = "unknown" if column in categorical_columns else np.nan
        return aligned.reindex(columns=expected_columns)

    @staticmethod
    def _expected_columns(preprocessor: Any) -> list[str]:
        if hasattr(preprocessor, "feature_names_in_"):
            return list(preprocessor.feature_names_in_)
        if hasattr(preprocessor, "feature_order_"):
            return list(preprocessor.feature_order_)
        return []

    @staticmethod
    def _load_feature_importance(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"top_features": []}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _assert_exists(path: Path, artifact_kind: str) -> None:
        if not path.exists():
            raise RuntimeError(f"Missing required {artifact_kind}: {path}")

    @staticmethod
    def _load_regression_log_target_flag(metrics_path: Path) -> bool:
        if not metrics_path.exists():
            return True
        with metrics_path.open("r", encoding="utf-8") as handle:
            metrics = json.load(handle)
        return "log_space_rmse" in metrics


_engine: InferenceEngine | None = None


def get_engine() -> InferenceEngine:
    global _engine
    if _engine is None:
        from backend.core.config import settings

        _engine = InferenceEngine(settings.artifacts_dir)
    return _engine
