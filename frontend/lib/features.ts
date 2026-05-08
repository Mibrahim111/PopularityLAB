import { z } from "zod";

import type { FeatureInput, IsoDateString } from "./types";

/** Section headers for the prediction form (single source for grouping). */
export const FEATURE_SECTIONS = [
  {
    id: "identity_release",
    title: "Identity & release",
    description: "Title and release timing sent to the API as structured fields.",
  },
  {
    id: "commerce",
    title: "Pricing & storefront",
    description: "Price caps, currency, and basic Steam commerce flags.",
  },
  {
    id: "steam_metrics",
    title: "SteamSpy estimates",
    description: "Historical ownership / player estimates when available.",
  },
  {
    id: "counts_ratings",
    title: "Counts & ratings",
    description: "Achievement, DLC, packages, screenshots, and Metacritic.",
  },
  {
    id: "platform_requirements",
    title: "Platforms & requirement flags",
    description: "Platform toggles and whether min/rec specs exist.",
  },
  {
    id: "categories",
    title: "Steam categories",
    description: "Gameplay and store category tags.",
  },
  {
    id: "genres",
    title: "Steam genres",
    description: "Genre tag booleans.",
  },
  {
    id: "audience",
    title: "Audience",
    description: "Age rating gate.",
  },
  {
    id: "descriptions",
    title: "Descriptions & reviews text",
    description: "Long text fields used by feature engineering (length/word counts).",
  },
  {
    id: "links_and_legal",
    title: "URLs, legal, and system requirements text",
    description: "Supporting strings passed through to preprocessing.",
  },
] as const;

export type FeatureSectionId = (typeof FEATURE_SECTIONS)[number]["id"];

export type FeatureFieldKind = "string" | "textarea" | "date" | "int" | "float" | "bool";

export interface FeatureFieldMeta {
  key: keyof FeatureInput;
  section: FeatureSectionId;
  label: string;
  kind: FeatureFieldKind;
  min?: number;
  max?: number;
  step?: number;
  rows?: number;
}

/**
 * Default payload aligned with `backend/schemas/request.py` (`FeatureInput` defaults,
 * `ReleaseDate` as ISO string for JSON).
 */
export const DEFAULT_FEATURE_INPUT: FeatureInput = {
  Name: "",
  ReleaseDate: "2020-01-01" as IsoDateString,

  RequiredAge: 0,
  DemoCount: 0,
  DeveloperCount: 1,
  DLCCount: 0,
  Metacritic: 0,
  MovieCount: 0,
  PackageCount: 1,
  PublisherCount: 1,
  ScreenshotCount: 0,
  SteamSpyOwners: 0,
  SteamSpyOwnersVariance: 0,
  SteamSpyPlayersEstimate: 0,
  SteamSpyPlayersVariance: 0,
  AchievementCount: 0,
  AchievementHighlightedCount: 0,
  PriceInitial: 9.99,
  PriceFinal: 9.99,
  ReleaseYear: 2020,
  ReleaseMonth: 6,

  ControllerSupport: false,
  IsFree: false,
  FreeVerAvail: false,
  PurchaseAvail: true,
  SubscriptionAvail: false,
  PlatformWindows: true,
  PlatformLinux: false,
  PlatformMac: false,
  PCReqsHaveMin: false,
  PCReqsHaveRec: false,
  LinuxReqsHaveMin: false,
  LinuxReqsHaveRec: false,
  MacReqsHaveMin: false,
  MacReqsHaveRec: false,
  CategorySinglePlayer: true,
  CategoryMultiplayer: false,
  CategoryCoop: false,
  CategoryMMO: false,
  CategoryInAppPurchase: false,
  CategoryIncludeSrcSDK: false,
  CategoryIncludeLevelEditor: false,
  CategoryVRSupport: false,
  GenreIsNonGame: false,
  GenreIsIndie: false,
  GenreIsAction: false,
  GenreIsAdventure: false,
  GenreIsCasual: false,
  GenreIsStrategy: false,
  GenreIsRPG: false,
  GenreIsSimulation: false,
  GenreIsEarlyAccess: false,
  GenreIsFreeToPlay: false,
  GenreIsSports: false,
  GenreIsRacing: false,
  GenreIsMassivelyMultiplayer: false,

  PriceCurrency: "USD",
  SupportEmail: "",
  SupportURL: "",
  AboutText: "",
  Background: "",
  ShortDescrip: "",
  DetailedDescrip: "",
  DRMNotice: "",
  ExtUserAcctNotice: "",
  HeaderImage: "",
  LegalNotice: "",
  Reviews: "",
  SupportedLanguages: "",
  Website: "",
  PCMinReqsText: "",
  PCRecReqsText: "",
  LinuxMinReqsText: "",
  LinuxRecReqsText: "",
  MacMinReqsText: "",
  MacRecReqsText: "",
};

