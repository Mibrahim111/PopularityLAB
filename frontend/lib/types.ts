/**
 * Wire types aligned with `backend/schemas/request.py`, `backend/schemas/response.py`,
 * and JSON bodies used in `test_backend_real_artifact_inference.py` (`model_dump(mode="json")`).
 *
 * Dates are ISO `YYYY-MM-DD` strings over the wire (FastAPI/Pydantic JSON).
 */

export type PredictionMode = "classification" | "regression";

/** ISO calendar date string (backend `date` serialized to JSON). */
export type IsoDateString = `${number}-${number}-${number}`;

/**
 * Mirrors `FeatureInput` field names (PascalCase) and primitive JSON shapes from the backend.
 */
export interface FeatureInput {
  Name: string;
  ReleaseDate: IsoDateString;

  RequiredAge: number;
  DemoCount: number;
  DeveloperCount: number;
  DLCCount: number;
  Metacritic: number;
  MovieCount: number;
  PackageCount: number;
  PublisherCount: number;
  ScreenshotCount: number;
  SteamSpyOwners: number;
  SteamSpyOwnersVariance: number;
  SteamSpyPlayersEstimate: number;
  SteamSpyPlayersVariance: number;
  AchievementCount: number;
  AchievementHighlightedCount: number;
  PriceInitial: number;
  PriceFinal: number;
  ReleaseYear: number;
  ReleaseMonth: number;

  ControllerSupport: boolean;
  IsFree: boolean;
  FreeVerAvail: boolean;
  PurchaseAvail: boolean;
  SubscriptionAvail: boolean;
  PlatformWindows: boolean;
  PlatformLinux: boolean;
  PlatformMac: boolean;
  PCReqsHaveMin: boolean;
  PCReqsHaveRec: boolean;
  LinuxReqsHaveMin: boolean;
  LinuxReqsHaveRec: boolean;
  MacReqsHaveMin: boolean;
  MacReqsHaveRec: boolean;
  CategorySinglePlayer: boolean;
  CategoryMultiplayer: boolean;
  CategoryCoop: boolean;
  CategoryMMO: boolean;
  CategoryInAppPurchase: boolean;
  CategoryIncludeSrcSDK: boolean;
  CategoryIncludeLevelEditor: boolean;
  CategoryVRSupport: boolean;
  GenreIsNonGame: boolean;
  GenreIsIndie: boolean;
  GenreIsAction: boolean;
  GenreIsAdventure: boolean;
  GenreIsCasual: boolean;
  GenreIsStrategy: boolean;
  GenreIsRPG: boolean;
  GenreIsSimulation: boolean;
  GenreIsEarlyAccess: boolean;
  GenreIsFreeToPlay: boolean;
  GenreIsSports: boolean;
  GenreIsRacing: boolean;
  GenreIsMassivelyMultiplayer: boolean;

  PriceCurrency: string;
  SupportEmail: string;
  SupportURL: string;
  AboutText: string;
  Background: string;
  ShortDescrip: string;
  DetailedDescrip: string;
  DRMNotice: string;
  ExtUserAcctNotice: string;
  HeaderImage: string;
  LegalNotice: string;
  Reviews: string;
  SupportedLanguages: string;
  Website: string;
  PCMinReqsText: string;
  PCRecReqsText: string;
  LinuxMinReqsText: string;
  LinuxRecReqsText: string;
  MacMinReqsText: string;
  MacRecReqsText: string;
}

export type FeatureScalar = string | number | boolean;

/**
 * Payload for `POST /predict` (`PredictRequest`).
 */
export interface PredictRequestBody {
  mode: PredictionMode;
  features: FeatureInput;
}

export type ClassificationLabel = "Low" | "Medium" | "High";

/** `ClassificationResult` from `PredictResponse.result` when mode is classification. */
export interface ClassificationResult {
  prediction: ClassificationLabel;
  probabilities: Record<string, number>;
}

/** `RegressionResult` when mode is regression. */
export interface RegressionResult {
  prediction: number;
}

/**
 * Narrow `PredictResponse` by `mode` for correct `result` typing.
 * Backend declares `PredictResponse.mode: str`; we treat values as well-known literals.
 */
export type PredictResponse =
  | { mode: "classification"; result: ClassificationResult }
  | { mode: "regression"; result: RegressionResult };

/**
 * Allowed values in `modified_features` for `POST /predict/whatif`
 * (`WhatIfRequest`: dict[str, int | float | bool | str | date]).
 */
export type WhatIfModifiedValue = FeatureScalar | IsoDateString;

/**
 * Payload for `POST /predict/whatif` (`WhatIfRequest`).
 */
export interface WhatIfRequestBody {
  mode: PredictionMode;
  base_features: FeatureInput;
  modified_features: Partial<Record<keyof FeatureInput, WhatIfModifiedValue>>;
}

/**
 * Backend `WhatIfResponse`.
 * Regression: numeric predictions plus delta fields.
 * Classification: string labels plus optional probability maps; delta fields unset.
 */
export interface WhatIfResponse {
  original_prediction: number | string;
  new_prediction: number | string;
  delta: number | null;
  delta_percentage: number | null;
  original_probabilities: Record<string, number> | null;
  new_probabilities: Record<string, number> | null;
}

export function isClassificationPredictResponse(
  body: PredictResponse,
): body is { mode: "classification"; result: ClassificationResult } {
  return body.mode === "classification";
}

export function isRegressionPredictResponse(
  body: PredictResponse,
): body is { mode: "regression"; result: RegressionResult } {
  return body.mode === "regression";
}
