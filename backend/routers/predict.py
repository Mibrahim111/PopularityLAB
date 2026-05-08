from fastapi import APIRouter, HTTPException, Request

from backend.core.inference import InferenceEngine
from backend.schemas.request import FeatureInput, PredictRequest, WhatIfRequest
from backend.schemas.response import PredictResponse, WhatIfResponse

router = APIRouter(prefix="/predict", tags=["predict"])

_FEATURE_INPUT_KEYS = frozenset(FeatureInput.model_fields.keys())


@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest, request: Request) -> PredictResponse:
    engine: InferenceEngine = request.app.state.engine
    features = req.features.model_dump()
    if req.mode == "classification":
        result = engine.predict_classification(features)
    else:
        result = engine.predict_regression(features)
    return PredictResponse(mode=req.mode, result=result)


@router.post("/whatif", response_model=WhatIfResponse)
def whatif(req: WhatIfRequest, request: Request) -> WhatIfResponse:
    engine: InferenceEngine = request.app.state.engine

    base = req.base_features.model_dump()
    # Validate raw FeatureInput keys only. `engine.top_features` stores preprocessor
    # column names (e.g. num__*) which do not align with API payload keys.
    invalid = set(req.modified_features.keys()) - _FEATURE_INPUT_KEYS
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=(
                f"modified_features contains unknown keys: {sorted(invalid)}. "
                f"Keys must be FeatureInput fields (see API schema)."
            ),
        )
    modified = {**base, **req.modified_features}

    if req.mode == "classification":
        original = engine.predict_classification(base)
        updated = engine.predict_classification(modified)
        return WhatIfResponse(
            original_prediction=original["prediction"],
            new_prediction=updated["prediction"],
            delta=None,
            delta_percentage=None,
            original_probabilities=original["probabilities"],
            new_probabilities=updated["probabilities"],
        )

    original = engine.predict_regression(base)
    updated = engine.predict_regression(modified)
    original_value = original["prediction"]
    updated_value = updated["prediction"]
    delta = updated_value - original_value
    delta_percentage = (delta / original_value * 100) if original_value != 0 else 0.0

    return WhatIfResponse(
        original_prediction=original_value,
        new_prediction=updated_value,
        delta=delta,
        delta_percentage=delta_percentage,
    )
