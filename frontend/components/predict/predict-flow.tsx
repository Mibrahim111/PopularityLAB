"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { FormProvider, useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  defaultFeatureInput,
  featureInputSchema,
  type FeatureInputFormValues,
} from "@/lib/features";
import { formatApiError, predict } from "@/lib/api";
import type { FeatureInput, PredictionMode, PredictResponse } from "@/lib/types";

import { PredictionFormFields } from "./prediction-form-fields";
import { PredictionResultsPanel } from "./prediction-results-panel";

export function PredictFlow({ mode }: { mode: PredictionMode }) {
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const methods = useForm<FeatureInputFormValues>({
    resolver: zodResolver(featureInputSchema),
    defaultValues: defaultFeatureInput(),
    mode: "onBlur",
  });

  async function onSubmit(values: FeatureInputFormValues) {
    setLoading(true);
    setError(null);
    try {
      const res = await predict({ mode, features: values as FeatureInput });
      setResult(res);
    } catch (err) {
      setResult(null);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-mono text-xl font-semibold tracking-tight text-foreground">
          Predict{" "}
          <span className="text-muted-foreground">
            (
            {mode === "classification" ? "classification" : "regression"})
          </span>
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Inputs mirror backend <span className="font-mono">FeatureInput</span>. Submission hits{" "}
          <span className="font-mono">POST /predict</span> with no mocks.
        </p>
      </div>

      <FormProvider {...methods}>
        <form className="space-y-8" onSubmit={methods.handleSubmit(onSubmit)}>
          <PredictionFormFields />
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={loading}>
              {loading ? "Running inference…" : "Run prediction"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                methods.reset(defaultFeatureInput());
                setResult(null);
                setError(null);
              }}
            >
              Reset defaults
            </Button>
          </div>
        </form>
      </FormProvider>

      {methods.formState.submitCount > 0 && Object.keys(methods.formState.errors).length > 0 ? (
        <p className="text-xs text-amber-200/90">
          Some fields failed validation—check prices (final ≤ initial) and numeric ranges.
        </p>
      ) : null}

      {error ? (
        <Card className="border-red-900/40 bg-red-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-200">Request failed</CardTitle>
          </CardHeader>
          <CardContent className="font-mono text-xs text-red-100/90">{error}</CardContent>
        </Card>
      ) : null}

      <PredictionResultsPanel mode={mode} result={result} />
    </div>
  );
}
