# Nexova API (`services/api`)

Backend FastAPI centralizado de Nexova. Expone estos dominios:

- **Directorio de proveedores** (`/suppliers`): registro oficial de proveedores, persistido en TinyDB. Especificación en [`09-lightweight-storage/CONTEXT-nexova.md`](../../09-lightweight-storage/CONTEXT-nexova.md).
- **Análisis de incidencias** (`/api/incidents/...`): procesa el CSV del helpdesk con la misma lógica que `scripts/analyze.py`.
- **Usuarios, perfiles y autenticación** (`/users`, `/profiles`, `/auth`): cuentas en TinyDB y JWT stateless (sin sesiones ni cookies). Todas las rutas de proveedores e incidencias exigen token.

## Instalación

Requiere Python 3.12+ y [uv](https://docs.astral.sh/uv/).

```bash
cd services/api
uv sync            # crea .venv e instala dependencias (incluye el grupo dev: pytest, httpx)
```

## Configurar `.env`

```bash
cp .env.example .env
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"   # pega el resultado en SECRET_KEY
```

La API no arranca si faltan `SECRET_KEY`, `ALGORITHM` o `ACCESS_TOKEN_EXPIRE_MINUTES`. `.env` está en `.gitignore`.

## Cargar los datos iniciales

```bash
uv run seed
# Seed completed on .../data/suppliers.json: 15 inserted, 0 skipped (already present).
```

El seeder carga los 15 proveedores de `SUPPLIERS_SEED` (copiados en `seed_data.py`). Es idempotente: comprueba cada proveedor por `name` y omite los que ya existen, así que puede ejecutarse varias veces. Cada registro se valida con `SupplierCreate` antes de insertarse.

No es obligatorio ejecutarlo: al arrancar, la API siembra la base automáticamente si está vacía.

## Arrancar la API

```bash
uv run uvicorn main:app --reload --port 8000
```

- Documentación interactiva: <http://localhost:8000/docs>
- Healthcheck: <http://localhost:8000/health>

## Tests

```bash
uv run pytest
```

Los tests usan bases TinyDB temporales (`tmp_path`) vía `SUPPLIERS_DB_PATH` y `USERS_DB_PATH`, nunca los ficheros reales, y fijan su propio `SECRET_KEY` (no leen tu `.env`).

## Variables de entorno

| Variable            | Por defecto                                   | Descripción                                                                 |
| ------------------- | --------------------------------------------- | --------------------------------------------------------------------------- |
| `SUPPLIERS_DB_PATH` | `services/api/data/suppliers.json`            | Fichero JSON de TinyDB. Una ruta relativa se resuelve desde el directorio de trabajo. La carpeta `data/` está en `.gitignore`. |
| `USERS_DB_PATH`     | `services/api/data/users.json`                | Fichero TinyDB de usuarios y perfiles (tablas `users` y `profiles`).         |
| `SECRET_KEY`        | — (obligatoria)                               | Clave con la que se firman los JWT.                                          |
| `ALGORITHM`         | — (obligatoria, p. ej. `HS256`)               | Algoritmo de firma JWT.                                                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — (obligatoria, p. ej. `30`)        | Validez del token de acceso.                                                 |
| `CORS_ORIGINS`      | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes permitidos (separados por comas), p. ej. la URL del backoffice.     |

## Estructura

```
services/api/
├── main.py              # Aplicación FastAPI: CORS, routers y lifespan (abre TinyDB y siembra si está vacía)
├── config.py            # Carga .env: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
├── models.py            # Modelos Pydantic: enums, SupplierCreate, Supplier, RateUpdate, StatusUpdate
├── user_models.py       # Modelos de usuarios, perfiles y token (las respuestas nunca incluyen hashed_password)
├── database.py          # Inicialización y acceso a TinyDB (único módulo que toca la base; facilita migrar a Postgres)
├── security.py          # Hash bcrypt (libpass) y firma/validación de JWT (python-jose)
├── user_service.py      # Lógica de usuarios y perfiles: create/get/update/delete_user, authenticate
├── dependencies.py      # get_current_user (Bearer → usuario activo, o 401)
├── routes/
│   ├── auth.py          # /auth/login y /auth/me
│   ├── users.py         # /users
│   ├── profiles.py      # /profiles/me
│   ├── suppliers.py     # Endpoints del directorio de proveedores (/suppliers) — protegidos
│   └── incidents.py     # Endpoints de análisis de incidencias (/api/incidents) — protegidos
├── seed.py              # Carga de datos iniciales (`uv run seed`)
├── seed_data.py         # SUPPLIERS_SEED copiado literalmente del CONTEXT
└── tests/
```

## Modelo de proveedor

| Campo                   | Tipo                                   | Notas                                         |
| ----------------------- | -------------------------------------- | --------------------------------------------- |
| `id`                    | int                                    | `doc_id` de TinyDB. Solo en respuestas.       |
| `name`                  | string, requerido, no vacío            | Único: un alta con nombre repetido da 409.    |
| `country`               | `"Spain"` \| `"USA"`                    |                                               |
| `categories`            | lista, mínimo 1                        | Valores de `VALID_CATEGORIES`.                |
| `monthly_rate`          | float > 0                              |                                               |
| `currency`              | `"EUR"` \| `"USD"`                      | Spain → EUR, USA → USD; otra combinación: 422. |
| `status`                | `"active"` \| `"suspended"`             |                                               |
| `contract_renewal_date` | `YYYY-MM-DD`, opcional                 |                                               |
| `contact_email`         | email, opcional                        |                                               |
| `notes`                 | string, opcional                       |                                               |
| `updated_at`            | datetime UTC ISO 8601                  | Lo genera el sistema al crear y en cada cambio de tarifa. Solo en respuestas. |

El cliente no puede enviar `id` ni `updated_at` (422).

## Autenticación

| Ruta | Acceso | Notas |
| --- | --- | --- |
| `POST /users` | Pública | Alta con `email`, `password` (≥ 8) y opcionalmente `name`, `phone`, `address` (crea el perfil). `role` siempre es `user`; enviarlo da 422. Email repetido: 409. |
| `POST /auth/login` | Pública | Formulario OAuth2: el email va en `username`. Devuelve `{"access_token", "token_type": "bearer"}`. Credenciales inválidas o cuenta inactiva: 401 genérico. |
| `GET /auth/me` | Token | Email, rol y perfil del usuario autenticado. |
| `GET /users`, `GET /users/{id}` | Token | Cualquier usuario autenticado. |
| `PUT /users/{id}` | Token | Solo el propio usuario o un admin (otro: 403). Cambia `email`/`password`; `role` solo un admin. |
| `DELETE /users/{id}` | Token | Solo el propio usuario o un admin (otro: 403). Borra también el perfil. |
| `GET /profiles/me`, `PUT /profiles/me` | Token | Perfil propio (`name`, `phone`, `address`). |
| `/suppliers/...`, `/api/incidents/...` | Token | Todas las rutas. |

Sin token, con token mal formado, expirado o de un usuario inexistente/inactivo: 401 con `WWW-Authenticate: Bearer`.

Roles: `admin`, `manager`, `user`. El registro público solo crea `user`; para tener el primer admin, edita su `role` en `data/users.json` (o desde otro admin con `PUT /users/{id}`).

**En `/docs`:** crea un usuario con `POST /users`, pulsa **Authorize**, escribe el email en `username` y la contraseña, y todas las rutas con candado enviarán el token.

```bash
API=http://localhost:8000
curl -X POST $API/users -H 'Content-Type: application/json' -d '{"email":"ana@nexova.example","password":"secret-123","name":"Ana"}'
TOKEN=$(curl -s -X POST $API/auth/login -d 'username=ana@nexova.example&password=secret-123' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"
curl -H "$AUTH" $API/auth/me
```

## Endpoints de proveedores (ejemplos con curl)

Todos requieren `-H "$AUTH"` (ver arriba); se omite en los ejemplos por brevedad.

```bash
API=http://localhost:8000

# Crear (201). 422 si la entrada es inválida, 409 si el nombre ya existe.
curl -X POST $API/suppliers -H 'Content-Type: application/json' -d '{
  "name": "Personio",
  "country": "Spain",
  "categories": ["payroll_and_hr_software", "ats_software"],
  "monthly_rate": 450,
  "currency": "EUR",
  "status": "active",
  "contract_renewal_date": "2027-01-31",
  "contact_email": "sales@personio.example",
  "notes": "En evaluación"
}'

# Listar todos
curl $API/suppliers

# Filtrar por país, por categoría o ambos (valores inválidos → 422)
curl "$API/suppliers?country=Spain"
curl "$API/suppliers?category=ats_software"
curl "$API/suppliers?country=USA&category=office_and_facilities"

# Obtener uno (404 si no existe)
curl $API/suppliers/1

# Actualizar tarifa (actualiza también updated_at). 404 / 422.
curl -X PATCH $API/suppliers/1/rate -H 'Content-Type: application/json' -d '{"monthly_rate": 1250}'

# Activar / suspender. 404 / 422.
curl -X PATCH $API/suppliers/1/status -H 'Content-Type: application/json' -d '{"status": "suspended"}'

# Eliminar (204, 404 si no existe). Preferible suspender: los suspendidos se conservan como historial.
curl -X DELETE $API/suppliers/1
```

## Endpoints de incidencias

```bash
curl -F "file=@../../scripts/incidents-nexova.csv;type=text/csv" $API/api/incidents/analyze
curl -o results.csv $API/api/incidents/results/export
```

## Backoffice

> ⚠️ El backoffice aún no envía token, así que sus llamadas a `/suppliers` y `/api/incidents` reciben 401 hasta que se implemente el login en el frontend.

El backoffice (`uis/backoffice`) llama a la API a través de un proxy de Next.js (`/api/suppliers` → `/suppliers`, `/api/incidents` → `/api/incidents`). La URL interna se configura con `API_INTERNAL_URL` (por defecto `http://127.0.0.1:8000`). Para llamar a la API directamente desde el navegador, define `NEXT_PUBLIC_API_URL` y añade ese origen del backoffice a `CORS_ORIGINS`.
