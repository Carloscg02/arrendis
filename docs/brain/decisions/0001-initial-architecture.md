# ADR 0001: Eleccion de arquitectura inicial

- **Estado**: Aceptado
- **Fecha**: Inicial
- **Estilo Acordado**: `hexagonal`

## 1. Contexto
Al inicializar `rental-handler` con el objetivo de `Plataforma integral de gestión de alquileres y motor de liquidación fiscal IRPF (AEAT) para propietarios en España`, se requiere establecer las fronteras arquitectonicas base.

## 2. Decision
Se adopta el estilo `hexagonal` para estructurar el codigo y los seams de prueba.

## 3. Consecuencias
Todo nuevo componente o feature desarrollada en el proyecto debe respetar las directrices registradas en `docs/brain/architecture.md`.
