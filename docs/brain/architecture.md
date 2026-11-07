# Arquitectura de `rental-handler`

## 1. Estilo Arquitectonico
Arquitectura Hexagonal (Puertos y Adaptadores):
- Dominio puro en el nucleo sin dependencias de I/O o librerias de infraestructura.
- Puertos (interfaces y seams publicos) para conectar logica de negocio y el mundo exterior.
- Adaptadores de entrada (CLI, API) y salida (persistencia, clientes externos).

---

## 2. Verification Commands
Comandos oficiales de verificacion ejecutados por el subagente constructor en cada ciclo:

- **Unit & Integration Tests (In-Loop TDD)**: `pytest`
  Ejecutado en cada iteracion red-green-refactor sobre los seams publicos.
- **Static / Lint Gate**: `cd frontend && npm run lint`
  Ejecutado como barrera de calidad estatica y tipado.
- **E2E / Browser UI Tests (Optional)**: `N/A`
  Ejecutado al completar features que toquen interfaz de usuario o flujos end-to-end completos.
