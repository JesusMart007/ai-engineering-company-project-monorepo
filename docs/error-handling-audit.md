# Auditoría de gestión de errores

**Rama:** `feature/error-handling-audit` (parte de `feature/incident-manager`) · **Fecha:** 2026-10-11 · **Estado:** Fase 1 (auditoría). Todavía no hay cambios de código.

## 1. Estructura auditada

| Capa | Ruta | Contenido |
| --- | --- | --- |
| Backend | `services/api/` | FastAPI + TinyDB: `main.py`, `config.py`, `database.py`, `security.py`, `email_service.py` (Resend), `user_service.py`, `incident_errors.py`, `seed.py` y `routes/` (`auth`, `users`, `profiles`, `suppliers`, `incidents`, `incident_manager`) |
| Lógica compartida | `packages/shared/python/nexova_shared/` | `csv_validation.py`, `incidents.py` (Python); `packages/shared/types/` (solo tipos TS) |
| Scripts | `scripts/` | `analyze.py` (analizador CSV) y `seed_incidents.py` |
| Scripts | `skills/data-analysis/scripts/` | `pandas_clean.py` (plantilla de la skill) |
| Frontend | `uis/backoffice/` | Next.js App Router: login, registro, reset, perfil, proveedores, análisis CSV y gestor de incidencias. Cliente HTTP en `src/lib/apiClient.ts` |
| Frontend | `uis/talent-pipeline-tracker/` | Next.js App Router con rutas API propias en memoria (`src/app/api/records`) y cliente en `src/services/candidates.ts` |
| Raíz | `src/` | Módulos TS de práctica (`demo.ts`, `utils/`) y `index.html` estático |

**Website público (Hito 1):** no está en este repositorio. El único HTML es `src/index.html`, una página estática de comprobación sin formularios ni JavaScript. No tiene nada que auditar. Si el website vive en otro repositorio o servicio, queda fuera de esta auditoría.

**Canal de soporte disponible:** `contacto@nexova.com` (CONTEXT.md, sección de contacto). Se usará en los estados de error que necesiten una salida de contacto.

## 2. Método

1. Lectura completa de cada módulo Python y TS/TSX listado arriba, con números de línea.
2. Barridos con `git grep` de `print`/`console.*`, patrones de secretos (claves `re_…`/`sk-…`, JWT `eyJ…`, cadenas de conexión), archivos `.env` versionados y `debug=True`.
3. Comprobaciones en vivo, sin tocar el código:
   - `POST /users` con una contraseña corta devuelve **422 con la contraseña en claro** en `detail[].input`.
   - Un error forzado en `GET /suppliers` devuelve **500 `text/plain` "Internal Server Error"**, sin JSON.
   - `analyze.py` con el directorio sin permisos de escritura termina con traceback de `PermissionError` (exit 1).
   - `seed_incidents.py` con una BD corrupta termina con traceback de `JSONDecodeError` (exit 1).

## 3. Resumen

| Capa | Crítico | Alto | Medio | Bajo | Total |
| --- | :-: | :-: | :-: | :-: | :-: |
| Backend (`services/api`, `packages/shared`) | 0 | 2 | 1 | 5 | 8 |
| Scripts (`scripts/`, `services/api/seed.py`, `skills/`) | 0 | 0 | 3 | 2 | 5 |
| Frontend backoffice (`uis/backoffice`) | 0 | 4 | 5 | 5 | 14 |
| Frontend tracker (`uis/talent-pipeline-tracker`) | 0 | 2 | 2 | 4 | 8 |
| Website público | — | — | — | — | 0 (no está en el repo) |
| **Total** | **0** | **8** | **11** | **16** | **35** |

**Sin hallazgos críticos.** No hay secretos, claves ni `.env` en git. Ninguna respuesta incluye tracebacks (FastAPI corre con `debug=False`). El gestor de incidencias ya tiene un 500 genérico con log.

