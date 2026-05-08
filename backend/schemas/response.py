from typing import Literal

from pydantic import BaseModel


class ClassificationResult(BaseModel):
    prediction: Literal["Low", "Medium", "High"]
    probabilities: dict[str, float]


class RegressionResult(BaseModel):
    prediction: float


class PredictResponse(BaseModel):
    mode: str
    result: ClassificationResult | RegressionResult


class WhatIfResponse(BaseModel):
    original_prediction: float | str
    new_prediction: float | str
    delta: float | None
    delta_percentage: float | None
    original_probabilities: dict[str, float] | None = None
    new_probabilities: dict[str, float] | None = None
