# Carpeta `scripts`

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Scripts de incidencias

Se ejecutan con el entorno de la API (`services/api`), que instala la lógica compartida `nexova_shared` (`packages/shared`). Desde la raíz del repo:

### `analyze.py`: analizador del CSV del helpdesk

```bash
uv run --project services/api python scripts/analyze.py scripts/incidents-nexova.csv
```

Imprime el informe de [`CONTEXT-nexova.es.md`](../CONTEXT-nexova.es.md) (100 filas: 96 válidas y 4 inválidas) y ofrece exportarlo a `results.csv`.

### `seed_incidents.py`: carga histórica del gestor de incidencias

```bash
uv run --project services/api python scripts/seed_incidents.py            # usa scripts/incidents-nexova.csv
uv run --project services/api python scripts/seed_incidents.py otro.csv   # u otro CSV con el mismo esquema
```

1. Valida cada fila con las reglas del analizador (`nexova_shared.csv_validation`).
2. La transforma según [`CONTEXT-nexova-incident-manager.es.md`](../CONTEXT-nexova-incident-manager.es.md) (`nexova_shared.incidents`): `OPEN/CLOSED/DISCARDED` → `open/resolved/discarded`; `TECHNICAL`/`ACCESS` → `technical_failure`, `BILLING`/`HR_QUERY` → `process_error`, `COMPLAINT` → `client_complaint`; `title` = primeros 120 caracteres de `description`; `date` → `created_at` (medianoche UTC, igual a `updated_at`); `origin = customer`; `branch = central`.
3. Inserta en la base de la API (`INCIDENTS_DB_PATH`, por defecto `services/api/data/incidents.json`).

Es **idempotente**: el `ticket_id` se guarda como `source_id` (único) y las filas ya cargadas se saltan. Al terminar imprime insertadas, ya existentes e inválidas, con la fila y el motivo de cada inválida (nunca imprime emails). Con el CSV de prueba: 96 insertadas y 4 inválidas (filas 18, 44, 87 y 91); una segunda ejecución inserta 0 y salta 96.

### Tests

```bash
uv run --project services/api pytest scripts/tests
```
