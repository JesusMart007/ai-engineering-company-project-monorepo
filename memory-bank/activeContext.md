# Active Context

## Foco actual

Configurar la fundación del monorepo y la infraestructura de soporte para agentes de desarrollo sin mezclarla con los agentes de producto.

## Decisiones activas

- `CONTEXT.md` consolida AgentHub para Nexova en Chile y Argentina.
- `.agents/` se reserva para protocolos y skills de asistentes de código.
- `agents/` y `skills/` permanecen como código de producto futuro.
- La capa inicial tendrá `uis/website`, `uis/backoffice` y `services/api`.
- `uis/talent-pipeline-tracker` se conserva sin cambios funcionales.
- El backend comienza como una API FastAPI centralizada.

## Trabajo de esta sesión

1. Inicializar y verificar el memory bank.
2. Añadir protocolos globales y una skill reutilizable de preflight.
3. Crear superficies mínimas ejecutables para website, backoffice y API.
4. Incorporar scripts raíz y validar tipos, lint, builds y pruebas.

## Riesgos abiertos

- El prototipo de `SPECS.md` usa HTML, Tailwind CDN y JavaScript vanilla, mientras las aplicaciones mantenibles usan Next.js. Cualquier migración del prototipo debe documentarse como decisión arquitectónica.
- Los orígenes CORS y las fuentes departamentales reales aún no están definidos.
- No deben asumirse contratos de autenticación, persistencia ni proveedores de IA sin una decisión explícita.
