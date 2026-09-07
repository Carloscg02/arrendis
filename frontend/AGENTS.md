# Frontend Guidelines

- **Design Tokens**: Follow the light porcelain system defined in `DESIGN.md` (`#f8fafc` canvas, `#ffffff` panels, `#0f172a` typography).
- **Anti-Slop Laws**: Strictly zero emojis in product UI (use Lucide SVG icons), no nested card-in-card borders, no layout-thrashing animations (`width`/`height`), no bounce easings.
- **Craft Skill**: When creating, redesigning, or refactoring UI components, follow the instructions in `.agent/skills/anti-slop-ui/SKILL.md`.
- **Quality**: Always ensure `npm run build` passes with zero errors before completing frontend tasks.
