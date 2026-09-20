# System Patterns

## Arquitectura del monorepo

- `uis/`: aplicaciones visibles para usuarios. `website` es pública, `backoffice` es interna y `talent-pipeline-tracker` conserva su alcance propio.
- `services/api`: backend FastAPI centralizado; se amplía por dominios antes de considerar servicios separados.
- `packages/`: librerías y contratos TypeScript reutilizables y versionables.
- `shared/`: esquemas, plantillas y recursos compartidos que no constituyen un paquete.
- `agents/`, `skills/` y `mcps/`: agentes, capacidades y servidores MCP del producto.
- `data/`: flujo de datos desde fuentes sin modificar hasta resultados procesados y evaluaciones.
- `workflows/`: automatizaciones entre sistemas.
- `infra/`, `scripts/` e `internal/`: despliegue, automatización ligera y herramientas internas estructuradas.
- `.agents/`: reglas y skills para asistentes de código; nunca contiene lógica de producto.

## Patrones de diseño

- API en capas con DDD ligero: routers, schemas, services, repositories, models y core.
- Rutas versionadas bajo `/api/v1` y contratos validados con Pydantic.
- Organización por dominio de negocio, no por operación CRUD global.
- Componentes de UI pequeños, accesibles y con estados visibles.
- Tipos compartidos cuando dos o más consumidores necesitan el mismo contrato.
- Funciones puras para filtros, búsquedas, transformaciones y agregaciones cuando sea posible.

## Flujo de datos objetivo

```text
Fuentes departamentales
  -> data/raw
  -> data/pipelines
  -> data/process
  -> services/api
  -> uis/backoffice y agentes
  -> reportes, alertas y consultas ejecutivas
```

Cada dato ejecutivo debe conservar origen, fecha de actualización y reglas de validación. Las evaluaciones de calidad viven en `data/eval`.
