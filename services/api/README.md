# Nexova API (`services/api`)

Backend FastAPI centralizado de Nexova. Expone estos dominios:

- **Directorio de proveedores** (`/suppliers`): registro oficial de proveedores, persistido en TinyDB. Especificación en [`09-lightweight-storage/CONTEXT-nexova.md`](../../09-lightweight-storage/CONTEXT-nexova.md).
- **Análisis de incidencias** (`/api/incidents/analyze`, `/api/incidents/results/export`): procesa el CSV del helpdesk con la misma lógica que `scripts/analyze.py`.
- **Gestor de incidencias** (`/api/incidents`, `/api/incidents/{id}`, `/api/incidents/summary`): registro centralizado de incidencias en TinyDB. Especificación en [`CONTEXT-nexova-incident-manager.es.md`](../../CONTEXT-nexova-incident-manager.es.md).
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

### Incidencias históricas

Las incidencias **no** se siembran solas. Se cargan desde el CSV del analizador con el script del monorepo (desde la raíz del repo):

```bash
uv run --project services/api python scripts/seed_incidents.py
# Insertadas 96 · Ya existentes (saltadas) 0 · Inválidas 4 (filas 18, 44, 87 y 91)
```

Es idempotente (una segunda ejecución inserta 0 y salta 96). Detalles en [`scripts/README.es.md`](../../scripts/README.es.md).

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

Los tests usan bases TinyDB temporales (`tmp_path`) vía `SUPPLIERS_DB_PATH`, `USERS_DB_PATH` e `INCIDENTS_DB_PATH`, nunca los ficheros reales, y fijan su propio `SECRET_KEY` (no leen tu `.env`).

## Variables de entorno

