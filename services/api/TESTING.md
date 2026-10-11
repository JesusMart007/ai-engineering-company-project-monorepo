# TESTING — AUTH-088: batería de pruebas de la API de autenticación

> Estado: **PLAN (Fase 1). Todavía sin resultados.** Pendiente de aprobación.

## 0. Punto de partida (reconocimiento)

| Aspecto | Hallazgo |
|---|---|
| Raíz FastAPI | `services/api/` (`pyproject.toml`, `uv.lock`). Módulos planos, sin paquete: `security.py`, `dependencies.py`, `user_service.py`, `database.py` (`UserRepository`), `user_models.py`, `email_service.py`, `config.py`, `routes/{auth,users,profiles}.py`. |
| Raíz frontend | `uis/backoffice/` (Next.js, **npm**, alias `@/*` → `src/*`). Utilidades: `src/lib/{auth,apiClient,authApi,errors}.ts`. |
| Tests existentes | `services/api/tests/` ya tiene **174 tests en verde** (`uv run pytest`), casi todos vía `TestClient`: `test_auth.py`, `test_users.py`, `test_profiles.py`, `test_password_reset.py`, `test_robustness.py`… |
| pytest | Ya configurado (`testpaths = ["tests"]`); `pytest` y `httpx` ya están en el grupo `dev`. **Falta `pytest-cov`** (`--cov` hoy da error). |
| Jest | No hay nada en el frontend (sin jest, sin script `test`). |
| BD | `UserRepository(path)` sobre TinyDB; la ruta sale de `USERS_DB_PATH` (leída en el `lifespan` de `main.py`). |
| Config | `config.py` lee `.env` con `load_dotenv` y fija `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `RESET_TOKEN_EXPIRE_MINUTES`… como **constantes de módulo en el import**. |
| Resend | `email_service._send` llama a `resend.Emails.send`; sin `RESEND_API_KEY` no envía nada. |
| Rol admin | **No existe ningún camino en la API ni en el seed para crear un admin**; solo se puede tocar la BD. Los tests lo crearán directamente en el repositorio. |

### Qué cambia respecto a lo que pide el ticket (para que lo valides)

1. **Ya existe una suite HTTP amplia.** No la reescribo ni la duplico: la mantengo como red de seguridad y añado una **capa de pruebas unitarias** (servicios, funciones de token, `get_current_user`, repositorio) con los módulos que indicas. Cuando un caso ya esté cubierto por un test HTTP existente, el nuevo test unitario afirma la *decisión* (excepción, efecto en BD) y no la repite por HTTP. Si algún archivo existente solapa con uno nuevo (`test_password_reset.py`), propongo **mover/ampliar**, no tener dos.
2. **Las variables de entorno no se pueden cambiar con `monkeypatch.setenv`**: `security.py` ya importó `SECRET_KEY`/`ACCESS_TOKEN_EXPIRE_MINUTES`/`RESET_TOKEN_EXPIRE_MINUTES` como constantes. La fixture hará `monkeypatch.setattr(security, "SECRET_KEY", …)` (y `user_service.RESET_TOKEN_EXPIRE_MINUTES`). El `conftest.py` actual ya fija el entorno antes de importar; lo conservo.
3. **Tiempo**: `security.py` usa `datetime.now(UTC)` y `jose` valida `exp` con el reloj real. Para "pasado ese tiempo se rechaza" usaré `freezegun` (única dependencia opcional que sí necesito) o, alternativamente, tokens creados con `expires_delta` negativo. Propongo `freezegun`.
4. Los tests de coste: se mantiene `bcrypt.using(rounds=4)` del conftest actual.

## 1. Estrategia

**Se prueba (lógica de negocio):**
- Servicios: `create_user`, `authenticate`, `update_user`, `delete_user`, `update_profile`, `request_password_reset`, `reset_password`, `change_password`.
- Seguridad: `hash_password`/`verify_password`, `create/decode_access_token`, `create/decode_reset_token` (claims `sub`, `exp`, `type`, `jti`).
- Dependencia `get_current_user` llamada **directamente** con un token y un repositorio.
- Repositorio: unicidad de email, borrado atómico User+Profile, consumo de token de reset de un solo uso.
- Reglas de permisos de las rutas (`_require_self_or_admin`, cambio de role solo admin) y qué dependencias protegen cada endpoint, vía `TestClient` **solo** donde la decisión vive en la ruta.

**No se prueba:**
- Forma/serialización JSON de las respuestas, nombres de campos de `response_model`, cabeceras, OpenAPI.
- Internos de FastAPI/Pydantic (que `EmailStr` valide formatos, que `extra="forbid"` rechace campos: solo compruebo que *nuestro* contrato lo usa donde importa, p. ej. registro con `role`).
- bcrypt/python-jose en sí; el envío real a Resend (siempre mockeado).
- Plantilla HTML del email (ya cubierta por un test existente).

**Convenciones:** Arrange/Act/Assert, nombres `test_<unidad>_<comportamiento>`, BD TinyDB en `tmp_path` por test, Resend mockeado en un fixture `autouse`, cero `sleep`.

## 2. Plan por endpoint

Leyenda: 🟢 camino feliz · 🟡 caso límite · 🔴 modo de fallo · ✅ ya cubierto por un test existente (se reexpresa a nivel unitario o se deja como está) · 🤖 sugerido por la IA (ver §3).

### 2.1 `POST /users` — registro (`test_register.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| R1 | 🟢 | Usuario válido: se crea con `role=user`, `is_active=True`, `id` uuid | Es la única puerta de entrada de cuentas; el role por defecto es el límite de privilegios. |
| R2 | 🟢 | La contraseña guardada es un hash bcrypt ≠ texto plano y `verify_password` lo valida | Una fuga de la BD no debe exponer contraseñas. |
| R3 | 🟢 | Se crea el `Profile` con `name/phone/address` opcionales (con y sin ellos) | El registro es transaccional User+Profile. |
| R4 | 🔴 | Email duplicado → `EmailAlreadyRegistered` (409 en la ruta); no se crea un segundo usuario ni perfil | Evita cuentas duplicadas / secuestro de email. |
| R5 | 🟡 | Mismo email con otras mayúsculas (`A@B.com`) → duplicado | Si no, existirían dos cuentas "iguales". |
| R6 | 🟡 | Email con espacios alrededor (`" a@b.com "`) → se normaliza y se trata como duplicado | Probado: Pydantic lo recorta; falta fijarlo en un test. |
| R7 | 🔴 | Contraseña vacía → rechazada | Cuenta sin contraseña real. |
| R8 | 🔴 | Contraseña solo espacios (8 espacios) → **debe** rechazarse | ⚠ Ver riesgo B1: hoy se acepta. |
| R9 | 🔴 | Intento de registrarse con `role: "admin"` → 422, no se crea usuario | Escalada de privilegios en el endpoint público. |
| R10 | 🔴 | Email inválido (`no-es-email`, sin dominio) → 422, nada se escribe | Integridad de datos. |
| R11 | 🟡 | Contraseña de exactamente 8 caracteres y de 72 bytes OK; 73 bytes rechazada; 8 caracteres multibyte | Límite de bcrypt (truncado silencioso a 72 bytes). |

