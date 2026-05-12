import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="space-y-10">
      <div className="max-w-2xl space-y-2">
        <p className="font-mono text-[11px] uppercase tracking-[0.35em] text-muted-foreground">
          Inference console
        </p>
        <h1 className="font-mono text-3xl font-semibold tracking-tight text-foreground">
          Steam popularity models
        </h1>
        <p className="text-sm text-muted-foreground">
         Start Exploring Steam Games Popularity with our models {" "}
          <span className="font-mono"></span> 
        </p>
      </div>

      <div className="flex justify-center">
        <div className="grid gap-6 md:grid-cols-2 max-w-4xl">
          <Link href="/predict?mode=classification" className="group block h-full">
            <Card className="h-full border-border bg-card transition-colors group-hover:border-primary/40">
              <CardHeader>
                <CardTitle className="font-mono text-base">Game Popularity Tier</CardTitle>
                <CardDescription>Three-band popularity tiers with calibrated probabilities.</CardDescription>
              </CardHeader>
              <CardContent className="font-mono text-[11px] text-muted-foreground">
                Run Classification Pipeline
              </CardContent>
            </Card>
          </Link>

          <Link href="/predict?mode=regression" className="group block h-full">
            <Card className="h-full border-border bg-card transition-colors group-hover:border-primary/40">
              <CardHeader>
                <CardTitle className="font-mono text-base">Game Recommendation Score</CardTitle>
                <CardDescription>
                  See how likely will a game go viral and get a score.
                </CardDescription>
              </CardHeader>
              <CardContent className="font-mono text-[11px] text-muted-foreground">
                Run Regression Pipeline
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
