"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { FormProvider, useForm } from "react-hook-form";

import { PredictionFormFields } from "@/components/predict/prediction-form-fields";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { formatApiError, whatIf } from "@/lib/api";
import {
  WHAT_IF_FOCUS_KEYS,
  defaultFeatureInput,
  featureInputSchema,
  metaForFeatureKey,
  type FeatureInputFormValues,
  type WhatIfFocusKey,
} from "@/lib/features";
import type { FeatureInput, PredictionMode, WhatIfResponse } from "@/lib/types";

type ScenarioSlice = Pick<FeatureInput, WhatIfFocusKey>;

function sliceFocus(raw: FeatureInputFormValues): ScenarioSlice {
  const base = raw as FeatureInput;
  return {
    SteamSpyOwners: base.SteamSpyOwners,
    SteamSpyPlayersEstimate: base.SteamSpyPlayersEstimate,
    AchievementCount: base.AchievementCount,
    ScreenshotCount: base.ScreenshotCount,
    Metacritic: base.Metacritic,
    ShortDescrip: base.ShortDescrip,
    DetailedDescrip: base.DetailedDescrip,
    AboutText: base.AboutText,
  };
}

function assignPatch<K extends WhatIfFocusKey>(
  target: Partial<FeatureInput>,
  key: K,
  value: FeatureInput[K],
): void {
  const mutable = target as Pick<FeatureInput, K>;
  mutable[key] = value;
}

function scenarioPatch(base: FeatureInput, scenario: ScenarioSlice): Partial<FeatureInput> {
  const mod: Partial<FeatureInput> = {};
  for (const key of WHAT_IF_FOCUS_KEYS) {
    if (scenario[key] !== base[key]) {
      assignPatch(mod, key, scenario[key]);
    }
  }
  return mod;
}