### 2.2 `POST /auth/login` (`test_login.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| L1 | 🟢 | Credenciales correctas → token con `sub` = id, `type=access`, `exp` = ahora + `ACCESS_TOKEN_EXPIRE_MINUTES` (con tiempo congelado) | Contrato central del ticket. |
| L2 | 🔴 | Contraseña incorrecta → `authenticate` devuelve `None` / 401 genérico | Control de acceso básico. |
| L3 | 🔴 | Email inexistente → misma respuesta y mismo `detail` que L2 | Sin enumeración de cuentas. |
| L4 | 🔴 | Usuario inactivo con contraseña correcta → rechazado con el mismo error | Desactivar cuenta debe cortar el acceso. |
| L5 | 🔴 | Contraseña vacía → rechazada (422 de formulario o 401), nunca token | Evita login sin contraseña. |
| L6 | 🟡 | Email en otras mayúsculas inicia sesión (✅ existe) | Coherente con el registro. |
| L7 | 🟡 | Email con espacios (`" a@b.com "`) | ⚠ Riesgo B3: el registro lo recorta pero el login no. |
| L8 | 🟡 | Contraseña de >72 bytes → falla sin excepción (✅ parcial) | No debe dar 500. |
| L9 | 🔴 | Hash almacenado corrupto → 401, no 500 (✅ existe) | Robustez. |