/**
 * Raw `FeatureInput` keys that align with high-impact engineered signals (ownership,
 * text volume, achievements, Metacritic). Used to streamline what-if adjustments.
 */
export type WhatIfFocusKey =
  | "SteamSpyOwners"
  | "SteamSpyPlayersEstimate"
  | "AchievementCount"
  | "ScreenshotCount"
  | "Metacritic"
  | "ShortDescrip"
  | "DetailedDescrip"
  | "AboutText";

export const WHAT_IF_FOCUS_KEYS: readonly WhatIfFocusKey[] = [
  "SteamSpyOwners",
  "SteamSpyPlayersEstimate",
  "AchievementCount",
  "ScreenshotCount",
  "Metacritic",
  "ShortDescrip",
  "DetailedDescrip",
  "AboutText",
];
/** Labels + layout + validation hints for every FeatureInput field (single source of truth). */
export const FEATURE_FIELD_METAS: FeatureFieldMeta[] = [
  { key: "Name", section: "identity_release", label: "Name", kind: "string" },
  { key: "ReleaseDate", section: "identity_release", label: "Release date", kind: "date" },
  { key: "ReleaseYear", section: "identity_release", label: "Release year", kind: "int", min: 2003, max: 2030 },
  { key: "ReleaseMonth", section: "identity_release", label: "Release month", kind: "int", min: 1, max: 12 },

  { key: "PriceInitial", section: "commerce", label: "Price (initial)", kind: "float", min: 0, step: 0.01 },
  { key: "PriceFinal", section: "commerce", label: "Price (final)", kind: "float", min: 0, step: 0.01 },
  { key: "PriceCurrency", section: "commerce", label: "Currency code", kind: "string" },
  { key: "IsFree", section: "commerce", label: "Is free", kind: "bool" },
  { key: "FreeVerAvail", section: "commerce", label: "Free version available", kind: "bool" },
  { key: "PurchaseAvail", section: "commerce", label: "Purchase available", kind: "bool" },
  { key: "SubscriptionAvail", section: "commerce", label: "Subscription available", kind: "bool" },

  { key: "SteamSpyOwners", section: "steam_metrics", label: "SteamSpy owners", kind: "int", min: 0 },
  {
    key: "SteamSpyOwnersVariance",
    section: "steam_metrics",
    label: "Owners variance",
    kind: "int",
    min: 0,
  },
  {
    key: "SteamSpyPlayersEstimate",
    section: "steam_metrics",
    label: "Players estimate",
    kind: "int",
    min: 0,
  },
  {
    key: "SteamSpyPlayersVariance",
    section: "steam_metrics",
    label: "Players variance",
    kind: "int",
    min: 0,
  },

  { key: "AchievementCount", section: "counts_ratings", label: "Achievements", kind: "int", min: 0 },
  {
    key: "AchievementHighlightedCount",
    section: "counts_ratings",
    label: "Highlighted achievements",
    kind: "int",
    min: 0,
  },
  { key: "DemoCount", section: "counts_ratings", label: "Demo count", kind: "int", min: 0 },
  { key: "DLCCount", section: "counts_ratings", label: "DLC count", kind: "int", min: 0 },
  { key: "Metacritic", section: "counts_ratings", label: "Metacritic score", kind: "int", min: 0, max: 100 },
  { key: "MovieCount", section: "counts_ratings", label: "Movie count", kind: "int", min: 0 },
  { key: "PackageCount", section: "counts_ratings", label: "Package count", kind: "int", min: 0 },
  { key: "PublisherCount", section: "counts_ratings", label: "Publishers", kind: "int", min: 0 },
  { key: "DeveloperCount", section: "counts_ratings", label: "Developers", kind: "int", min: 0 },
  { key: "ScreenshotCount", section: "counts_ratings", label: "Screenshots", kind: "int", min: 0 },

  { key: "ControllerSupport", section: "platform_requirements", label: "Controller support", kind: "bool" },
  { key: "PlatformWindows", section: "platform_requirements", label: "Windows", kind: "bool" },
  { key: "PlatformLinux", section: "platform_requirements", label: "Linux", kind: "bool" },
  { key: "PlatformMac", section: "platform_requirements", label: "macOS", kind: "bool" },
  { key: "PCReqsHaveMin", section: "platform_requirements", label: "PC min requirements listed", kind: "bool" },
  { key: "PCReqsHaveRec", section: "platform_requirements", label: "PC recommended reqs listed", kind: "bool" },
  {
    key: "LinuxReqsHaveMin",
    section: "platform_requirements",
    label: "Linux min requirements listed",
    kind: "bool",
  },
  {
    key: "LinuxReqsHaveRec",
    section: "platform_requirements",
    label: "Linux recommended reqs listed",
    kind: "bool",
  },
  {
    key: "MacReqsHaveMin",
    section: "platform_requirements",
    label: "macOS min requirements listed",
    kind: "bool",
  },
  {
    key: "MacReqsHaveRec",
    section: "platform_requirements",
    label: "macOS recommended reqs listed",
    kind: "bool",
  },

  { key: "CategorySinglePlayer", section: "categories", label: "Single-player", kind: "bool" },
  { key: "CategoryMultiplayer", section: "categories", label: "Multi-player", kind: "bool" },
  { key: "CategoryCoop", section: "categories", label: "Co-op", kind: "bool" },
  { key: "CategoryMMO", section: "categories", label: "MMO", kind: "bool" },
  { key: "CategoryInAppPurchase", section: "categories", label: "In-app purchases", kind: "bool" },
  { key: "CategoryIncludeSrcSDK", section: "categories", label: "Includes Source SDK", kind: "bool" },
  { key: "CategoryIncludeLevelEditor", section: "categories", label: "Includes level editor", kind: "bool" },
  { key: "CategoryVRSupport", section: "categories", label: "VR support", kind: "bool" },

  { key: "GenreIsNonGame", section: "genres", label: "Non-game", kind: "bool" },
  { key: "GenreIsIndie", section: "genres", label: "Indie", kind: "bool" },
  { key: "GenreIsAction", section: "genres", label: "Action", kind: "bool" },
  { key: "GenreIsAdventure", section: "genres", label: "Adventure", kind: "bool" },
  { key: "GenreIsCasual", section: "genres", label: "Casual", kind: "bool" },
  { key: "GenreIsStrategy", section: "genres", label: "Strategy", kind: "bool" },
  { key: "GenreIsRPG", section: "genres", label: "RPG", kind: "bool" },
  { key: "GenreIsSimulation", section: "genres", label: "Simulation", kind: "bool" },
  { key: "GenreIsEarlyAccess", section: "genres", label: "Early Access", kind: "bool" },
  { key: "GenreIsFreeToPlay", section: "genres", label: "Free to play", kind: "bool" },
  { key: "GenreIsSports", section: "genres", label: "Sports", kind: "bool" },
  { key: "GenreIsRacing", section: "genres", label: "Racing", kind: "bool" },
  { key: "GenreIsMassivelyMultiplayer", section: "genres", label: "Massively multiplayer", kind: "bool" },

  { key: "RequiredAge", section: "audience", label: "Required age", kind: "int", min: 0, max: 21 },

  {
    key: "AboutText",
    section: "descriptions",
    label: "About text",
    kind: "textarea",
    rows: 4,
  },
  {
    key: "ShortDescrip",
    section: "descriptions",
    label: "Short description",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "DetailedDescrip",
    section: "descriptions",
    label: "Detailed description",
    kind: "textarea",
    rows: 5,
  },
  { key: "Reviews", section: "descriptions", label: "Reviews excerpt", kind: "textarea", rows: 3 },
  {
    key: "SupportedLanguages",
    section: "descriptions",
    label: "Supported languages",
    kind: "string",
  },

  { key: "Website", section: "links_and_legal", label: "Website URL", kind: "string" },
  { key: "SupportEmail", section: "links_and_legal", label: "Support email", kind: "string" },
  { key: "SupportURL", section: "links_and_legal", label: "Support URL", kind: "string" },
  { key: "Background", section: "links_and_legal", label: "Background asset", kind: "string" },
  { key: "HeaderImage", section: "links_and_legal", label: "Header image", kind: "string" },
  { key: "DRMNotice", section: "links_and_legal", label: "DRM notice", kind: "textarea", rows: 2 },
  {
    key: "ExtUserAcctNotice",
    section: "links_and_legal",
    label: "External account notice",
    kind: "textarea",
    rows: 2,
  },
  { key: "LegalNotice", section: "links_and_legal", label: "Legal notice", kind: "textarea", rows: 2 },
  {
    key: "PCMinReqsText",
    section: "links_and_legal",
    label: "PC minimum requirements",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "PCRecReqsText",
    section: "links_and_legal",
    label: "PC recommended requirements",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "LinuxMinReqsText",
    section: "links_and_legal",
    label: "Linux minimum requirements",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "LinuxRecReqsText",
    section: "links_and_legal",
    label: "Linux recommended requirements",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "MacMinReqsText",
    section: "links_and_legal",
    label: "macOS minimum requirements",
    kind: "textarea",
    rows: 3,
  },
  {
    key: "MacRecReqsText",
    section: "links_and_legal",
    label: "macOS recommended requirements",
    kind: "textarea",
    rows: 3,
  },
];