Los fallos de más peso son tres:
- **Respuestas inconsistentes en el backend:** fuera del gestor de incidencias los 500 llegan como texto plano, y los 422 devuelven contraseñas y tokens en `input`.
- **Errores en crudo en el frontend:** se muestran `HTTP 500`, `Unexpected token`, `Failed to fetch` y los textos en inglés del servidor.
- **Sin `error.tsx` ni `not-found.tsx`:** un error de renderizado deja la página en blanco en las dos apps Next.js.

## 4. Hallazgos

Categorías: 1 try/catch ausente · 2 catch demasiado amplio · 3 fallo silencioso · 4 exposición de errores en crudo · 5 filtración de datos sensibles · 6 sin estado de carga/error · 7 sin llamada a la acción · 8 sin `sys.exit` · 9 carga sin `finally` · 10 acceso inseguro a propiedades · 11 llamada externa sin proteger · 12 código HTTP incorrecto.

### ALTO

| ID | Archivo:línea | Cat. | Problema | Corrección sugerida | Estado |
| --- | --- | :-: | --- | --- | --- |
| B1 | `services/api/main.py:51-57` | 12, 4 | No hay handler global de excepciones. Fuera de `/api/incidents` (que usa `IncidentRoute`), un error no controlado responde `500 text/plain "Internal Server Error"`, sin JSON y sin log propio. | Handler `Exception` a nivel de app que reutilice el mensaje y el log de `incident_errors.py`: `{"detail": "Ha ocurrido un error inesperado"}` y traza solo en el log. | Pendiente |
| B2 | `services/api/main.py:51` (handler 422 por defecto de FastAPI) | 5 | El 422 incluye `detail[].input` con el valor enviado. Devuelve **contraseñas** (`/users`, `/auth/change-password`), **tokens de reset** (`/auth/reset-password`) y datos personales en claro, que acaban en devtools, proxies y logs. | Handler de `RequestValidationError` que mantenga el 422 y `detail[]` (`loc`, `msg`, `type`, `ctx`) pero elimine `input`. El mapeo por campo de AUTH-02 no cambia. | Pendiente |
| F1 | `uis/backoffice/src/app/` (no existen `error.tsx`, `global-error.tsx` ni `not-found.tsx`) | 6, 7 | Un error de renderizado deja "Application error: a client-side exception has occurred" (pantalla en blanco). Una URL inexistente muestra el 404 genérico en inglés, sin menú ni salida. | Añadir `error.tsx` (mensaje + Reintentar + Inicio), `global-error.tsx` y `not-found.tsx` en español, con enlace a inicio y contacto. | Pendiente |
| F2 | `uis/backoffice/src/lib/apiClient.ts:124-127` | 1, 4 | `apiJson` hace `await response.json()` sin protección. Un 200 con HTML (proxy o página de error) lanza `SyntaxError: Unexpected token '<'`, que llega a la UI. | try/catch acotado al parseo que lance `ApiError` con un mensaje legible. | Pendiente |
| F3 | `uis/backoffice/src/lib/apiClient.ts:54-57, 67, 73, 111` | 4 | Los mensajes de usuario incluyen `(HTTP 500)`, "¿Está arrancada en el puerto 8000?" y el `detail` en inglés del servidor tal cual ("Supplier 5 not found", "A supplier named 'X' already exists", mensajes de Pydantic). No hay traducción centralizada. | Crear `lib/errors.ts` con `getUserMessage(error)`: sin conexión, timeout, 404, 409 y 5xx con textos fijos. Se conservan los mensajes por campo (400/422) y los ya traducidos de AUTH. | Pendiente |
| F4 | `uis/backoffice/src/app/(protected)/incidents/page.tsx:21, 33` | 4, 7 | Muestra `reason.message` de cualquier `Error` (incluidos `SyntaxError` y `TypeError`). El error no ofrece ninguna acción. | Usar `getUserMessage` y añadir una salida: volver a seleccionar el archivo o contacto. | Pendiente |
| T1 | `uis/talent-pipeline-tracker/src/app/` (no existen `error.tsx` ni `not-found.tsx`) | 6, 7 | Igual que F1: un error de renderizado deja la pantalla en blanco. | Igual que F1, con el estilo de la app. | Pendiente |
| T2 | `uis/talent-pipeline-tracker/src/services/candidates.ts:7-36` (y re-envoltorios en 57-243) | 1, 4 | `fetch` sin try (llega "Failed to fetch"), `Error HTTP ${status}: ${statusText}` y `response.json()` sin proteger. Además se encadenan prefijos ("Error al crear la nota: Error HTTP 500: Internal Server Error"). Las páginas lo muestran con `err.message`. | `fetchJson` con try acotado al `fetch` y al parseo, un `ApiError` con status y `getUserMessage` en las páginas y formularios. | Pendiente |