### 2.3 Tokens y `get_current_user` (`test_token.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| T1 | 🟢 | Token válido → `get_current_user` devuelve el usuario correcto | Base de toda la autorización. |
| T2 | 🟢 | `create_access_token`: `exp` = ahora + `ACCESS_TOKEN_EXPIRE_MINUTES`; `expires_delta` explícito lo sustituye | Regresión del ticket. |
| T3 | 🔴 | Pasado `ACCESS_TOKEN_EXPIRE_MINUTES` (tiempo avanzado 1 min) → `InvalidToken` / 401; un segundo antes aún vale | Frontera exacta de expiración. |
| T4 | 🔴 | Firmado con otra clave → rechazado | Falsificación. |
| T5 | 🔴 | Token malformado (`abc`, `a.b.c`, vacío, `None`) → 401 `Not authenticated`/`Invalid…` | Entradas hostiles. |
| T6 | 🔴 | Token válido sin `sub` / `sub` vacío / `sub` no string → rechazado | Identidad ausente. |
| T7 | 🔴 | Token de un usuario eliminado → 401 | Revocación implícita al borrar. |
| T8 | 🔴 | Token de reset usado como sesión → 401; y al revés (token de sesión en `decode_reset_token`) | Separación de tipos de token. |
| T9 | 🔴 | Algoritmo `none` (sin firma) y token HS512 firmado con la clave correcta → rechazados | Ataque clásico de JWT. |
| T10 | 🔴 | Usuario inactivo con token aún vigente → 401 (✅ existe) | Desactivar debe ser inmediato. |
| T11 | 🔴 | Token **sin `exp`** firmado con la clave correcta → debe rechazarse | ⚠ Riesgo B2: hoy se acepta. |
| T12 | 🟡 | Token sin claim `type` → rechazado (✅ existe) | Tokens heredados/antiguos. |
| T13 | 🟡 | `hash_password` produce hashes distintos para la misma contraseña (sal); `verify_password` con cadena vacía / hash inválido → `False` | Propiedades del hashing. |
| T14 | 🔴 | Sin cabecera `Authorization` → 401 con `WWW-Authenticate: Bearer` | Contrato de la dependencia. |

### 2.4 `GET /auth/me` y `/profiles/me` (`test_auth_me.py`, `test_profiles.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| M1 | 🟢 | `/auth/me` devuelve email, role y perfil del **usuario del token** (dos usuarios, cada uno ve lo suyo) | Evita mostrar datos ajenos. |
| M2 | 🟡 | Usuario sin Profile → `profile` nulo en `/auth/me`; `/profiles/me` GET → 404 | Dato faltante no rompe. |
| M3 | 🔴 | Sin token / token inválido → 401 en ambos | Protección de ruta. |
| P1 | 🟢 | `update_profile` cambia solo los campos enviados (`exclude_unset`) | Una actualización parcial no borra el resto. |
| P2 | 🟡 | Enviar `name: null` explícito lo borra; enviar `{}` no cambia nada | Diferencia entre "no enviado" y "nulo". |
| P3 | 🟡 | `update_profile` sin perfil previo lo crea; llamadas repetidas mantienen un único perfil (✅) | Sin duplicados. |
| P4 | 🔴 | Un usuario no puede modificar el perfil de otro: no existe `/profiles/{id}` y body con `user_id`/`id` → 422 (✅) | Propiedad del perfil. |
| P5 | 🔴 | Campo de más de 200 caracteres → rechazado | Límite de tamaño. |

