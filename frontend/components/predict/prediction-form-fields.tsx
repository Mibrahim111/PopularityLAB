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
import { parseTxtInput } from "@/lib/parseInput";
import type { FeatureInput } from "@/lib/types";
import { useRef } from "react";
import { Button } from "@/components/ui/button";

export function PredictionFormFields() {
  const grouped = fieldsGroupedBySection();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const methods = useFormContext<FeatureInput>();

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      const parsed = parseTxtInput(content);
      
      // Update form with parsed values
      methods.reset(parsed as FeatureInput, { keepValues: false });
    } catch (error) {
      console.error("Failed to parse file:", error);
      alert(`Failed to parse file: ${error instanceof Error ? error.message : "Unknown error"}`);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Load from File</CardTitle>
          <CardDescription>Upload a .txt file with game data to populate the form</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
              >
                Browse
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Format: key: value (one per line, e.g., Name: My Game, ReleaseDate: 2020-01-01)
            </p>
          </div>
        </CardContent>
      </Card>

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
