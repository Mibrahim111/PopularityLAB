import { redirect } from "next/navigation";

import { PredictFlow } from "@/components/predict/predict-flow";
import type { PredictionMode } from "@/lib/types";

function normalizeMode(raw: string | string[] | undefined): PredictionMode | null {
  const v = Array.isArray(raw) ? raw[0] : raw;
  if (v === "classification" || v === "regression") return v;
  return null;
}

interface PredictPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export default function PredictPage({ searchParams }: PredictPageProps) {
  const mode = normalizeMode(searchParams.mode);
  if (!mode) {
    redirect("/");
  }

  return <PredictFlow mode={mode} />;
}
