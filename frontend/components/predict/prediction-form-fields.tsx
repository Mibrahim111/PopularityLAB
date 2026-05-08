"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  FEATURE_SECTIONS,
  fieldsGroupedBySection,
  type FeatureFieldMeta,
} from "@/lib/features";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useFormContext } from "react-hook-form";
import type { FeatureInput } from "@/lib/types";

export function PredictionFormFields() {
  const grouped = fieldsGroupedBySection();

  return (
    <div className="space-y-6">
      {FEATURE_SECTIONS.map((section) => (
        <Card key={section.id}>
          <CardHeader>
            <CardTitle>{section.title}</CardTitle>
            <CardDescription>{section.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {grouped[section.id].map((meta) => (
                <FeatureRow key={meta.key} meta={meta} />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function FeatureRow({ meta }: { meta: FeatureFieldMeta }) {
  const { register } = useFormContext<FeatureInput>();
  const id = `field-${meta.key}`;

  if (meta.kind === "bool") {
    return (
      <div className="flex items-center gap-2 pt-6">
        <input
          id={id}
          type="checkbox"
          className="h-4 w-4 rounded border border-input bg-background text-primary focus-visible:ring-2 focus-visible:ring-ring"
          {...register(meta.key)}
        />
        <Label htmlFor={id} className="cursor-pointer normal-case tracking-normal">
          {meta.label}
        </Label>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{meta.label}</Label>
      {meta.kind === "textarea" ? (
        <Textarea id={id} rows={meta.rows ?? 3} {...register(meta.key)} />
      ) : (
        <Input
          id={id}
          type={meta.kind === "date" ? "date" : meta.kind === "float" || meta.kind === "int" ? "number" : "text"}
          step={meta.kind === "float" ? (meta.step ?? "any") : meta.kind === "int" ? "1" : undefined}
          {...register(meta.key)}
        />
      )}
    </div>
  );
}
