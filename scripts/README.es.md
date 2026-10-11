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

### Tests

```bash
uv run --project services/api pytest scripts/tests
```