### 2.5 `/users` — gestión (`test_users.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| U1 | 🟢 | Usuario actualiza su propio email y contraseña (nuevo hash, el viejo ya no sirve) | Autoservicio. |
| U2 | 🟢 | Admin actualiza/borra a otro usuario | Capacidad administrativa. |
| U3 | 🔴 | Usuario B hace `PUT`/`DELETE` sobre A → 403 y A queda intacto | Autorización horizontal (IDOR). |
| U4 | 🔴 | Un `user`/`manager` envía `role` sobre sí mismo → 403, role sin cambios | Autoescalada de privilegios. |
| U5 | 🟢 | Admin cambia el role de otro | Único camino legítimo. |
| U6 | 🔴 | Role fuera de `admin/manager/user` → 422 | Valores inválidos en BD. |
| U7 | 🟢 | `DELETE` elimina User **y** Profile (comprobado en BD) | Sin datos huérfanos. |
| U8 | 🔴 | `DELETE`/`GET` de id inexistente: admin → 404; no-admin sobre id ajeno → 403 (no revela existencia) | Sin enumeración por id. |
| U9 | 🔴 | Cambiar el email a uno ya en uso → `EmailAlreadyRegistered` / 409; el propio email actual no cuenta como duplicado | Unicidad en actualización. |
| U10 | 🟡 | `PUT {}` no cambia nada y devuelve el usuario | Caso vacío. |
| U11 | 🔴 | Todas las rutas `/users` salvo `POST` exigen token (✅) | Protección por dependencia. |
| U12 | 🟡 | Las respuestas nunca incluyen `hashed_password` (✅, solo se afirma la ausencia del hash) | Fuga de credenciales. |

### 2.6 `POST /auth/forgot-password` (`test_password_reset.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| F1 | 🟢 | Email registrado → se guarda un token (jti, `expires_at` = ahora + `RESET_TOKEN_EXPIRE_MINUTES`) y Resend mock recibe 1 envío con enlace `FRONTEND_URL/reset-password?token=…` | Flujo principal. |
| F2 | 🔴 | Email no registrado → misma respuesta, **0 tokens, 0 envíos** | Sin enumeración. |
| F3 | 🔴 | Resend falla (`ResendError`, sin API key, `ValueError`) → la respuesta no cambia y no se propaga la excepción (✅ parcial) | Un fallo del proveedor no debe filtrar información. |
| F4 | 🟡 | Usuario inactivo → sin token ni email (✅) | No reactivar por la puerta de atrás. |
| F5 | 🟡 | Pedir un segundo enlace invalida el primero (✅) | Solo el último funciona. |
| F6 | 🟡 | Email en otras mayúsculas encuentra la cuenta | Coherencia con registro. |
| F7 | 🟡 | `_send_reset_link` captura cualquier excepción del servicio | La tarea en segundo plano no debe romper. |

### 2.7 `POST /auth/reset-password` (`test_password_reset.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| X1 | 🟢 | Token válido → nueva contraseña verificable, la anterior ya no; token con `used_at` en la BD | Flujo principal y un solo uso. |
| X2 | 🔴 | Reutilizar el mismo token → `InvalidResetToken` / 400 | Un solo uso. |
| X3 | 🔴 | Token expirado (tiempo avanzado) → rechazado, contraseña intacta | Caducidad. |
| X4 | 🔴 | Token de sesión usado como token de reset → rechazado | Separación de tipos. |
| X5 | 🔴 | Nueva contraseña vacía/corta/de solo espacios → rechazada **sin gastar el token** | Un error del usuario no debe quemar el enlace. |
| X6 | 🔴 | Token firmado válido pero sin estado en BD / de usuario eliminado o inactivo → rechazado (✅ parcial) | Estado servidor como segunda barrera. |
| X7 | 🟡 | Tras el reset se invalidan los demás enlaces pendientes (✅) | Higiene de tokens. |
| X8 | 🔴 | Token con `jti` de otro usuario (sub ≠ dueño del jti) → `consume_reset_token` False | Confusión de identidad. |