### MEDIO

| ID | Archivo:línea | Cat. | Problema | Corrección sugerida | Estado |
| --- | --- | :-: | --- | --- | --- |
| B4 | `services/api/email_service.py:21-31` | 11, 2 | Llama a Resend con el timeout implícito del SDK (30 s) y un `except Exception` genérico. No distingue el fallo de Resend (clave inválida, 4xx/5xx) del fallo de red. | Timeout explícito (10 s) mediante el cliente HTTP del SDK. Capturar primero `resend.exceptions.ResendError` y los errores de red, y dejar `Exception` como último recurso con log. Forgot-password sigue respondiendo 200. | Pendiente |
| S1 | `scripts/analyze.py:86-96` | 1, 8 | La exportación a `results.csv` no tiene try: un `PermissionError` u `OSError` termina con traceback (exit 1). | Capturar `OSError`, mostrar un mensaje en stderr y terminar con `exit 1`. | Pendiente |
| S2 | `scripts/seed_incidents.py:91-97` | 1, 8 | Abrir o escribir la BD TinyDB no tiene try: una BD corrupta (`JSONDecodeError`) o sin permisos termina con traceback. | Capturar `json.JSONDecodeError` y `OSError`, mostrar un mensaje en stderr (sin el contenido) y terminar con `sys.exit(1)`. | Pendiente |
| S3 | `services/api/seed.py:27-38` (`uv run seed`) | 1, 8 | No tiene ningún manejo de errores: `main()` no devuelve código y cualquier fallo de la BD sale como traceback. | Mismo patrón que S2 y `raise SystemExit(main())`. | Pendiente |
| F5 | `uis/backoffice/src/components/SupplierForm.tsx:71`, `SupplierRow.tsx:27`, `app/(protected)/suppliers/page.tsx:36`, `account/profile/page.tsx:10`, `account/change-password/page.tsx:34`, `(public)/reset-password/page.tsx:34`, `(auth)/login/page.tsx:26`, `(auth)/register/page.tsx:35` | 4 | Muestran `reason.messages` en crudo (ver F3). | `getUserMessage(reason)`, conservando los errores por campo. | Pendiente |
| F6 | `uis/backoffice/src/app/(protected)/suppliers/page.tsx:95, 125-127` | 7 | El error de carga no tiene botón Reintentar y además aparece a la vez la fila "No hay proveedores que coincidan con los filtros" (mensaje engañoso). | Añadir botón Reintentar y no mostrar el estado vacío cuando hay error. | Pendiente |
| F7 | `uis/backoffice/src/app/(protected)/account/profile/page.tsx:21-23, 50` | 7 | Si `getMe()` falla, solo aparece el mensaje: no hay forma de reintentar ni salida. | Botón Reintentar y enlace a inicio. | Pendiente |
| F8 | `uis/backoffice/src/app/(public)/forgot-password/page.tsx:16-20` | 3 | `catch {}` vacío: con la API caída o un 5xx se le dice al usuario "recibirás un enlace en breve". | Mostrar el error solo en los fallos de red, timeout o 5xx. La API responde siempre 200 para cualquier email, así que esto no revela si existe y la anti-enumeración se mantiene. | Pendiente |
| F9 | `uis/backoffice/src/lib/apiClient.ts:98-121` | 1 | No hay timeout por defecto (solo lo tienen las llamadas del gestor de incidencias). Si la API se cuelga, proveedores, perfil, login y análisis se quedan cargando indefinidamente. | Timeout por defecto en `apiFetch` (15 s) cuando no se pase `signal`, con su propio mensaje. | Pendiente |
| T3 | `uis/talent-pipeline-tracker/src/components/ErrorState.tsx:1-51` | 7 | La única salida es Reintentar, que no sirve en un 404 (candidato inexistente). No hay enlace a inicio ni contacto. | Añadir enlace a inicio y contacto de soporte. | Pendiente |
| T4 | `uis/talent-pipeline-tracker/src/services/candidates.ts:7-14` | 1 | El `fetch` no tiene timeout. | `AbortSignal.timeout(15000)` y un mensaje de timeout. | Pendiente |

