"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PredictionMode, PredictResponse } from "@/lib/types";
import { isClassificationPredictResponse, isRegressionPredictResponse } from "@/lib/types";

export function PredictionResultsPanel({
  mode,
  result,
}: {
  mode: PredictionMode;
  result: PredictResponse | null;
}) {
  if (!result) {
    return (
      <Card className="border-dashed border-muted/60 bg-muted/10">
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>Submit the form to render live model output.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (mode === "classification" && isClassificationPredictResponse(result)) {
    const chartData = Object.entries(result.result.probabilities).map(([label, value]) => ({
      label,
      value,
    }));

    return (
      <Card>
        <CardHeader>
          <CardTitle>Classification</CardTitle>
          <CardDescription>
            Predicted tier:{" "}
            <span className="font-mono text-foreground">{result.result.prediction}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={(v) => `${Math.round(Number(v) * 100)}%`}
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  width={44}
                />
                <Tooltip
                  formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, "Probability"]}
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="value" fill="hsl(217 91% 60%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (mode === "regression" && isRegressionPredictResponse(result)) {
    const value = result.result.prediction;
    const formatted = Number.isFinite(value)
      ? Math.round(value).toLocaleString(undefined, { maximumFractionDigits: 0 })
      : String(value);

    return (
      <Card>
        <CardHeader>
          <CardTitle>Regression</CardTitle>
          <CardDescription>
            Training target was Steam <span className="font-mono">RecommendationCount</span>; interpret as a
            relative popularity proxy rather than a live Steam figure.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="font-mono text-4xl font-semibold tracking-tight text-foreground">{formatted}</p>
          <p className="mt-2 text-xs text-muted-foreground">Point estimate from stacked regressor output.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-muted">
      <CardHeader>
        <CardTitle>Unexpected response shape</CardTitle>
        <CardDescription>Mode and payload mismatch—check API compatibility.</CardDescription>
      </CardHeader>
    </Card>
  );
}
