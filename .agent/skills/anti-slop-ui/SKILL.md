---
name: anti-slop-ui
description: Use when designing, refactoring, styling, or evaluating frontend interfaces in any web framework (React, Vue, Svelte, HTML/CSS). Enforces high-craft, elegant light-porcelain design, eliminates generic AI slop (emojis, neon gradients, nested cards, layout shifts), and provides production-grade UI recipes.
version: 1.0.0
---

# Anti-Slop UI & Frontend Craft Playbook

A universal, production-grade guide to designing and refactoring modern web interfaces. Rejects generic AI-generated aesthetics ("AI Slop") in favor of restrained, elegant, high-craft interfaces inspired by Stripe, Linear, and Vercel.

---

## 1. The 6 Non-Negotiable "Anti-Slop" Laws

Whenever writing HTML, CSS, JSX, or components, you must adhere to these 6 rules:

1. **Strictly Zero Emojis in Product UI**:
   - **Never**: Use emojis (`🏠`, `📊`, `⚠️`, `🟢`, `🔴`, `📋`, `✨`) as interface iconography, buttons, or status badges.
   - **Always**: Use SVG icon libraries (e.g., `lucide-react`, `lucide-vue`, Heroicons, or Phosphor) with explicit sizes (14px–18px) and optical alignment.

2. **De-Carding Over Nested Containers**:
   - **Never**: Nest cards inside cards (`border` inside `border` inside `border` with generic shadows).
   - **Always**: Use flat stat tiles, subtle background wells, whitespace dividers, or hairline borders (`1px solid var(--border-subtle)`).

3. **No Neon / Cliché AI Gradients**:
   - **Never**: Cyan-to-purple or neon gradients on dark obsidian backgrounds.
   - **Always**: Restrained porcelain/white palettes (`#f8fafc` canvas, `#ffffff` panels) with deep slate typography (`#0f172a`).

4. **Zero Layout Shifts in Transitions & Motion**:
   - **Never**: Animate layout properties (`transition: width`, `transition: height`, `transition: all`). Never use bounce/spring easings (`cubic-bezier(0.175, 0.885, ...)`) for product UI.
   - **Always**: Animate only `transform` and `opacity` with exponential deceleration (`cubic-bezier(0.16, 1, 0.3, 1)`) between 150ms and 250ms.

5. **Direct, High-Density Typography (No Filler Copy)**:
   - **Never**: Add robotic filler subtitles like *"Aquí podrás gestionar tus cosas de manera rápida y eficiente"*.
   - **Always**: Keep headers confident, terse, and let the data and controls speak for themselves.

6. **Tabular Numerals & Accessible Contrast**:
   - **Always**: Use `font-variant-numeric: tabular-nums` for currency, counters, dates, and metrics to prevent jitter and misalignment.
   - **Always**: Maintain WCAG AA contrast (minimum 4.5:1 for body text, 3:1 for large display text).

---

## 2. Universal Design Token Architecture (Porcelain Palette)

When implementing or updating theme variables, use this baseline system:

```css
:root {
  /* Surfaces & Canvas */
  --bg-primary: #f8fafc;          /* Slate 50 - Page Canvas */
  --bg-secondary: #ffffff;        /* Pure White - Cards, Panels, Modals */
  --bg-tertiary: #f1f5f9;         /* Slate 100 - Inputs, Subdued wells */

  /* Hairline Borders */
  --panel-border: #e2e8f0;        /* Slate 200 - Hairline dividers */
  --panel-border-hover: #cbd5e1;  /* Slate 300 - Focus / Hover */

  /* Deep Slate Typography */
  --text-primary: #0f172a;        /* Slate 900 - Headings & Body */
  --text-secondary: #475569;      /* Slate 600 - Captions, Subheaders */
  --text-muted: #94a3b8;          /* Slate 400 - Placeholders, Inactive */

  /* High-Contrast Interactive Actions */
  --accent-primary: #0f172a;       /* Slate 900 - Primary Button BG */
  --accent-primary-hover: #1e293b; /* Slate 800 - Primary Hover */
  --accent-primary-fg: #ffffff;    /* Pure White - Primary Text */

  /* Subtle Semantic Colors (Pastel Wells + High-Contrast Text) */
  --badge-success-bg: #ecfdf5;
  --badge-success-text: #047857;
  --badge-success-border: #a7f3d0;

  --badge-warning-bg: #fffbeb;
  --badge-warning-text: #b45309;
  --badge-warning-border: #fde68a;

  --badge-danger-bg: #fef2f2;
  --badge-danger-text: #b91c1c;
  --badge-danger-border: #fecaca;

  /* Shadows (Subtle, Layered Optical Depth) */
  --shadow-card: 0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05);
  --shadow-card-hover: 0 4px 12px -2px rgba(15, 23, 42, 0.08);
  --shadow-modal: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.06);

  /* Micro-radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-pill: 9999px;

  /* Motion */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 3. High-Craft Component Patterns

### A. Primary & Secondary Buttons
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.625rem 1.25rem;
  font-weight: 500;
  font-size: 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background-color 0.15s var(--ease-out), transform 0.15s var(--ease-out);
}
.btn:active { transform: scale(0.98); }
.btn-primary {
  background: var(--accent-primary);
  color: var(--accent-primary-fg);
}
.btn-primary:hover {
  background: var(--accent-primary-hover);
  transform: translateY(-1px);
}
.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--panel-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
.btn-secondary:hover {
  background: var(--bg-tertiary);
  border-color: var(--panel-border-hover);
}
```

### B. Flat Stat / KPI Tiles (No Over-Framing)
```css
.kpi-tile {
  background: var(--bg-secondary);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow-card);
}
.kpi-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.kpi-value {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
  margin-top: 0.35rem;
}
```

### C. Status Badges & Indicators
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-sm);
}
.badge-success {
  background: var(--badge-success-bg);
  color: var(--badge-success-text);
  border: 1px solid var(--badge-success-border);
}
.badge-danger {
  background: var(--badge-danger-bg);
  color: var(--badge-danger-text);
  border: 1px solid var(--badge-danger-border);
}
```

---

## 4. Refactoring Protocol (Step-by-Step)

When tasked with cleaning up or improving an existing UI:

1. **Identify Incumbent Truth**: Inspect the existing CSS and components before changing code. Look for hardcoded colors, inline styles, and emojis.
2. **Audit for AI Slop**:
   - Grep for emojis: `grep -rn '[^\x00-\x7F]' src/` (or check common icons).
   - Grep for bounce easings: `cubic-bezier(0.175, 0.885`.
   - Grep for layout animation: `transition:.*width|transition:.*height`.
3. **Execute De-Slop**:
   - Replace emojis with Lucide / SVG icons.
   - De-card nested containers.
   - Consolidate color tokens into `:root`.
   - Tighten typography (remove filler descriptions, add `tabular-nums` to financial data).
4. **Verification**:
   - Run typecheck and bundle build (`npm run build` or framework equivalent).
   - Confirm responsive behavior (mobile, tablet, desktop).
   - Ensure zero regressions in business logic, state management, or API calls.
