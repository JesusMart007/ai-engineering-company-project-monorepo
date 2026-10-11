# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Incident scripts

They run with the API's environment (`services/api`), which installs the shared `nexova_shared` package (`packages/shared`). From the repo root:

### `analyze.py`: helpdesk CSV analyzer

```bash
uv run --project services/api python scripts/analyze.py scripts/incidents-nexova.csv
```

### `seed_incidents.py`: historical load for the incident manager

```bash
uv run --project services/api python scripts/seed_incidents.py   # defaults to scripts/incidents-nexova.csv
```

Validates every row with the analyzer rules, maps it as described in `CONTEXT-nexova-incident-manager.es.md` and inserts it into the API's database (`INCIDENTS_DB_PATH`). Idempotent: `ticket_id` is stored as the unique `source_id` and rows already loaded are skipped. See [README.es.md](./README.es.md) for details.

### Tests

```bash
uv run --project services/api pytest scripts/tests
```
