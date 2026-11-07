# Contrato de Diseno: Arrendis (Atelier Editorial)

> Arquetipo: Warm Editorial / Precision. Lienzo tactil tipo papel calido, tipografia literaria y precision fiscal monospace suiza. Sin AI Slop ni emojis.

---

## 1. Direccion Estetica y Filosofia
- **Lienzo de papel calido**: Fondo base papel tiza (`#f9f7f5`) y paneles blancos puros (`#ffffff`) con filetes lino hairline (`#e5e2dd`).
- **Tipografia editorial**: Titulares en serif literaria (`Newsreader`), datos fiscales y cifras en mono (`Space Mono`), UI en sans (`Inter`).
- **Acento de marca**: Granate Arrendis (`#6b0008`) reservado para identidad principal, tabs activos y CTAs de impacto.
- **Densidad de datos serena**: Cifras fiscales con espaciado respirable, alineadas y tabulares (`font-variant-numeric: tabular-nums`).

---

## 2. Leyes Duras Anti-Slop (No Negociables)
1. **Cero emojis en UI**: Prohibido usar emojis como iconos o balas. Usar siempre SVGs opticos de `lucide-react` (14-18px).
2. **De-Carding**: Prohibido anidar tarjetas dentro de tarjetas. Emplear filas tabulares planas, filetes de 1px o wells sutiles.
3. **Cero degradados neon o cliches oscuros**: Contraste alto con materiales fisicos calidos y texto espresso (`#1c1917`).
4. **Cero layout shifts en movimiento**: Solo animar `transform` y `opacity` con deceleracion exponencial (150-250ms).
5. **Copy sobrio y directo**: Sin frases de relleno condescendientes ni explicaciones obvias bajo encabezados.
6. **Mobile-First & Touch Targets**: Todo layout responsive desde 360px; tactiles minimo 44x44px; safe-areas en movil/PWA.
7. **Regla de los 4 estados**: Toda vista o lista debe implementar explicitamente Loading, Empty, Error y Populated.

---

## 3. Design Tokens (CSS Variables Reference)
```css
:root {
  --bg-primary: #f9f7f5;          /* Warm chalk paper canvas */
  --bg-secondary: #ffffff;        /* Pure white panel */
  --bg-tertiary: #f2efe9;         /* Warm stone control well */
  --panel-border: #e5e2dd;        /* Linen hairline divider */
  --panel-border-hover: #c8c2b9;
  --text-primary: #1c1917;        /* Deep espresso charcoal */
  --text-secondary: #57534e;      /* Warm stone body */
  --text-muted: #8c827a;          /* Muted taupe metadata */
  --brand-burgundy: #6b0008;      /* Arrendis Garnet brand */
  --brand-burgundy-hover: #520006;
  --font-serif: 'Newsreader', Georgia, serif;
  --font-mono: 'Space Mono', Menlo, Consolas, monospace;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --radius-xs: 2px; --radius-sm: 4px; --radius-md: 6px;
}
```
