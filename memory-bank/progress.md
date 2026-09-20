# Progress

## Estado actual

Fundación del monorepo completada el 20 de septiembre de 2026. Las aplicaciones base y la API pueden instalarse, validarse y ejecutarse con comandos desde la raíz.

## Completado

- Se exploraron los README de la raíz y de las subcarpetas.
- Se identificó la separación entre `.agents/` y las carpetas de producto `/agents` y `/skills`.
- Se consolidó `CONTEXT.md` con el briefing canónico de Nexova AgentHub.
- Se inicializó el banco de memoria de negocio y técnico.
- Se creó `AGENTS.md` con protocolo de sesión, checks pre-commit y política stop-and-ask.
- Se añadieron reglas de Git y estilo en `.agents/rules/`.
- Se añadió la skill reutilizable `.agents/skills/deployment-preflight/`.
- Se configuraron npm workspaces y scripts raíz para desarrollo y validación.
- Se creó `uis/website` como sitio público responsive de Nexova.
- Se creó `uis/backoffice` con una vista ejecutiva funcional de KPIs, alertas y actividad.
- Se creó `services/api` como FastAPI centralizada con `GET /api/v1/health`.
- Se corrigieron errores de lint preexistentes en `uis/talent-pipeline-tracker` con autorización explícita.

## Verificación

- `npm run typecheck`: PASS.
- `npm run lint`: PASS en 3 workspaces.
- `npm run build`: PASS en 3 workspaces.
- `npm run test:api`: PASS, 1 prueba.
- Instalación npm: 0 vulnerabilidades reportadas.
- Sintaxis Python mediante `compileall`: PASS.

Persisten dos advertencias de deprecación emitidas por dependencias de Starlette/AnyIO durante pytest; no afectan el resultado y deben revisarse al actualizar esas dependencias.

## Próximos pasos

1. Definir autenticación, autorización y contratos de acceso para el backoffice.
2. Diseñar persistencia y fuentes de datos departamentales para la API.
3. Conectar el backoffice con contratos reales bajo `/api/v1`.
4. Añadir CI para ejecutar el preflight en cada pull request.
5. Incorporar observabilidad, seguridad y pruebas de integración antes del primer despliegue.