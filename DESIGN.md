---
name: Arrendis
description: Atelier Editorial Design System for Spanish real estate and fiscal management platform. Warm chalk paper canvas, literary serif typography, Swiss monospace financial precision, and Arrendis Garnet brand accent.
colors:
  bg-primary: "#f9f7f5"
  bg-secondary: "#ffffff"
  bg-tertiary: "#f2efe9"
  panel-bg: "#ffffff"
  panel-border: "#e5e2dd"
  panel-border-hover: "#c8c2b9"
  panel-border-subtle: "#eeeae4"
  text-primary: "#1c1917"
  text-secondary: "#57534e"
  text-muted: "#8c827a"
  text-disabled: "#c7c2bc"
  brand-burgundy: "#6b0008"
  brand-burgundy-hover: "#520006"
  brand-burgundy-subtle: "#fbf2f2"
  accent-primary: "#1c1917"
  accent-primary-hover: "#292524"
  accent-primary-fg: "#f9f7f5"
  accent-garnet: "#6b0008"
  accent-garnet-hover: "#520006"
  accent-garnet-fg: "#ffffff"
  success: "#2b5329"
  success-subtle: "#f2f6f1"
  success-border: "#c8dec4"
  warning: "#8f4d0a"
  warning-subtle: "#fdf6ed"
  warning-border: "#f8dfbf"
  danger: "#8c1d18"
  danger-subtle: "#fbf1f0"
  danger-border: "#f3cecc"
typography:
  serif: "'Newsreader', Georgia, 'Times New Roman', serif"
  mono: "'Space Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace"
  sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
rounded:
  none: "0px"
  xs: "2px"
  sm: "4px"
  md: "6px"
  pill: "9999px"
---

# Design System & Guidelines: Arrendis (Atelier Editorial)

## 1. Overview & Aesthetic Philosophy

**Arrendis** is a high-precision real estate portfolio and Spanish fiscal calculation platform (AEAT Modelo 100). Its visual identity rejects generic SaaS aesthetics and AI slop (nested card borders, neon gradients, emojis in UI, and conversational filler text) in favor of the **Atelier Editorial** design philosophy:

- **Tactile Paper Canvas**: Rooted in warm chalk paper (`#f9f7f5`) and crisp white panels (`#ffffff`), bound by warm linen hairline dividers (`#e5e2dd`).
- **Architectural Typography**: Literary serif (`Newsreader`) for titles and section presence; Swiss monospace (`Space Mono`) for fiscal figures, cadastral codes, and dates; and clean sans-serif (`Inter`) for UI controls and body text.
- **Brand Authority**: Arrendis Garnet (`#6b0008`) used intentionally for primary brand identity, active tabs, and high-impact calls to action.
- **Quiet Data Density**: Financial information is presented with breathability, aligned monospace numbers, and zero visual clutter.

---

## 2. The 6 Non-Negotiable "Anti-Slop" Laws

Every screen, modal, component, and spec in Arrendis MUST adhere to these 6 laws:

1. **Strictly Zero Emojis in Product UI**:
   - **Never**: Use emojis (`🏠`, `📊`, `⚠️`, `🟢`, `🔴`, `📋`, `✨`) as interface icons, button graphics, or status bullets.
   - **Always**: Use SVG icons from `lucide-react` (14px–18px) with optical alignment and deliberate semantic color.

2. **De-Carding Over Nested Containers**:
   - **Never**: Nest cards inside cards (`border` inside `border` with generic drop-shadows).
   - **Always**: Use flat tabular rows, subtle background wells (`var(--bg-tertiary)`), hairline dividers (`1px solid var(--panel-border)`), or generous whitespace.

3. **No Neon / Cliché Dark Gradients**:
   - **Never**: Cyan-to-purple, dark obsidian neon, or generic glassmorphism gradients.
   - **Always**: High-contrast, warm physical materials: warm chalk paper (`#f9f7f5`), pure white surfaces, and deep espresso text (`#1c1917`).

4. **Zero Layout Shifts in Motion & Transitions**:
   - **Never**: Animate layout properties (`width`, `height`, `margin`, `padding`). Never use bouncy spring easings.
   - **Always**: Animate only `transform` and `opacity` with exponential deceleration (`cubic-bezier(0.16, 1, 0.3, 1)`) between 150ms and 250ms.

5. **Direct, Terse Copy (No Conversational Slop)**:
   - **Never**: Add redundant explanatory filler under titles like *"Aquí podrás gestionar tus contratos de manera rápida y sencilla"*.
   - **Always**: Keep headers terse, confident, and self-evident. Let the data and controls speak for themselves.

6. **Tabular Numerals & Monospace Precision**:
   - **Always**: Render monetary amounts (€), percentages (%), official AEAT casillas (`[0102]`), dates, and cadastral references with `font-family: var(--font-mono)` and `font-variant-numeric: tabular-nums`.

---

## 3. Design Tokens (CSS Variables Reference)

All styling in `frontend/src/` must consume CSS variables from `frontend/src/index.css`:

