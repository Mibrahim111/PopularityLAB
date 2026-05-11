from __future__ import annotations

from pathlib import Path

import joblib

from backend.core.inference import InferenceEngine
from backend.schemas.request import FeatureInput


def test_artifact_smoke_loads_and_predicts() -> None:
    artifacts_root = Path("ml/artifacts")
    artifact_paths = [
        artifacts_root / "classification" / "preprocessor.pkl",
        artifacts_root / "classification" / "stacking_clf.pkl",
        artifacts_root / "classification" / "label_encoder.pkl",
        artifacts_root / "regression" / "reg_preprocessor.pkl",
        artifacts_root / "regression" / "stacking_reg.pkl",
    ]

    for artifact_path in artifact_paths:
        assert artifact_path.exists(), f"Artifact is missing: {artifact_path}"
        loaded = joblib.load(artifact_path)
        print(f"{artifact_path}: {type(loaded).__name__}")

    engine = InferenceEngine(artifacts_root)
    payload = FeatureInput().model_dump(mode="python")

    clf_result = engine.predict_classification(payload)
    assert "prediction" in clf_result
    assert "probabilities" in clf_result
    assert isinstance(clf_result["probabilities"], dict)
    assert clf_result["probabilities"]

    reg_result = engine.predict_regression(payload)
    assert "prediction" in reg_result
    assert isinstance(reg_result["prediction"], float)