### BAJO

| ID | Archivo:línea | Cat. | Problema | Corrección sugerida | Estado |
| --- | --- | :-: | --- | --- | --- |
| B3 | `packages/shared/python/nexova_shared/csv_validation.py:200` | 4 | `CsvFormatError` incluye el texto interno de `csv.Error`, que llega como 422 al análisis CSV. | Mensaje fijo; el detalle va solo al log. Los mensajes de `analyze.py` siguen siendo informativos. | Pendiente |
| B7 | `services/api/database.py:52, 144, 234` y `main.py:36-42` | 1 | Un fichero TinyDB corrupto rompe el arranque (o cada lectura) con `JSONDecodeError` sin decir qué fichero es. | Comprobar al abrir: `RuntimeError` claro con el nombre del fichero y la causa, y el detalle en el log. | Pendiente |
| B8 | `services/api/security.py:31-32` | 1 | `bcrypt.verify` lanza `ValueError` si el hash guardado está dañado, y el login responde 500. | Capturar `ValueError` → `False` + warning en el log (sin el hash). | Pendiente |
| B9 | `services/api/config.py:27, 34` | 1 | `int()` sobre `ACCESS_TOKEN_EXPIRE_MINUTES` y `RESET_TOKEN_EXPIRE_MINUTES` lanza un `ValueError` que no dice qué variable falla. | Error claro con el nombre de la variable. | Pendiente |
| B10 | `services/api/main.py` | — | El logging no está configurado: `logger.exception` depende del handler de último recurso de Python (sin nivel ni formato). | `logging.basicConfig` con nivel configurable (`LOG_LEVEL`). | Pendiente |
| S5 | `scripts/analyze.py:86-90`, `scripts/seed_incidents.py:75-101` | 8 | Ctrl+C termina con traceback. | Capturar `KeyboardInterrupt` → exit 130 y un mensaje breve. | Pendiente |
| S6 | `skills/data-analysis/scripts/pandas_clean.py:8-30` | 1, 5, 8 | Plantilla de la skill: `read_csv` sin try ni `sys.exit`, e imprime `df.head()` (puede mostrar datos personales). | No aplica: es una plantilla de ejemplo para copiar, no un script del proyecto. Se propone dejarla como está (ver §6). | Propuesto: no aplica |
| F10 | `uis/backoffice/src/lib/authApi.ts:24-31` | 10 | `access_token` no se valida: si faltara, se guardaría `"undefined"` como token. | Comprobar que sea un `string` no vacío; si no, lanzar `ApiError`. | Pendiente |
| F11 | `uis/backoffice/src/components/IncidentSummary.tsx:60, 91` | 10 | `result.labels.rules[...]` y `result.labels.scores[...]` sin `?.`. | Optional chaining y fallback "—". | Pendiente |
| F12 | `uis/backoffice/src/app/(auth)/login/page.tsx:22-28`, `(auth)/register/page.tsx:30-45` | 9 | `setSubmitting(false)` se repite en cada rama en vez de ir en `finally`. | `finally` que lo reinicie salvo cuando se está navegando tras el éxito. | Pendiente |
| F13 | `uis/backoffice/src/lib/auth.ts:24-27` | 1 | `localStorage.setItem` sin try: con el almacenamiento bloqueado, el login muestra "Error inesperado". | try/catch con un mensaje claro ("Tu navegador bloquea el almacenamiento…"). | Pendiente |
| F14 | `uis/backoffice/src/lib/incidentsApi.ts:32-40` | 1 | `response.blob()` en la descarga del CSV no está protegido. | Envolverlo y lanzar `ApiError`. | Pendiente |
| T5 | `uis/talent-pipeline-tracker/src/app/api/records/route.ts:9-36` | 12 | `POST /api/records` sin `name`, `email` ni `position` responde 201 con valores por defecto. | 400 con `{ error, errors: [...] }` cuando falten campos obligatorios. | Pendiente |
| T6 | `uis/talent-pipeline-tracker/src/app/api/records/[id]/notes/[note_id]/route.ts:19-25` | 12 | `DELETE` de una nota inexistente responde 204. | 404 si la nota no existe. | Pendiente |
| T7 | `uis/talent-pipeline-tracker/src/app/api/records/route.ts:31`, `[id]/route.ts:41`, `[id]/notes/route.ts:55` | 2, 3 | `catch (error)` trata cualquier fallo como 400 "petición inválida" y no deja log. | Acotar el catch al `request.json()` (400) y dejar que el resto vaya a un 500 con log. | Pendiente |
| T8 | `uis/talent-pipeline-tracker/src/app/candidates/[id]/page.tsx:157` | 4 | `handleAddNote` muestra el error y además lo relanza: aparece dos veces (banner y formulario). | Mostrarlo en un solo sitio. | Pendiente |

