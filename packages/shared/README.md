# `packages/shared`

Código compartido del monorepo. Contiene dos paquetes independientes:

- **`types/`** (`@repo/shared-types`): tipos TypeScript.
- **`python/nexova_shared/`** (`nexova-shared`): lógica Python compartida por `scripts/` y `services/api`.

## `nexova_shared`

| Módulo | Contenido | Lo usan |
| --- | --- | --- |
| `csv_validation.py` | Validación y métricas del CSV del helpdesk (reglas de [`CONTEXT-nexova.es.md`](../../CONTEXT-nexova.es.md)). Nunca devuelve valores de campos, solo conteos y nombres de campo. | `scripts/analyze.py`, `scripts/seed_incidents.py`, `services/api` (`/api/incidents/analyze`) |
| `incidents.py` | Enums del gestor de incidencias (`IncidentStatus`, `IncidentCategory`, `IncidentOrigin`, `Branch`), transiciones de estado y transformación CSV → modelo (de [`CONTEXT-nexova-incident-manager.es.md`](../../CONTEXT-nexova-incident-manager.es.md)). | `services/api`, `scripts/seed_incidents.py` |

Los valores permitidos se definen **solo aquí**; la API y el seed los importan.

### Cómo se instala

No hay workspace de uv: la API lo declara como dependencia por ruta (editable), así que `uv sync` en `services/api` lo deja importable para la API y para los scripts que se ejecutan con su entorno:

```toml
# services/api/pyproject.toml
[tool.uv.sources]
nexova-shared = { path = "../../packages/shared", editable = true }
```

### Tests

```bash
# desde la raíz del repo
uv run --project services/api pytest packages/shared/tests
```