| Variable            | Por defecto                                   | Descripción                                                                 |
| ------------------- | --------------------------------------------- | --------------------------------------------------------------------------- |
| `SUPPLIERS_DB_PATH` | `services/api/data/suppliers.json`            | Fichero JSON de TinyDB. Una ruta relativa se resuelve desde el directorio de trabajo. La carpeta `data/` está en `.gitignore`. |
| `USERS_DB_PATH`     | `services/api/data/users.json`                | Fichero TinyDB de usuarios y perfiles (tablas `users` y `profiles`).         |
| `INCIDENTS_DB_PATH` | `services/api/data/incidents.json`            | Fichero TinyDB del gestor de incidencias (tabla `incidents`). Lo usan la API y `scripts/seed_incidents.py`. |
| `SECRET_KEY`        | — (obligatoria)                               | Clave con la que se firman los JWT.                                          |
| `ALGORITHM`         | — (obligatoria, p. ej. `HS256`)               | Algoritmo de firma JWT.                                                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — (obligatoria, p. ej. `30`)        | Validez del token de acceso.                                                 |
| `CORS_ORIGINS`      | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes permitidos (separados por comas), p. ej. la URL del backoffice.     |
| `RESEND_API_KEY`    | — (vacía: los emails no se envían y se registra el error) | Clave de [Resend](https://resend.com/api-keys) para el email de restablecimiento. Solo en `.env`. |
| `EMAIL_FROM`        | `onboarding@resend.dev`                       | Remitente. Con `onboarding@resend.dev`, Resend solo entrega al email de tu cuenta de Resend; para otros destinatarios hay que verificar un dominio. |
| `FRONTEND_URL`      | `http://localhost:3000`                       | URL del backoffice; el enlace del email es `{FRONTEND_URL}/reset-password?token=…`. En Codespaces, la URL pública del puerto 3000. |
| `RESET_TOKEN_EXPIRE_MINUTES` | `30`                                 | Validez del enlace de restablecimiento.                                      |

## Estructura

```
services/api/
├── main.py              # Aplicación FastAPI: CORS, routers y lifespan (abre TinyDB y siembra si está vacía)
├── config.py            # Carga .env: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
├── models.py            # Modelos Pydantic: enums, SupplierCreate, Supplier, RateUpdate, StatusUpdate
├── incident_models.py   # Modelos del gestor de incidencias (enums en packages/shared: nexova_shared.incidents)
├── incident_errors.py   # IncidentRoute: 400 con errores por campo y 500 genérico, solo en el gestor de incidencias
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
│   ├── incidents.py     # Análisis del CSV (/api/incidents/analyze, /results/export) — protegidos
│   └── incident_manager.py  # Gestor de incidencias (/api/incidents, /summary, /{id}, /{id}/status) — protegidos
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
| `POST /auth/forgot-password` | Pública | `{"email"}`. Siempre 200 con el mismo mensaje, exista o no el email. Si existe y está activo, envía el enlace de restablecimiento por email (en segundo plano). |
| `POST /auth/reset-password` | Pública | `{"token", "new_password"}`. Enlace inválido, caducado o ya usado: 400. Contraseña con las reglas del registro (422). |
| `POST /auth/change-password` | Token | `{"current_password", "new_password"}`. Contraseña actual incorrecta: 400. |
| `/suppliers/...`, `/api/incidents/...` | Token | Todas las rutas. |

Sin token, con token mal formado, expirado, de un usuario inexistente/inactivo o que no sea de sesión (`type` distinto de `"access"`): 401 con `WWW-Authenticate: Bearer`.

### Recuperación y cambio de contraseña

- **Tokens con tipo.** Los de sesión llevan `type: "access"` y los de restablecimiento `type: "password_reset"`; cada uno solo vale para lo suyo, así que un enlace de reset nunca sirve como token de sesión. Los tokens de sesión anteriores a este cambio (sin `type`) dejan de valer: basta con volver a iniciar sesión.
- **Un solo uso.** El token de reset es un JWT con `sub`, `exp`, `jti` (uuid4) y `type`. Su estado vive en la tabla TinyDB `password_reset_tokens` (`jti`, `user_id`, `expires_at`, `used_at`) del mismo fichero que `users`. Al usarlo se marca `used_at` (comprobación y marca en un único paso).
- **Invalidación.** Pedir un enlace nuevo invalida los pendientes del usuario, y cualquier cambio de contraseña (reset o change) también.
- **Sin filtrar si el email existe.** `forgot-password` responde siempre igual y busca al usuario, crea el token y envía el email con `BackgroundTasks`, después de responder. Si Resend falla, solo se registra en los logs.
- **Email** (`email_service.py`): HTML de una columna con estilos inline y botón grande, más versión en texto plano con la URL completa; indica cuándo caduca y que puede ignorarse si no se pidió.

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

## Endpoints de análisis del CSV

```bash
curl -F "file=@../../scripts/incidents-nexova.csv;type=text/csv" $API/api/incidents/analyze
curl -o results.csv $API/api/incidents/results/export
```

## Gestor de incidencias

### Modelo `Incident`

| Campo         | Tipo                                                     | Notas |
| ------------- | -------------------------------------------------------- | ----- |
| `id`          | int                                                      | `doc_id` de TinyDB. Solo en respuestas. |
| `title`       | string, obligatorio, 1–120 caracteres                    | Se recortan los espacios. |
| `description` | string, obligatorio                                      | |
| `category`    | `technical_failure` \| `process_error` \| `client_complaint` \| `candidate_issue` \| `staff_issue` \| `sla_breach` \| `data_quality` \| `other` | |
| `status`      | `open` \| `in_progress` \| `resolved` \| `discarded`     | Siempre `open` al crear; luego solo cambia con `PATCH /{id}/status`. |
| `origin`      | `customer` \| `branch` \| `internal`                     | |
| `branch`      | `central` \| `valencia_operations` \| `miami_office` \| `remote` | Siempre obligatorio; `central` si no corresponde a una oficina. |
| `source_id`   | string \| null, único                                    | `ticket_id` del CSV; solo para la idempotencia del seed. `null` en las creadas por la API. |
| `created_at`, `updated_at` | datetime UTC                                | Automáticos; `updated_at` cambia en cada modificación. |
| `next_statuses` | lista                                                  | Calculado: estados a los que puede pasar (vacío en los finales). Solo en respuestas. |

Los valores permitidos y las transiciones se definen una sola vez en `packages/shared` (`nexova_shared.incidents`). TinyDB no admite restricciones (NOT NULL, CHECK), así que la integridad se garantiza en los modelos (`IncidentRecord` valida cada documento antes de escribirlo) y en `IncidentRepository` (unicidad de `source_id` y transiciones comprobadas bajo un lock).

Transiciones: `open → in_progress | discarded`, `in_progress → resolved | discarded`; `resolved` y `discarded` son finales.

### Endpoints

| Ruta | Respuesta |
| --- | --- |
| `POST /api/incidents` | 201 con la incidencia. Campo obligatorio vacío o valor no permitido: 400. |
| `GET /api/incidents?status=&origin=&branch=&category=` | Lista (más recientes primero), filtros opcionales combinables. `[]` si no hay datos. |
| `GET /api/incidents/summary` | `{total, by_status, by_category, by_origin, by_branch}` con **todos** los valores permitidos, aunque estén a 0. |
| `GET /api/incidents/{id}` | Detalle, o 404 `{"detail": "No existe ninguna incidencia con id 7"}`. |
| `PATCH /api/incidents/{id}/status` | Body `{"status"}`. Solo cambia `status` y `updated_at`. Transición no permitida: 400 explicándola. Id inexistente: 404. |

### Errores

Solo en estas rutas (`route_class=IncidentRoute`), los errores de validación son **400** en vez del 422 de FastAPI, con un mensaje claro por campo:

```json
{"detail": "Datos no válidos", "errors": [{"field": "title", "message": "El título es obligatorio"}]}
```

Las excepciones no controladas devuelven `500 {"detail": "Ha ocurrido un error inesperado"}` sin stack trace; el error completo se registra en los logs del servidor (logger `incident_errors`). El resto de rutas (`/users`, `/auth`, `/suppliers`, `/api/incidents/analyze`) mantienen el formato 422 de FastAPI, del que depende el formulario de registro del backoffice.

```bash
curl -X POST $API/api/incidents -H "$AUTH" -H 'Content-Type: application/json' -d '{
  "title": "Zendesk no carga los tickets",
  "description": "El panel devuelve 503 a todo el equipo de soporte.",
  "category": "technical_failure",
  "origin": "branch",
  "branch": "miami_office"
}'
curl -H "$AUTH" "$API/api/incidents?status=open&branch=central"
curl -H "$AUTH" $API/api/incidents/summary
curl -X PATCH $API/api/incidents/1/status -H "$AUTH" -H 'Content-Type: application/json' -d '{"status": "in_progress"}'
```

## Backoffice

El backoffice (`uis/backoffice`) llama a la API a través de un proxy de Next.js: cada ruta de la API vive bajo `/api` para no chocar con las páginas (`/api/suppliers` → `/suppliers`, `/api/incidents` → `/api/incidents`, `/api/auth` → `/auth`, `/api/users` → `/users`, `/api/profiles` → `/profiles`). La URL interna se configura con `API_INTERNAL_URL` (por defecto `http://127.0.0.1:8000`). Para llamar a la API directamente desde el navegador, define `NEXT_PUBLIC_API_URL` y añade ese origen del backoffice a `CORS_ORIGINS`.

### Sesión en el backoffice

- `/login` y `/register` son públicas (con sesión redirigen a `/`); `/forgot-password` y `/reset-password` son públicas sin redirección (el enlace del email funciona aunque haya sesión); el resto (`/`, `/incidents`, `/suppliers`, `/account/profile`, `/account/change-password`) exige sesión.
- Al iniciar sesión, el token de `POST /auth/login` se guarda en `localStorage` (`nexova.accessToken`) y cada llamada protegida lo envía como `Authorization: Bearer <token>` (`src/lib/apiClient.ts`).
- La protección es en el cliente (`src/components/AuthGuard.tsx`): sin token, o con el `exp` vencido, redirige a `/login`. La firma la valida la API; cualquier 401 borra el token y lleva a `/login`.
- "Cerrar sesión" (barra superior) borra el token. No hay cookies ni middleware de Next.js.

```bash
cd uis/backoffice
npm install
npm run dev     # http://localhost:3000 → /login; crea una cuenta en /register
npm run lint
npm run build
```
