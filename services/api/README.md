# AgentHub API

API FastAPI centralizada de Nexova. La base expone un endpoint versionado de salud y está preparada para crecer por dominios de negocio.

## Preparación

Desde la raíz del monorepo:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r services/api/requirements-dev.txt
```

## Desarrollo

```bash
.venv/bin/python -m uvicorn app.main:app --reload --app-dir services/api
```

- API: `http://localhost:8000`
- Salud: `http://localhost:8000/api/v1/health`
- OpenAPI: `http://localhost:8000/docs`

## Pruebas

```bash
PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests
```