function buildZodField(meta: FeatureFieldMeta): z.ZodTypeAny {
  switch (meta.kind) {
    case "string":
      return z.string();
    case "textarea":
      return z.string();
    case "date":
      return z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use date format YYYY-MM-DD");
    case "int": {
      let n = z.coerce.number().int();
      if (meta.min !== undefined) n = n.min(meta.min);
      if (meta.max !== undefined) n = n.max(meta.max);
      return n;
    }
    case "float": {
      let n = z.coerce.number();
      if (meta.min !== undefined) n = n.min(meta.min);
      return n;
    }
    case "bool":
      return z.boolean();
    default: {
      const _never: never = meta.kind;
      return _never;
    }
  }
}

const featureShape: Record<string, z.ZodTypeAny> = {};
for (const meta of FEATURE_FIELD_METAS) {
  featureShape[meta.key] = buildZodField(meta);
}

/** Zod schema mirroring backend `FeatureInput` constraints (incl. price ordering). */
export const featureInputSchema = z
  .object(featureShape as unknown as z.ZodRawShape)
  .superRefine((data, ctx) => {
    const row = data as FeatureInput;
    if (row.PriceFinal > row.PriceInitial) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Final price cannot exceed initial price.",
        path: ["PriceFinal"],
      });
    }
  });

export type FeatureInputFormValues = z.infer<typeof featureInputSchema>;

export function defaultFeatureInput(): FeatureInput {
  return { ...DEFAULT_FEATURE_INPUT };
}

export function fieldsGroupedBySection(): Record<FeatureSectionId, FeatureFieldMeta[]> {
  const empty = Object.fromEntries(
    FEATURE_SECTIONS.map((s) => [s.id, [] as FeatureFieldMeta[]]),
  ) as Record<FeatureSectionId, FeatureFieldMeta[]>;
  for (const field of FEATURE_FIELD_METAS) {
    empty[field.section].push(field);
  }
  return empty;
}

export function metaForFeatureKey(key: keyof FeatureInput): FeatureFieldMeta | undefined {
  return FEATURE_FIELD_METAS.find((m) => m.key === key);
}