export function WhatIfFlow() {
  const [mode, setMode] = useState<PredictionMode>("classification");
  const [scenario, setScenario] = useState<ScenarioSlice>(() => sliceFocus(defaultFeatureInput()));
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const methods = useForm<FeatureInputFormValues>({
    resolver: zodResolver(featureInputSchema),
    defaultValues: defaultFeatureInput(),
    mode: "onBlur",
  });

  async function onCompare(e: React.FormEvent) {
    e.preventDefault();
    await methods.handleSubmit(async (baseline) => {
      const modified = scenarioPatch(baseline as FeatureInput, scenario);
      if (Object.keys(modified).length === 0) {
        setError(
          "Adjust at least one scenario field so it differs from the baseline form values.",
        );
        setResult(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await whatIf({
          mode,
          base_features: baseline as FeatureInput,
          modified_features: modified,
        });
        setResult(res);
      } catch (err) {
        setResult(null);
        setError(formatApiError(err));
      } finally {
        setLoading(false);
      }
    })();
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-mono text-xl font-semibold tracking-tight text-foreground">
          What-if comparison
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Establish a validated baseline, tweak high-leverage fields on the right, then compare outcomes via{" "}
          <span className="font-mono">POST /predict/whatif</span>.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-4 border-b border-border sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base">Mode</CardTitle>
            <CardDescription>Classification shifts tier probabilities; regression reports delta.</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant={mode === "classification" ? "default" : "outline"}
              onClick={() => {
                setMode("classification");
                setResult(null);
              }}
            >
              Classification
            </Button>
            <Button
              type="button"
              variant={mode === "regression" ? "default" : "outline"}
              onClick={() => {
                setMode("regression");
                setResult(null);
              }}
            >
              Regression
            </Button>
          </div>
        </CardHeader>
      </Card>

      <FormProvider {...methods}>
        <form className="space-y-8" onSubmit={onCompare}>
          <PredictionFormFields />

          <Card>
            <CardHeader>
              <CardTitle>Scenario overrides</CardTitle>
              <CardDescription>
                Values here replace the baseline fields listed below when they differ. Keys mirror{" "}
                <span className="font-mono">WHAT_IF_FOCUS_KEYS</span> in <span className="font-mono">lib/features.ts</span>.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" onClick={() => setScenario(sliceFocus(methods.getValues()))}>
                  Copy baseline → scenario
                </Button>
                <Button type="button" variant="ghost" onClick={() => setScenario(sliceFocus(defaultFeatureInput()))}>
                  Reset scenario to defaults
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {WHAT_IF_FOCUS_KEYS.map((key) => {
                  const meta = metaForFeatureKey(key);
                  if (!meta) return null;
                  const id = `scenario-${key}`;
                  const value = scenario[key];

                  if (meta.kind === "textarea") {
                    return (
                      <div key={key} className="space-y-1.5">
                        <Label htmlFor={id}>Scenario — {meta.label}</Label>
                        <Textarea
                          id={id}
                          rows={meta.rows ?? 3}
                          value={value as string}
                          onChange={(e) =>
                            setScenario((prev) => ({
                              ...prev,
                              [key]: e.target.value,
                            }))
                          }
                        />
                      </div>
                    );
                  }

                  if (meta.kind === "int") {
                    return (
                      <div key={key} className="space-y-1.5">
                        <Label htmlFor={id}>Scenario — {meta.label}</Label>
                        <Input
                          id={id}
                          type="number"
                          step="1"
                          value={value as number}
                          onChange={(e) =>
                            setScenario((prev) => ({
                              ...prev,
                              [key]: e.target.value === "" ? 0 : Number(e.target.value),
                            }))
                          }
                        />
                      </div>
                    );
                  }

                  return null;
                })}
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={loading}>
              {loading ? "Comparing…" : "Run what-if"}
            </Button>
          </div>
        </form>
      </FormProvider>

      {error ? (
        <Card className="border-red-900/40 bg-red-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-200">Request failed</CardTitle>
          </CardHeader>
          <CardContent className="font-mono text-xs text-red-100/90">{error}</CardContent>
        </Card>
      ) : null}

      {result ? <WhatIfSummaryCard mode={mode} result={result} /> : null}
    </div>
  );
}

function WhatIfSummaryCard({ mode, result }: { mode: PredictionMode; result: WhatIfResponse }) {
  const clsOriginal = result.original_probabilities;
  const clsNew = result.new_probabilities;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Comparison</CardTitle>
        <CardDescription>
          {mode === "classification"
            ? "Prediction labels with refreshed probability mass."
            : "Regression deltas measured against the baseline estimate."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 font-mono text-sm">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-md border border-border bg-muted/20 p-3">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Original</p>
            <p className="mt-1 text-lg text-foreground">{String(result.original_prediction)}</p>
          </div>
          <div className="rounded-md border border-border bg-muted/20 p-3">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Scenario</p>
            <p className="mt-1 text-lg text-foreground">{String(result.new_prediction)}</p>
          </div>
        </div>

        {mode === "regression" && result.delta !== null && result.delta_percentage !== null ? (
          <div className="rounded-md border border-border bg-secondary/30 px-3 py-2 text-xs">
            <span className="text-muted-foreground">Δ absolute:</span>{" "}
            <span className="text-foreground">{result.delta.toFixed(3)}</span>
            <span className="mx-2 text-muted-foreground">·</span>
            <span className="text-muted-foreground">Δ %:</span>{" "}
            <span className="text-foreground">{result.delta_percentage.toFixed(2)}%</span>
          </div>
        ) : null}

        {mode === "classification" && clsOriginal && clsNew ? (
          <div className="overflow-x-auto rounded-md border border-border">
            <table className="w-full border-collapse text-left text-xs">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2 font-medium text-muted-foreground">Class</th>
                  <th className="px-3 py-2 font-medium text-muted-foreground">Baseline</th>
                  <th className="px-3 py-2 font-medium text-muted-foreground">Scenario</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(new Set([...Object.keys(clsOriginal), ...Object.keys(clsNew)])).map((label) => (
                  <tr key={label} className="border-t border-border">
                    <td className="px-3 py-2 text-foreground">{label}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {(clsOriginal[label] ?? 0).toFixed(4)}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {(clsNew[label] ?? 0).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