### 2.8 `POST /auth/change-password` (`test_change_password.py`)

| # | Tipo | Caso | Por qué importa |
|---|---|---|---|
| C1 | 🟢 | Contraseña actual correcta → hash nuevo; antigua rechazada; tokens de reset pendientes invalidados | Flujo principal. |
| C2 | 🔴 | Contraseña actual incorrecta → `WrongPassword` / 400; hash sin cambios | Evita cambio con sesión robada. |
| C3 | 🔴 | Nueva contraseña vacía, <8, >72 bytes, solo espacios → rechazada; hash sin cambios | Reglas de contraseña consistentes. |
| C4 | 🔴 | Sin token → 401 | Protección de ruta. |
| C5 | 🟡 | Contraseña actual vacía → `WrongPassword` | No debe lanzar 500. |

## 3. Casos sugeridos por la IA (🤖 — tú decides cuáles entran)

Marcados así porque **no estaban en tu lista**:

1. 🤖 **S1** Token sin `exp` firmado con la clave correcta (T11) — `jose` no exige `exp` por defecto.
2. 🤖 **S2** Login con email con espacios alrededor (L7) y `forgot-password` con espacios.
3. 🤖 **S3** Contraseña solo espacios en `PUT /users/{id}`, `reset-password` y `change-password`, no solo en registro.
4. 🤖 **S4** Un usuario que cambia su contraseña **vía `PUT /users/{id}`** ¿invalida los enlaces de reset pendientes? (`update_user` no llama a `invalidate_reset_tokens`).
5. 🤖 **S5** Una contraseña rechazada en reset (X5) no gasta el token.
6. 🤖 **S6** `consume_reset_token` no deja gastar un `jti` de otro usuario y es atómico (dos intentos seguidos: solo el primero gana).
7. 🤖 **S7** Admin que se borra a sí mismo / se degrada: ¿queda el sistema sin admins? (documentar comportamiento).
8. 🤖 **S8** Cambiar el email a mayúsculas del propio email actual no es duplicado.
9. 🤖 **S9** `ALGORITHM=none` o vacío en la configuración: `config.py` solo exige que no esté vacío.
10. 🤖 **S10** Rutas protegidas distintas de auth (`/suppliers`, `/incident-manager`…) rechazan token de reset (test parametrizado de "qué dependencias protegen").
11. 🤖 **S11** Un token de acceso sigue válido tras `change-password`/`reset-password` (JWT sin estado) — documentar, no necesariamente corregir.
12. 🤖 **S12** Usuario con rol cambiado: el siguiente request refleja el nuevo role (se lee de la BD, no del token).
13. 🤖 **S13** `change-password` con nueva contraseña igual a la actual.

## 4. Riesgos de comportamiento inesperado detectados al leer el código (sin corregir)

