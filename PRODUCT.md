# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React 19, TypeScript, Vite, Motion, Lucide React (Frontend); Python, FastAPI, SQLite, Hexagonal Architecture (Backend).

## Users

Individual landlords and property owners in Spain managing personal rental portfolios and tax declarations.

## Product Purpose

Provide a comprehensive property management web platform that simplifies rental property cataloging, lease contract tracking, and automated Spanish tax calculations (AEAT IRPF draft generation).

## Positioning

End-to-end rental portfolio management seamlessly integrated with a Spanish fiscal calculation engine (amortizations, reductions, net income calculation, and AEAT-compliant tax reporting).

## Operating Context

Landlords reviewing property status, managing active tenant contracts, classifying rental income and deductible expenses, and preparing tax draft reports for Spanish annual IRPF declarations.

## Capabilities and Constraints

- **Confirmed Capabilities**:
  - Property catalog & listing with detailed photo galleries and full-width cards
  - Shielded JWT Authentication & Multi-Tenancy Data Isolation
  - Cadastral & Acquisition fiscal property data management
  - Lease contract tracking and management
  - Income and expense fiscal classification (amortizable, deductible, non-deductible)
  - Fiscal Calculation Engine (Amortization, Reductions, Net Yield)
  - Tax report & AEAT Draft PDF generator
- **Technical & Architectural Constraints**:
  - Hexagonal Architecture (Domain, Application Ports, Infrastructure Adapters)
  - Spec-Driven Development (SDD) workflow governed by `SDD-WoW.md` and `agents.md`
  - Strict Port/Adapter naming conventions

## Brand Commitments

- **Name**: Rental Property Web Platform ("Rental Handler")
- **Visual Identity**: Modern, high-craft UI aesthetic with rich data presentation, fluid micro-interactions, dark/light theme support, and clear data visualization.

## Evidence on Hand

- `feature_list.json`: Detailed epic and feature status tracking.
- `specs/epics/E-01-fiscalidad/vision_y_dominio.md`: Technical specification for the tax engine.
- `SDD-WoW.md`: Development workflow guidelines.
- Runnable frontend app on port 5173 and backend on port 8000.

## Product Principles

1. **Fiscal Precision**: Strict adherence to Spanish AEAT tax calculation rules and guidelines.
2. **Data Isolation & Security**: Uncompromising multi-tenant security ensuring complete user data isolation.
3. **Task Efficiency**: Streamlined workflows for logging expenses, updating contracts, and extracting tax reports.
4. **Impeccable Craft**: High visual excellence, responsive dynamic layouts, clear typography, and tactile motion feedback.
