import type {
  PredictRequestBody,
  PredictResponse,
  WhatIfRequestBody,
  WhatIfResponse,
} from "./types";

const DEFAULT_PUBLIC_API_ORIGIN = "http://localhost:8000";

/**
 * Reads `NEXT_PUBLIC_API_URL` (see `specs/FRONTEND_SPEC.md`), strips trailing slashes.
 */
export function getPublicApiOrigin(): string {
  const fromEnv =
    typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_API_URL !== undefined &&
    process.env.NEXT_PUBLIC_API_URL.length > 0
      ? process.env.NEXT_PUBLIC_API_URL.trim()
      : undefined;
  const base = fromEnv ?? DEFAULT_PUBLIC_API_ORIGIN;
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly endpoint: string,
    readonly responseBodyText: string,
    message?: string,
  ) {
    super(message ?? `API error ${status} on ${endpoint}`);
    this.name = "ApiError";
  }
}

/** Turns API failures into concise UI copy (handles FastAPI `detail` shapes). */
export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.responseBodyText) as unknown;
      if (parsed && typeof parsed === "object" && "detail" in parsed) {
        const detail = (parsed as { detail: unknown }).detail;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) {
          return detail
            .map((entry) => {
              if (entry && typeof entry === "object" && "msg" in entry) {
                const msg = (entry as { msg?: unknown }).msg;
                if (typeof msg === "string") return msg;
              }
              return JSON.stringify(entry);
            })
            .join("; ");
        }
        return JSON.stringify(detail);
      }
    } catch {
      return error.responseBodyText || error.message;
    }
    return error.responseBodyText || error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
async function parseResponseJson(endpoint: string, response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new ApiError(
      response.status,
      endpoint,
      text,
      `Non-JSON response from ${endpoint} (status ${response.status})`,
    );
  }
}

function assertPredictResponse(parsed: unknown, endpoint: string): PredictResponse {
  if (!parsed || typeof parsed !== "object") {
    throw new ApiError(500, endpoint, String(parsed), `Invalid predict response envelope`);
  }
  const envelope = parsed as Record<string, unknown>;
  const mode = envelope.mode;
  if (mode !== "classification" && mode !== "regression") {
    throw new ApiError(500, endpoint, JSON.stringify(parsed), `Unexpected predict mode`);
  }
  const result = envelope.result;
  if (!result || typeof result !== "object") {
    throw new ApiError(500, endpoint, JSON.stringify(parsed), `Missing predict result`);
  }

  if (mode === "classification") {
    const r = result as Record<string, unknown>;
    const prediction = r.prediction;
    if (prediction !== "Low" && prediction !== "Medium" && prediction !== "High") {
      throw new ApiError(500, endpoint, JSON.stringify(parsed), `Invalid classification prediction`);
    }
    const probs = r.probabilities;
    if (!probs || typeof probs !== "object") {
      throw new ApiError(500, endpoint, JSON.stringify(parsed), `Invalid classification probabilities`);
    }
    return {
      mode: "classification",
      result: {
        prediction,
        probabilities: probs as Record<string, number>,
      },
    };
  }

  const r = result as Record<string, unknown>;
  const prediction = r.prediction;
  if (typeof prediction !== "number") {
    throw new ApiError(500, endpoint, JSON.stringify(parsed), `Invalid regression prediction`);
  }
  return {
    mode: "regression",
    result: { prediction },
  };
}

function assertWhatIfResponse(parsed: unknown, endpoint: string): WhatIfResponse {
  if (!parsed || typeof parsed !== "object") {
    throw new ApiError(500, endpoint, String(parsed), `Invalid what-if response`);
  }
  const o = parsed as Record<string, unknown>;

  const orig = o.original_prediction;
  const neu = o.new_prediction;
  if ((typeof orig !== "number" && typeof orig !== "string") ||
    (typeof neu !== "number" && typeof neu !== "string")) {
    throw new ApiError(
      500,
      endpoint,
      JSON.stringify(parsed),
      `Invalid what-if prediction fields`,
    );
  }

  const delta = o.delta;
  const deltaPct = o.delta_percentage;
  if (
    !(delta === null || typeof delta === "number") ||
    !(deltaPct === null || typeof deltaPct === "number")
  ) {
    throw new ApiError(500, endpoint, JSON.stringify(parsed), `Invalid what-if delta fields`);
  }

  const origProb = o.original_probabilities;
  const newProb = o.new_probabilities;
  if (!(origProb === null || (typeof origProb === "object" && origProb !== null))) {
    throw new ApiError(
      500,
      endpoint,
      JSON.stringify(parsed),
      `Invalid original_probabilities`,
    );
  }
  if (!(newProb === null || (typeof newProb === "object" && newProb !== null))) {
    throw new ApiError(500, endpoint, JSON.stringify(parsed), `Invalid new_probabilities`);
  }

  return {
    original_prediction: orig,
    new_prediction: neu,
    delta,
    delta_percentage: deltaPct,
    original_probabilities: origProb as Record<string, number> | null,
    new_probabilities: newProb as Record<string, number> | null,
  };
}

/**
 * POST `/predict` → `PredictResponse`
 */
export async function predict(body: PredictRequestBody, init?: RequestInit): Promise<PredictResponse> {
  const origin = getPublicApiOrigin();
  const endpoint = `${origin}/predict`;
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  const response = await fetch(endpoint, {
    ...init,
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const parsed = await parseResponseJson(endpoint, response);

  if (!response.ok) {
    throw new ApiError(response.status, endpoint, parsed === undefined ? "" : JSON.stringify(parsed));
  }

  return assertPredictResponse(parsed, endpoint);
}

/**
 * POST `/predict/whatif` → `WhatIfResponse`
 */
export async function whatIf(
  body: WhatIfRequestBody,
  init?: RequestInit,
): Promise<WhatIfResponse> {
  const origin = getPublicApiOrigin();
  const endpoint = `${origin}/predict/whatif`;
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  const response = await fetch(endpoint, {
    ...init,
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const parsed = await parseResponseJson(endpoint, response);

  if (!response.ok) {
    throw new ApiError(response.status, endpoint, parsed === undefined ? "" : JSON.stringify(parsed));
  }

  return assertWhatIfResponse(parsed, endpoint);
}
