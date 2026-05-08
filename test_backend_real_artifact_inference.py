from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.core.inference import InferenceEngine
from backend.main import app
from backend.schemas.request import FeatureInput


def _build_realistic_feature_payload() -> dict[str, object]:
    payload = FeatureInput().model_dump(mode="json")
    sample_path = Path("Data/classification/train_data.csv")
    if not sample_path.exists():
        return payload

    sample = pd.read_csv(sample_path, nrows=1).iloc[0].to_dict()
    for key in FeatureInput.model_fields:
        if key not in sample or pd.isna(sample[key]):
            continue
        value = sample[key]
        if key == "ReleaseDate":
            try:
                payload[key] = str(pd.to_datetime(value).date())
            except (TypeError, ValueError):
                pass
            continue
        default_value = payload[key]
        if isinstance(default_value, bool):
            payload[key] = bool(value)
        elif isinstance(default_value, int) and not isinstance(default_value, bool):
            payload[key] = int(value)
        elif isinstance(default_value, float):
            payload[key] = float(value)
        elif isinstance(default_value, str):
            payload[key] = str(value)
        elif isinstance(default_value, date):
            payload[key] = str(default_value)

    if payload["PriceFinal"] > payload["PriceInitial"]:
        payload["PriceFinal"] = payload["PriceInitial"]
    return payload


def test_artifacts_load_on_startup_and_predict_end_to_end() -> None:
    with TestClient(app) as client:
        engine = client.app.state.engine
        assert isinstance(engine, InferenceEngine)
        assert engine.classification_dir == settings.artifacts_dir / "classification"
        assert engine.regression_dir == settings.artifacts_dir / "regression"
        assert "mock" not in type(engine.stacking_clf).__name__.lower()
        assert "mock" not in type(engine.stacking_reg).__name__.lower()

        features = _build_realistic_feature_payload()

        clf_response = client.post(
            "/predict",
            json={"mode": "classification", "features": features},
        )
        assert clf_response.status_code == 200, clf_response.text
        clf_body = clf_response.json()
        assert clf_body["mode"] == "classification"
        assert isinstance(clf_body["result"]["prediction"], str)
        probabilities = clf_body["result"]["probabilities"]
        assert isinstance(probabilities, dict)
        assert probabilities
        assert all(math.isfinite(float(v)) for v in probabilities.values())
        assert abs(sum(float(v) for v in probabilities.values()) - 1.0) < 1e-3

        reg_response = client.post(
            "/predict",
            json={"mode": "regression", "features": features},
        )
        assert reg_response.status_code == 200, reg_response.text
        reg_body = reg_response.json()
        assert reg_body["mode"] == "regression"
        prediction = reg_body["result"]["prediction"]
        assert isinstance(prediction, (float, int))
        assert math.isfinite(float(prediction))
        assert float(prediction) >= 0.0


def test_artifact_files_are_real_and_loadable() -> None:
    required_artifacts = [
        Path("ml/artifacts/classification/preprocessor.pkl"),
        Path("ml/artifacts/classification/stacking_clf.pkl"),
        Path("ml/artifacts/classification/label_encoder.pkl"),
        Path("ml/artifacts/regression/reg_preprocessor.pkl"),
        Path("ml/artifacts/regression/stacking_reg.pkl"),
    ]
    for path in required_artifacts:
        assert path.exists(), f"Missing required artifact: {path}"
        loaded = joblib.load(path)
        assert loaded is not None