| ID | Riesgo | Evidencia | Gravedad | Test que lo cubrirá |
|---|---|---|---|---|
| **B1** | **Contraseña de solo espacios aceptada**: `Password = Field(min_length=8)` cuenta `"        "` como válida (comprobado). | `user_models.py` | Media (cuenta con contraseña trivial; afecta registro, reset, change y PUT). | R8, X5, C3, S3 |
| **B2** | **Token sin `exp` aceptado**: `_decode` no pasa `options={"require_exp": True}`; un JWT bien firmado sin `exp` no caduca nunca (comprobado). Hoy solo lo firma el servidor, pero es defensa en profundidad. | `security.py::_decode` | Media-baja. | T11 |
| **B3** | **Email con espacios inconsistente**: el registro lo recorta (`" A@B.com "` → `a@b.com`) pero `authenticate`/`forgot-password` hacen solo `.lower()` sobre `form.username`, sin `strip()`. Un usuario que copia el email con un espacio no puede entrar. | `user_service.get_user_by_email`, `routes/auth.py::login` | Baja (UX). | L7, F6, S2 |
| B4 | `PUT /users/{id}` permite cambiar la **contraseña sin la actual** y sin invalidar enlaces de reset pendientes; un token de sesión robado basta para tomar la cuenta (change-password sí exige la actual). | `routes/users.py`, `user_service.update_user` | Media. **Cambiaría el contrato** → te preguntaría antes. | U1, S4 |
| B5 | Los JWT de acceso siguen vigentes tras cambiar/restablecer contraseña (stateless). | `user_service._set_password` | Baja/diseño. Solo documentar. | S11 |
| B6 | Un admin puede borrarse o degradarse a sí mismo y dejar la app sin admin; además no hay forma de crear el primer admin salvo editando la BD. | `routes/users.py` | Baja/diseño. Solo documentar. | S7 |
| B7 | `reset_password` consume el token **antes** de escribir la contraseña; si `update_user` fallara, el enlace queda gastado. (Las validaciones de contraseña ocurren antes, en Pydantic, así que el riesgo práctico es mínimo.) | `user_service.reset_password` | Baja. | X5 |
| B8 | `config.py` acepta cualquier `ALGORITHM` (incluso `none`). | `config.py` | Baja (error de configuración). | S9 |
| B9 | `UserRepository.get_user_by_email` es sensible a mayúsculas; solo se normaliza en la capa de servicio. Cualquier llamada directa al repositorio con mayúsculas fallaría. | `database.py` | Informativo. | R5 |

## 5. Plan de implementación (resumen de fases siguientes)

- **Fase 2 (backend):** `uv add --dev pytest-cov freezegun` (pytest/httpx ya están); `tests/conftest.py` ampliado con fixtures de repositorio aislado, factorías de usuarios (normal/admin/inactivo) y de tokens (válido/expirado/mal firmado/reset), mock de Resend `autouse`. Módulos: `test_register.py`, `test_login.py`, `test_token.py`, `test_users.py`, `test_profiles.py`, `test_auth_me.py`, `test_password_reset.py`, `test_change_password.py`. Los bugs B1/B2/B3 (si los apruebas) irán cada uno en su commit `fix:` mínimo; B4 requiere tu decisión.
- **Fase 3 (frontend, `uis/backoffice`, npm):** `jest`, `ts-jest`, `@types/jest`, `jest-environment-jsdom`, `jest.config.ts` con `moduleNameMapper` para `@/`; tests de `auth.ts` (token CRUD, `isTokenValid`: exp pasado/malformado/sin exp, `logout`) y `apiClient.ts` (Bearer, 401 → limpia y redirige, con `fetch` y `window.location` mockeados).
- **Fase 4 (extras):** API-042 (incidencias + proveedores) y FE-019 (`getUserMessage`, `statusMessage`, `isTransient`…), solo si lo anterior está en verde.

## 6. Decisiones que necesito de ti

1. ¿Aceptas conservar la suite existente (174 tests) y añadir la capa unitaria, moviendo `test_password_reset.py` si solapa, en vez de reescribir todo?
2. ¿`freezegun` para controlar el tiempo (recomendado)?
3. ¿Qué sugeridos 🤖 (S1–S13) entran? Mi recomendación: todos menos S9 y S10.
4. B1, B2, B3: ¿los corrijo con el cambio mínimo (`strip()`/validador anti-espacios, `require_exp`, `.strip()` en el login)? B4 lo dejo documentado salvo que me digas que lo cambie.
