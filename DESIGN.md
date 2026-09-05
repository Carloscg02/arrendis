---
name: Rental Handler
description: Modern, professional rental property and Spanish fiscal management platform with editorial craft, crisp light porcelain aesthetic, and de-slopped UI.
colors:
  bg-primary: "#f8fafc"
  bg-secondary: "#ffffff"
  bg-tertiary: "#f1f5f9"
  surface: "#ffffff"
  surface-subtle: "#f8fafc"
  border-subtle: "#e2e8f0"
  border-hover: "#cbd5e1"
  border-active: "#94a3b8"
  accent-primary: "#0f172a"
  accent-primary-hover: "#1e293b"
  accent-primary-fg: "#ffffff"
  accent-muted: "#0284c7"
  text-primary: "#0f172a"
  text-secondary: "#475569"
  text-muted: "#94a3b8"
  danger: "#dc2626"
  danger-subtle: "rgba(220, 38, 38, 0.08)"
  warning: "#d97706"
  warning-subtle: "rgba(217, 119, 6, 0.08)"
  success: "#059669"
  success-subtle: "rgba(5, 150, 105, 0.08)"
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
    backgroundColor: "{colors.bg-secondary}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
---

# Design System & Guidelines: Rental Handler (Light Theme)

## Overview

Rental Handler is a high-precision real estate and Spanish fiscal calculation platform. Its visual design language rejects generic AI-generated aesthetics ("AI Slop"—unnecessary nested cards, heavy borders, neon gradients, and redundant microcopy) in favor of an understated, confident, high-craft light interface inspired by Stripe, Vercel, and Linear.

Key visual attributes:
- **Quiet Authority**: Crisp porcelain/snow surfaces (`#f8fafc`, `#ffffff`) with deep slate typography (`#0f172a`) and restrained contrast.
- **De-carded Structure**: Flat layouts and natural white space separate distinct functional zones instead of stacking borders and nested cards.
- **Data Density with Breathability**: Monospace values for financial precision, cleanly aligned metadata tables, and compact contextual actions.
- **Smooth, Organic Transitions**: High-performance exponential easing (`cubic-bezier(0.16, 1, 0.3, 1)`); strict ban on bounce or spring wobbles and layout property animation.

## Colors

- **Backgrounds**: Rooted in crisp, clean whites and porcelain slates (`#f8fafc`, `#ffffff`, `#f1f5f9`), providing an airy, premium canvas.
- **Surfaces**: Pure white (`#ffffff`) for elevated panels, tables, and modals.
- **Borders**: Highly restrained hairline borders (`#e2e8f0` / `rgba(0, 0, 0, 0.08)`) only when separation is functionally critical. No double borders or borders within cards.
- **Accents**: Monochromatic primary accent (`#0f172a` deep obsidian button on white canvas), paired with restrained semantic accents (Emerald `#059669` for positive yield, Amber `#d97706` for deductions, Crimson `#dc2626` for liabilities or deletions).
- **No Neon Gradients**: Pure, solid or subtle tonal contrast only.

## Typography

- **Font Family**: `Outfit`, backed by system fallbacks (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif).
- **Scale**:
  - `Display` (2.75rem / 44px, weight 600, line-height 1.15, tracking -0.035em): For key fiscal summary numbers and page hero titles.
  - `H1` (2.0rem / 32px, weight 600, line-height 1.2, tracking -0.025em): Main page titles.
  - `H2` (1.35rem / 21px, weight 500, line-height 1.3, tracking -0.015em): Section headings.
  - `Body` (0.9375rem / 15px, weight 400, line-height 1.55): Content text and table values.
  - `Body Small / Label` (0.8125rem / 13px, weight 500, line-height 1.5, uppercase tracking 0.04em): Form labels and status badges.
- **Anti-Slop Rule**: Delete redundant explanatory subtitles beneath self-evident titles.

## Layout

- **Maximum Width**: 1280px centered (`margin: 0 auto; padding: 0 1.5rem;`).
- **De-carding Protocol**: Lists of items (properties, contracts, expenses) are rendered as clean tabular rows or minimalist flat panels separated by vertical whitespace and hairline dividers, not floating boxes with heavy shadows.
- **Spacing Rhythm**: Consistent 8px grid (`8px`, `16px`, `24px`, `32px`, `48px`, `64px`).

## Elevation & Depth

- **Flat Tonal Hierarchy**: Depth is achieved through crisp hairline borders (`#e2e8f0`) and subtle canvas contrast (`#f8fafc` canvas vs `#ffffff` surface), not heavy blurred drop-shadows.
- **Shadows**:
  - Flyout / Dropdown / Modal: `0 16px 36px -8px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04)`.
  - No shadows on flat cards or inline lists.

## Shapes

- **Radius Scale**:
  - Inputs & Buttons: `8px` (`var(--radius-md)`)
  - Panels & Modals: `12px` to `16px` (`var(--radius-lg)` to `var(--radius-xl)`)
  - Badges & Pills: `9999px` (`var(--radius-pill)`) or `4px` (`var(--radius-sm)`)
- Avoid exaggerated, toy-like pill corners on full-width panels.

## Components

- **Buttons**:
  - Primary: Deep slate background (`#0f172a`), pure white text, slight brightness bump on hover (`background: #1e293b`).
  - Secondary / Outline: Pure white background with hairline border (`#e2e8f0`), text `#0f172a`, hover background `#f8fafc`.
  - Ghost / Link: No border, text-secondary shifting to text-primary.
- **Inputs & Selects**:
  - Crisp white background (`#ffffff`), 1px border (`#e2e8f0`), soft focus ring (`rgba(15, 23, 42, 0.08)`).
- **Modals & Overlays**:
  - Darkened backdrop with blur (`rgba(15, 23, 42, 0.35)` + `backdrop-filter: blur(4px)`).
  - Modal window uses `#ffffff`, crisp 1px border (`#e2e8f0`), smooth enter transition via opacity + translateY(6px), no bounce springs.
- **Tables & Lists**:
  - Clean edge-to-edge layout, header labels muted and uppercase, hover states subtle (`rgba(0, 0, 0, 0.02)`).
  - Secondary actions concealed behind an overflow button or aligned quietly at the end of the row.

## Do's and Don'ts

### Do
- Use generous vertical padding (`3rem` to `4rem`) between major sections.
- Format all euro amounts and fiscal numbers consistently with tabular numbers and clean currency symbols.
- Keep primary navigation clean and minimal with crisp underline indicators or quiet pill highlights.
- Rely on negative space as the primary divider between information blocks.

### Don't
- DO NOT wrap every piece of information in an isolated `glass-panel` or card with its own border and shadow.
- DO NOT use bouncy spring cubic-bezier easing.
- DO NOT animate layout properties (`width`, `height`, `margin`, `padding`).
- DO NOT place obvious subtitle text under headings explaining the purpose of a button or page.
- DO NOT crowd rows with 4+ visible action buttons; tuck secondary actions into context menus or detail views.