## 5. Comprobado sin hallazgos

- **Secretos:** no hay claves, JWT ni cadenas de conexión en el código, ni `.env` versionados (solo `.env.example`). `RESEND_API_KEY` y `SECRET_KEY` se leen del entorno y no se registran.
- **Debug:** `FastAPI()` corre con `debug=False`. `--reload` solo aparece en la documentación de desarrollo.
- **Logs:**
  - `email_service.py` registra solo el asunto, nunca el destinatario ni el enlace.
  - `routes/auth.py:49` registra el fallo de reset sin el email.
  - `seed_incidents.py` y `analyze.py` nunca imprimen emails (cubierto por tests).
  - Los `print` de los scripts son la salida del CLI.
  - Los `console.log` de `src/demo.ts` imprimen datos de ejemplo.
- **Anti-enumeración de AUTH-03:** `/auth/forgot-password` responde siempre 200 y el envío va en segundo plano, con el fallo en el log.
- **AUTH-02:** un 401 en una llamada protegida borra el token y redirige a `/login` (`apiClient.ts:114-118`).
- **Gestor de incidencias:** errores 400 con `{detail, errors}`, 500 genérico con log, timeout de 15 s y estados de carga, error y vacío con Reintentar.
- **Scripts:**
  - Archivo inexistente, vacío, no UTF-8 o con cabeceras incorrectas: mensaje en stderr y exit 1 (`analyze.py:100-117`, `seed_incidents.py:75-88`).
  - Las filas inválidas se reportan y el proceso continúa.
  - Ningún script requiere variables de entorno obligatorias (`INCIDENTS_DB_PATH` y `SUPPLIERS_DB_PATH` tienen valor por defecto).
- **Tracker:** las vistas de listado y detalle ya tienen carga, error con Reintentar y `finally`. `candidateUtils.ts` usa fallbacks para los campos opcionales.

## 6. Decisiones que necesitan aprobación

1. **B2:** quitar `input` del 422 global mantiene el formato que usa AUTH-02 (`loc`, `msg`, `type`, `ctx`). Es el único cambio de formato de error del backend fuera del gestor de incidencias.
2. **S6:** propongo no modificar la plantilla `skills/data-analysis/scripts/pandas_clean.py`.
3. **Website del Hito 1:** no está en el repo. Si existe en otra ubicación, indícala; si no, queda como "no aplica".
