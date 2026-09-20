# Project Brief

## Misión

Construir AgentHub, la plataforma de operaciones ejecutivas de Nexova Solutions, para centralizar KPIs, alertas, reportes semanales y consultas de negocio respaldadas por datos trazables.

## Objetivos

- Reducir la preparación manual de informes para Dirección Ejecutiva.
- Dar a Laura Mendoza y a responsables autorizados una vista actualizada de ventas, selección, formación, soporte, RR. HH. y marketing.
- Detectar riesgos mediante umbrales y reglas de negocio explícitas.
- Evolucionar hacia un asistente conversacional sin inventar métricas ni fuentes.
- Mantener cada aplicación, servicio y capacidad de IA en su límite de responsabilidad dentro del monorepo.

## Stack base

- TypeScript estricto para utilidades, contratos y frontends.
- Next.js y React para aplicaciones web mantenidas como proyectos independientes en `uis/`.
- FastAPI y Pydantic para la API centralizada en `services/api`.
- Paquetes compartidos versionables en `packages/`.
- Configuración de asistentes de desarrollo en `.agents/`; agentes y skills de producto en `agents/` y `skills/`.

## Fuentes de verdad

- `CONTEXT.md`: identidad, reglas de negocio y hoja de ruta.
- `SPECS.md`: alcance del prototipo visual de AgentHub.
- `docs/ARCHITECTURE_PROPOSAL.md`: dirección arquitectónica del backend.
- README de cada carpeta: límites de responsabilidad y operación local.
