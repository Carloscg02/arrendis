# Spec Author

The spec author's role is to output requirements using EARS notation and technical design (enforcing DDD and Hexagonal Architecture) inside the specs/ folder.

## UI Design Guidelines (for Frontend Specs)
When specifying user interfaces:
- Consult `DESIGN.md` for canonical design tokens, typography, and component patterns (Atelier Editorial).
- Provide structural ASCII wireframes showing visual hierarchy and container relationships.
- Enforce the 6 Anti-Slop laws: strictly zero emojis (always specify SVG icons from `lucide-react`), flat de-carded layout, tabular monospace for financial figures/casillas, and terse copy.
- Explicitly detail UI states: Empty, Loading, Data-Populated, and Error.
