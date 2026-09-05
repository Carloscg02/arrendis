---
name: Rental Handler
description: Modern, professional rental property and Spanish fiscal management platform with editorial craft and de-slopped UI.
colors:
  bg-primary: "#090a0c"
  bg-secondary: "#111317"
  bg-tertiary: "#181b20"
  surface: "#14171d"
  surface-subtle: "#1c2027"
  border-subtle: "rgba(255, 255, 255, 0.08)"
  border-hover: "rgba(255, 255, 255, 0.16)"
  border-active: "rgba(255, 255, 255, 0.28)"
  accent-primary: "#f3f4f6"
  accent-primary-hover: "#ffffff"
  accent-primary-fg: "#090a0c"
  accent-muted: "#38bdf8"
  text-primary: "#f9fafb"
  text-secondary: "#9ca3af"
  text-muted: "#6b7280"
  danger: "#f87171"
  danger-subtle: "rgba(248, 113, 113, 0.12)"
  warning: "#fbbf24"
  warning-subtle: "rgba(251, 191, 36, 0.12)"
  success: "#34d399"
  success-subtle: "rgba(52, 211, 153, 0.12)"
typography:
  display:
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  h1:
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  h2:
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  body:
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.005em"
  body-sm:
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "-0.01em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.accent-primary}"
    textColor: "{colors.accent-primary-fg}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "{colors.accent-primary-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
---

# Design System & Guidelines: Rental Handler

## Overview

Rental Handler is a high-precision real estate and Spanish fiscal calculation platform. Its visual design language rejects generic AI-generated aesthetics ("AI Slop"—unnecessary nested cards, heavy borders, neon gradients, and redundant microcopy) in favor of an understated, confident, high-craft interface inspired by Stripe and Vercel.

Key visual attributes:
- **Quiet Authority**: Dark obsidian surfaces (`#090a0c`) with crisp typographic hierarchy and restrained contrast.
- **De-carded Structure**: Flat layouts and natural white space separate distinct functional zones instead of stacking borders and nested cards.
- **Data Density with Breathability**: Monospace values for financial precision, cleanly aligned metadata tables, and compact contextual actions.
- **Smooth, Organic Transitions**: High-performance exponential easing (`cubic-bezier(0.16, 1, 0.3, 1)`); strict ban on bounce or spring wobbles and layout property animation.

## Colors

- **Backgrounds**: Rooted in deep slate-black (`#090a0c`, `#111317`, `#181b20`), providing an immersive dark canvas that reduces eye fatigue for data-heavy operations.
- **Surfaces**: Tonal subtle elevation (`#14171d`, `#1c2027`) used sparingly for focused modals or dropdowns.
- **Borders**: Highly restrained semi-transparent borders (`rgba(255, 255, 255, 0.08)`) only when separation is functionally critical. No double borders or borders within cards.
- **Accents**: Monochromatic primary accent (`#f3f4f6` off-white text on dark, dark on white buttons), paired with restrained semantic accents (Emerald green for positive yield, Amber for deductions, Coral red for liabilities or deletions).
- **No Neon Gradients**: Pure, solid or subtle radial light washes only. No purple-to-blue saturated meshes or floating glow blobs.

## Typography

- **Font Family**: `Outfit`, backed by system fallbacks (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif).
- **Scale**:
  - `Display` (2.75rem / 44px, weight 600, line-height 1.15, tracking -0.035em): For key fiscal summary numbers and page hero titles.
  - `H1` (2.0rem / 32px, weight 600, line-height 1.2, tracking -0.025em): Main page titles.
  - `H2` (1.35rem / 21px, weight 500, line-height 1.3, tracking -0.015em): Section headings.
  - `Body` (0.9375rem / 15px, weight 400, line-height 1.55): Content text and table values.
  - `Body Small / Label` (0.8125rem / 13px, weight 500, line-height 1.5, uppercase tracking 0.04em): Form labels and status badges.
- **Anti-Slop Rule**: Delete redundant explanatory subtitles beneath self-evident titles (e.g., replace "Propiedades: Administra aquí tus propiedades" with simply "Propiedades").

## Layout

- **Maximum Width**: 1280px centered (`margin: 0 auto; padding: 0 1.5rem;`).
- **De-carding Protocol**: Lists of items (properties, contracts, expenses) are rendered as clean tabular rows or minimalist flat panels separated by vertical whitespace and single hairline dividers, not floating boxes with heavy shadows.
- **Spacing Rhythm**: Consistent 8px grid (`8px`, `16px`, `24px`, `32px`, `48px`, `64px`).

## Elevation & Depth

- **Flat Tonal Hierarchy**: Depth is achieved through tonal contrast (e.g. `#090a0c` canvas vs `#111317` surface), not heavy blurred drop-shadows.
- **Shadows**:
  - Flyout / Dropdown / Modal: `0 16px 40px -8px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.08)`.
  - No shadows on flat cards or inline lists.

## Shapes

- **Radius Scale**:
  - Inputs & Buttons: `8px` (`var(--radius-md)`)
  - Panels & Modals: `12px` to `16px` (`var(--radius-lg)` to `var(--radius-xl)`)
  - Badges & Pills: `9999px` (`var(--radius-pill)`) or `4px` (`var(--radius-sm)`)
- Avoid exaggerated, toy-like pill corners on full-width panels.

## Components

- **Buttons**:
  - Primary: Off-white background, deep black text, slight brightness bump on hover (`transform: translateY(-1px)` maximum, no extreme scaling).
  - Secondary / Outline: Transparent background with subtle border, becoming slightly brighter on hover.
  - Ghost / Link: No border, text-secondary shifting to text-primary.
- **Inputs & Selects**:
  - Understated background (`#090a0c`), 1px subtle border, soft focus ring with 0.08 alpha glow.
- **Modals & Overlays**:
  - Darkened backdrop with blur (`rgba(0,0,0,0.75)` + `backdrop-filter: blur(8px)`).
  - Modal window uses `#111317`, crisp 1px border, smooth enter transition via opacity + translateY(6px), no bounce springs.
- **Tables & Lists**:
  - Clean edge-to-edge layout, header labels muted and uppercase, hover states subtle (`rgba(255, 255, 255, 0.02)`).
  - Secondary actions (edit, delete, view contract) concealed behind an overflow button or aligned quietly at the end of the row.

## Do's and Don'ts

### Do
- Use generous vertical padding (`3rem` to `4rem`) between major sections.
- Format all euro amounts and fiscal numbers consistently with tabular numbers and clean currency symbols.
- Keep primary navigation clean and minimal with crisp underline indicators or quiet pill highlights.
- Rely on negative space as the primary divider between information blocks.

### Don't
- DO NOT wrap every piece of information in an isolated `glass-panel` or card with its own border and shadow.
- DO NOT use bouncy spring cubic-bezier easing (`cubic-bezier(0.175, 0.885, 0.32, 1.275)`). Use smooth exponential deceleration (`cubic-bezier(0.16, 1, 0.3, 1)`).
- DO NOT animate layout properties (`width`, `height`, `margin`, `padding`). Animate `transform` and `opacity`.
- DO NOT place obvious subtitle text under headings explaining the purpose of a button or page.
- DO NOT crowd rows with 4+ visible action buttons; tuck secondary actions into context menus or detail views.
