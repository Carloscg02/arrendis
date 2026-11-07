# Cerebro del Proyecto: `rental-handler`

> Mapa central de contexto del proyecto (Nivel 1). Consulta los documentos de Nivel 2 segun necesidad.

---

## 1. Identidad del Proyecto
- **Nombre**: `rental-handler`
- **Objetivo**: Plataforma integral de gestión de alquileres y motor de liquidación fiscal IRPF (AEAT) para propietarios en España
- **Stack Tecnologico**: `python, node, fastapi, react`
- **Dominio**: Gestión de alquileres inmobiliarios, contratos de arrendamiento y fiscalidad IRPF española (AEAT)

---

## 2. Documentos Centrales (Nivel 2)
- **[`architecture.md`](architecture.md)** - Diseno de capas, reglas de codigo y comandos de verificacion.
- **[`handoff.md`](handoff.md)** - Estado del turno actual y siguiente paso inmediato (maximo 30 lineas).
- **[`design.md`](design.md)** - Contrato de diseno visual, tokens y reglas anti-slop (Atelier Editorial).
- **[`decisions/index.md`](decisions/index.md)** - Sub-indice de decisiones tecnicas irreversibles (ADRs). Consultar solo ante decisiones arquitectonicas.

---

## 3. Modulos del Sistema (`modules/`)
- **[`auth-and-security.md`](modules/auth-and-security.md)**: Autenticacion, usuarios, sesiones JWT y blindaje HTTP.
- **[`core-property-and-contracts.md`](modules/core-property-and-contracts.md)**: Catalogo de inmuebles, contratos de arrendamiento y onboarding.
- **[`tax-and-fiscal-engine.md`](modules/tax-and-fiscal-engine.md)**: Motor de liquidacion fiscal IRPF Modelo 100 y generacion de informe AEAT.
- **[`invoice-ai-extraction.md`](modules/invoice-ai-extraction.md)**: Extraccion multimodal de facturas con IA/OCR y conciliacion CUPS.
- **[`market-valuation.md`](modules/market-valuation.md)**: Estimacion automatizada de valoracion y rentabilidad inmobiliaria.
- **[`frontend-atelier-spa.md`](modules/frontend-atelier-spa.md)**: SPA en React 19 + TypeScript con diseno Atelier Editorial y PWA.
