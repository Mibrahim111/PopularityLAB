# UI design notes

Use this file to agree on look-and-feel **before** changing code. When you decide something here, update the referenced files so the app stays consistent.

## Principles (from product spec)

- Clean, technical, **dark neutral** palette—Steam-adjacent, not a Steam clone.
- Data-dense but readable; favor spacing and hierarchy over decoration.

## Typography

| Role | Current implementation | Where to change |
|------|-------------------------|-----------------|
| Body | **Inter** (`next/font/google`), CSS variable `--font-sans` | `app/layout.tsx` |
| Labels / code / headers accent | **JetBrains Mono** (`--font-mono`) | `app/layout.tsx`, Tailwind class `font-mono` |

**Ideas to discuss:** switch body to **IBM Plex Sans**, mono to **Geist Mono**, or reduce mono usage to navigation only.

## Color tokens (HSL via CSS variables)

All semantic colors live in **`app/globals.css`** under `:root`. Tailwind maps them in **`tailwind.config.ts`** (`background`, `foreground`, `primary`, `muted`, `border`, `card`, etc.).

| Token | Role |
|-------|------|
| `--background` / `--foreground` | Page surface and default text |
| `--card` | Panels and elevated surfaces |
| `--muted` / `--muted-foreground` | Secondary text and inset regions |
| `--primary` / `--accent` | Actions and focus emphasis |
| `--border` / `--ring` | Dividers and focus rings |

**Ideas:** cooler blues vs warmer neutrals; bump `--primary` saturation slightly for CTAs; add a dedicated `--danger` / `--success` for result states (currently derived inline in components).

## Radius and density

- **`--radius`** in `app/globals.css` (default `0.5rem`). Used by Tailwind `rounded-lg` / component radii.
- **Container width:** `tailwind.config.ts` → `theme.container.screens["2xl"]` (currently `1200px`).

## Components

- Prefer **`components/ui/*`** for primitives (button, input, card). Keep variants minimal until shadcn blocks are added with `npx shadcn@latest add …`.
- Charts: **Recharts**—keep chart colors aligned with `--primary` / `--muted-foreground` where possible.

## Feature form UX

- Field labels and sections come from **`lib/features.ts`** only (single source of truth). Edit copy there, not in scattered strings.
- What-if “focus” fields are **`WHAT_IF_FOCUS_KEYS`** in `lib/features.ts`; tweak when modeling priorities change.

## Backend alignment

- Colors/fonts do not affect API behavior. **`FeatureInput`** / Zod schema in **`lib/features.ts`** must stay aligned with **`backend/schemas/request.py`**.
- **What-if:** `modified_features` keys must be **`FeatureInput`** PascalCase fields (not engineered `num__*` preprocessor names). The FastAPI router validates keys against `FeatureInput.model_fields`.

---

## Collaboration workflow

Discuss typography and palette changes **here first**, then mirror them in code:

| Topic | Where to capture intent | Files that implement |
|-------|-------------------------|----------------------|
| Fonts / hierarchy | `### Typography decisions` | `app/layout.tsx`, `tailwind.config.ts` |
| Neutral vs accents | `### Palette decisions` | `app/globals.css` |
| Density / radius | `### Density decisions` | `app/globals.css` (`--radius`), Tailwind utilities |

### Typography decisions

<!-- Example: Use Inter only for body; reserve mono for data outputs. -->

### Palette decisions

<!-- Example: Cool down `--muted` for higher contrast forms. -->

### Density decisions

<!-- Example: Tighter grid on `/predict` at `lg` breakpoint. -->

---

### Scratchpad (edit freely)

<!-- Example:
- [ ] Try softer `--border` for less grid-like forms
- [ ] Landing cards: add subtle gradient border
-->
remove the text on the icons "Mode=classification) post predict etc..
make the icons classification -> 