# Frontend Guidelines & Craft Rules

Every agent implementing or modifying code in `frontend/` MUST adhere to these rules:

1. **Design System Authority**: Strictly follow the Atelier Editorial Design System defined in `DESIGN.md` and `frontend/src/index.css`:
   - Warm chalk canvas (`var(--bg-primary, #f9f7f5)`), pure white panels (`var(--bg-secondary, #ffffff)`), and linen borders (`var(--panel-border, #e5e2dd)`).
   - Brand Garnet accent (`var(--brand-burgundy, #6b0008)`) and espresso primary (`var(--text-primary, #1c1917)`).
   - Typography: `var(--font-serif)` for titles/headings, `var(--font-mono)` with `tabular-nums` for currency/dates/codes/casillas, and `var(--font-sans)` for UI controls and body text.
2. **Anti-Slop Laws**:
   - **Zero Emojis**: Strictly forbidden in product UI. Use SVG icons from `lucide-react` (14px–18px).
   - **De-carding**: Never nest bordered cards inside bordered cards. Use flat rows, background wells, and whitespace dividers.
   - **No Layout-thrashing Animations**: Only animate `transform` and `opacity` with `var(--ease-out)`. Never animate `width`/`height` or use spring/bounce curves.
   - **Terse Copy**: Eliminate filler or robotic subtitles; keep copy confident and direct.
3. **Quality & Compilation**:
   - Always run `npm run build` (or `tsc -b && vite build`) and ensure it completes with zero errors before marking any frontend task done.