```css
:root {
  /* Surfaces & Paper Canvas */
  --bg-primary: #f9f7f5;               /* Warm chalk paper */
  --bg-secondary: #ffffff;             /* Pure white surface */
  --bg-tertiary: #f2efe9;              /* Warm stone control well */
  --bg-elevated: #faf8f5;

  /* Borders & Dividers */
  --panel-border: #e5e2dd;             /* Linen hairline divider */
  --panel-border-hover: #c8c2b9;
  --panel-border-subtle: #eeeae4;

  /* Typography */
  --text-primary: #1c1917;             /* Deep espresso charcoal */
  --text-secondary: #57534e;           /* Warm stone body */
  --text-muted: #8c827a;               /* Muted taupe metadata */
  --text-disabled: #c7c2bc;            /* Inactive / placeholder */

  /* Fonts */
  --font-serif: 'Newsreader', Georgia, 'Times New Roman', serif;
  --font-mono: 'Space Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  /* Arrendis Garnet Brand Accent */
  --brand-burgundy: #6b0008;
  --brand-burgundy-hover: #520006;
  --brand-burgundy-subtle: #fbf2f2;
  --brand-burgundy-border: #f5d0d3;
  --brand-burgundy-ring: rgba(107, 0, 8, 0.16);

  /* Primary Interactive Elements */
  --accent-primary: #1c1917;           /* Espresso black */
  --accent-primary-hover: #292524;
  --accent-primary-fg: #f9f7f5;

  --accent-garnet: #6b0008;            /* Brand Garnet */
  --accent-garnet-hover: #520006;
  --accent-garnet-fg: #ffffff;

  /* Semantic Statuses (Muted Editorial) */
  --success: #2b5329;
  --success-subtle: #f2f6f1;
  --success-border: #c8dec4;

  --warning: #8f4d0a;
  --warning-subtle: #fdf6ed;
  --warning-border: #f8dfbf;

  --danger: #8c1d18;
  --danger-subtle: #fbf1f0;
  --danger-border: #f3cecc;

  /* Radii */
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-pill: 9999px;

  /* Shadows (Restrained Hairline Depth) */
  --shadow-card: 0 1px 3px rgba(28, 25, 23, 0.04);
  --shadow-card-hover: 0 4px 16px -2px rgba(28, 25, 23, 0.06);
  --shadow-modal: 0 20px 40px -10px rgba(28, 25, 23, 0.12), 0 0 0 1px rgba(28, 25, 23, 0.05);

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 4. Component Patterns & Usage

### A. Buttons

```html
<!-- Primary (Espresso Dark) -->
<button class="btn btn-primary">Guardar cambios</button>

<!-- Brand Garnet (Hero Action) -->
<button class="btn btn-garnet">Crear primer inmueble</button>

<!-- Secondary (White Surface with Linen Border) -->
<button class="btn btn-secondary">Cancelar</button>

<!-- Compact Action (Inside tables/lists) -->
<button class="btn btn-secondary btn-sm">
  <FileText size={14} /> Ver borrador
</button>
```

### B. Typography & Headers

```html
<!-- Page Title: Editorial Serif -->
<h1 style="font-family: var(--font-serif); font-weight: 400; font-size: 2rem; color: var(--text-primary); letter-spacing: -0.02em;">
  Cartera de Inmuebles
</h1>

<!-- Kicker / Overline: Monospace uppercase label -->
<span style="font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--brand-burgundy);">
  Modelo 100 AEAT · Ejercicio 2026
</span>
```

### C. Financial Amounts & Metrics (Mono tabular)

```html
<!-- Always use monospace for currency and calculations -->
<span style="font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-weight: 600; color: var(--text-primary);">
  1.250,00 €
</span>
```

### D. Status Badges

```html
<!-- Green / Active / Reconciled -->
<span class="badge badge-success">Arrendado</span>

<!-- Garnet / Brand / Primary highlight -->
<span class="badge badge-garnet">Deducible IRPF</span>

<!-- Neutral / Inactive -->
<span class="badge badge-neutral">Borrador</span>

<!-- Warning / Pending -->
<span class="badge badge-warning">Pendiente revisión</span>
```

### E. Tables & Lists (Flat, De-carded)

- Use edge-to-edge tabular structure with `border-bottom: 1px solid var(--panel-border)`.
- Table headers: `font-size: 0.75rem`, `font-family: var(--font-mono)`, uppercase, color `var(--text-muted)`.
- Numeric columns: right-aligned with `tabular-nums`.
- Actions: tucked quietly at the end of the row.

---

## 5. Specification Authoring Protocol (For AI Spec Authors)

When writing `specs/<feature>/design.md`, the UI design section must:

1. **Provide an ASCII Wireframe**: Depict the structural hierarchy, panels, and navigation clearly.
2. **Explicit Token Mapping**: Specify which CSS variables govern backgrounds, text, and borders.
3. **List Required Icons**: Explicitly name icons from `lucide-react` (e.g. `Plus`, `FileText`, `Building2`, `Calendar`). Never include emojis in the specification.
4. **Define UI States**: Document Empty State, Loading/Skeleton State, Data-Populated State, and Error State.
