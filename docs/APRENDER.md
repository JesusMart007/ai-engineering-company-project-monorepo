# Aprender: cómo se construyó el Analizador de incidentes de Nexova

> **Parte I** (§1–14): el analizador de incidentes. **Parte II** (§15–22): los hitos posteriores (proveedores, autenticación, gestor de incidencias, recuperación de contraseña, auditoría de errores y batería de tests). Guía de estudio del proyecto. Explica **qué** se hizo, **por qué** se hizo así y **qué conceptos** hay detrás, para que puedas defenderlo en una revisión y reutilizar las ideas en otros proyectos.

---

## Índice

1. [El problema que resolvemos](#1-el-problema-que-resolvemos)
2. [Paso 0: leer el contexto antes de programar](#2-paso-0-leer-el-contexto-antes-de-programar)
3. [La arquitectura en una imagen](#3-la-arquitectura-en-una-imagen)
4. [Fase 1: el script de consola](#4-fase-1-el-script-de-consola)
5. [Fase 2: la API con FastAPI](#5-fase-2-la-api-con-fastapi)
6. [Fase 2: el backoffice con Next.js](#6-fase-2-el-backoffice-con-nextjs)
7. [Tests: cómo sabemos que funciona](#7-tests-cómo-sabemos-que-funciona)
8. [Problemas reales que aparecieron (y cómo se resolvieron)](#8-problemas-reales-que-aparecieron-y-cómo-se-resolvieron)
9. [Limpieza del repositorio](#9-limpieza-del-repositorio)
10. [Git, PR y entrega](#10-git-pr-y-entrega)
11. [Limitaciones conocidas e ideas para mejorar](#11-limitaciones-conocidas-e-ideas-para-mejorar)
12. [Glosario de conceptos](#12-glosario-de-conceptos)
13. [Preguntas para repasar](#13-preguntas-para-repasar)
14. [Chuleta de comandos](#14-chuleta-de-comandos)

**Parte II: hitos posteriores**

15. [Hito 09: directorio de proveedores](#15-hito-09-directorio-de-proveedores)
16. [AUTH-01: autenticación con JWT](#16-auth-01-autenticación-con-jwt)
17. [Gestor de incidencias centralizado](#17-gestor-de-incidencias-centralizado)
18. [AUTH-03: recuperación y cambio de contraseña](#18-auth-03-recuperación-y-cambio-de-contraseña)
19. [Auditoría de gestión de errores](#19-auditoría-de-gestión-de-errores)
20. [AUTH-088: batería de pruebas de autenticación](#20-auth-088-batería-de-pruebas-de-autenticación)
21. [Glosario ampliado y preguntas de repaso](#21-glosario-ampliado-y-preguntas-de-repaso)
22. [Chuleta de comandos de la Parte II](#22-chuleta-de-comandos-de-la-parte-ii)

---

## 1. El problema que resolvemos

**Nexova** tiene un servicio de soporte al cliente con 30 agentes. Cada ticket se registra en un helpdesk antiguo, y **Roberto Díaz** (Customer Support Lead) exportó un mes de tickets a un CSV. Necesita saber:

- cuántos tickets hay y cuántos están mal registrados,
- cómo se reparten por **categoría** (`TECHNICAL`, `BILLING`, `ACCESS`, `HR_QUERY`, `COMPLAINT`),
- cómo se reparten por **estado** (`OPEN`, `CLOSED`, `DISCARDED`),
- y el **índice de satisfacción** medio de los tickets cerrados (puntuación 1–5).

Hay una restricción muy importante: la columna `customer_email` contiene correos de clientes, así que **ningún email puede aparecer en ninguna salida** (ni consola, ni CSV exportado, ni mensajes de error). Por eso no se puede "pasar el CSV a ChatGPT": hay que construir una herramienta propia.

El proyecto tiene dos fases:

| Fase | Qué se construye | Dónde |
|---|---|---|
| 1 | Script de consola que analiza el CSV | `scripts/analyze.py` |
| 2 | API web + interfaz gráfica que reutilizan la misma lógica | `services/api/` y `uis/backoffice/` |

---

## 2. Paso 0: leer el contexto antes de programar

El prompt pedía leer `CONTEXT-company.md` **antes de escribir código**. Esto es una práctica profesional clave: **el contexto es la especificación**. Si inventas nombres de columnas o reglas, el código "funciona" pero da resultados incorrectos.

Al buscarlo encontramos tres problemas:

1. `CONTEXT-company.md` **no estaba en la raíz**, y el único que existía estaba **vacío (0 bytes)**.
2. El contexto real era `CONTEXT-nexova.es.md`, escondido en una carpeta duplicada por error (`scripts/workspaces/ai-engineering-company-project-monorepo/`).
3. El prompt que se pegó estaba **cortado** a mitad de frase.

En lugar de suponer, **se paró y se preguntó**. Lección: *cuando la especificación es ambigua, preguntar es más barato que rehacer*.

Del contexto se extrajo, sin inventar nada:

| Campo | Obligatorio | Regla |
|---|---|---|
| `ticket_id` | Sí | Formato `NXV-XXXXXX` (6 dígitos) |
| `date` | Sí | `YYYY-MM-DD` |
| `client_company` | Sí | No vacío |
| `category` | Sí | Una de las 5 categorías válidas |
| `description` | Sí | Mínimo 5 caracteres |
| `agent_id` | Sí | Formato `AGT-XX` |
| `status` | Sí | `OPEN`, `CLOSED` o `DISCARDED` |
| `customer_email` | Sí | Debe contener `@` (**dato sensible**) |
| `satisfaction_score` | Solo si `CLOSED` | Entero 1–5 |

Y, muy importante, los **valores esperados** (100 filas → 96 válidas, 4 inválidas, media 3.84…). Con eso tenemos un **oráculo**: una respuesta correcta conocida contra la que comparar. Antes de escribir nada, se hizo una validación rápida del CSV y se confirmó que los datos cuadraban con esos valores.

> Detalle curioso: el contexto dice "1,000 filas" en un párrafo y "100" en otro. El fichero real tiene 100. Cuando dos fuentes se contradicen, manda el dato verificable (el fichero), y conviene mencionarlo.

---

## 3. La arquitectura en una imagen

```
                    ┌──────────────────────────────────────┐
                    │   scripts/incident_analysis.py        │
                    │   (LÓGICA COMPARTIDA)                 │
                    │   - validar filas                     │
                    │   - calcular métricas                 │
                    │   - generar CSV de resultados         │
                    └──────────────┬───────────────────────┘
                   importa         │          importa
          ┌────────────────────────┴───────────────────────┐
          ▼                                                ▼
┌──────────────────────┐                     ┌──────────────────────────┐
│ scripts/analyze.py   │                     │ services/api/app/main.py │
│ (CLI: consola)       │                     │ (FastAPI, puerto 8000)   │
│ imprime el informe   │                     │ POST /analyze  → JSON    │
│ pregunta [s/n]       │                     │ GET  /export   → CSV     │
└──────────────────────┘                     └────────────▲─────────────┘
                                                          │ proxy (rewrite)
                                             ┌────────────┴─────────────┐
                                             │ uis/backoffice (Next.js) │
                                             │ puerto 3000              │
                                             │ /incidents: subir CSV,   │
                                             │ ver resumen, descargar   │
                                             └────────────▲─────────────┘
                                                          │
                                                     navegador
```

**Idea central: una sola fuente de verdad.** La validación y las métricas viven en **un único módulo** (`incident_analysis.py`). El script y la API lo **importan**; no copian su código. Si mañana cambia una regla (por ejemplo, la descripción pasa a necesitar 10 caracteres), se cambia en un sitio y ambos se actualizan. Esto es el principio **DRY** (*Don't Repeat Yourself*), y el prompt lo exigía explícitamente.

También aplica **separación de responsabilidades**:

| Capa | Responsabilidad | NO hace |
|---|---|---|
| `incident_analysis.py` | Reglas de negocio y cálculos | No imprime, no sabe de HTTP |
| `analyze.py` | Presentación en consola, preguntar al usuario | No valida nada por su cuenta |
| `main.py` (API) | HTTP: recibir ficheros, códigos de error | No valida nada por su cuenta |
| Backoffice | Mostrar resultados de forma visual | No calcula métricas |

---

## 4. Fase 1: el script de consola

Archivos: [`scripts/incident_analysis.py`](../scripts/incident_analysis.py) y [`scripts/analyze.py`](../scripts/analyze.py).

### 4.1 Lectura del CSV: ¿pandas o `csv` nativo?

El prompt dejaba elegir. Se usó el módulo **`csv` de la librería estándar** porque:

- son 100 filas: pandas no aporta rendimiento aquí,
- no añade dependencias (el script corre con cualquier Python 3.10+),
- las reglas son fila a fila, algo natural con `csv.DictReader` (cada fila es un diccionario `{columna: valor}`).

Con millones de filas o cálculos vectoriales, pandas sería la mejor elección.

Se lee con `encoding="utf-8-sig"`: igual que UTF-8 pero elimina el **BOM** (un carácter invisible que Excel añade al principio de algunos CSV y que rompería el nombre de la primera columna).

### 4.2 Validar: el modelo `Issue(rule, field, kind)`

Cada problema de una fila se representa con una tupla con nombre:

```python
class Issue(NamedTuple):
    rule: str   # regla del CONTEXT, p. ej. "invalid_category"
    field: str  # columna afectada, p. ej. "category"
    kind: str   # "missing" (valor faltante) o "invalid" (valor no permitido)
```

¿Por qué tres datos? Porque el prompt pedía clasificar los inválidos **"por tipo de problema (campo faltante vs valor fuera de rango) y por campo"**, y además el CONTEXT agrupa por **regla**. Con esta estructura se pueden sacar ambas vistas del mismo dato:

- Vista por regla (la del CONTEXT): `Invalid or missing category ... 1`
- Vista por campo y tipo: `category: missing value ... 1`

Una función auxiliar hace el patrón común "¿está vacío? → faltante; ¿no cumple la regla? → no permitido":

```python
def _check(row, field, rule, is_valid) -> list[Issue]:
    value = _text(row, field)
    if not value:
        return [Issue(rule, field, MISSING)]
    if not is_valid(value):
        return [Issue(rule, field, INVALID)]
    return []
```

Y `find_issues` la aplica a cada campo pasando la regla concreta como función (una expresión regular, una comprobación de pertenencia, una `lambda`…). Esto es **programación con funciones como datos**: en vez de 9 bloques `if` casi iguales, un patrón reutilizado 8 veces.

La puntuación tiene lógica especial (es obligatoria **solo** si el ticket está cerrado), así que tiene su propia función `_score_issues`.

**Decisión importante:** se recogen **todos** los problemas de una fila, no solo el primero. Así el informe es completo: si una fila tiene la categoría y el email mal, cuenta en ambas reglas. El total de inválidos, en cambio, cuenta **filas**, no problemas (por eso la interfaz avisa: "un registro puede tener más de un problema").

### 4.3 Las 4 filas inválidas del fichero

| Ticket | Problema | Tipo |
|---|---|---|
| NXV-000017 | `client_company` vacío | valor faltante |
| NXV-000043 | `category` vacía | valor faltante |
| NXV-000086 | email sin `@` | valor no permitido |
| NXV-000090 | `CLOSED` sin puntuación | valor faltante |

(Para averiguarlo se inspeccionaron las filas **sin imprimir los emails**: solo se mostró si el email estaba vacío o tenía `@`. La privacidad se respeta también mientras desarrollas.)

### 4.4 Calcular las métricas

`analyze_rows` recorre las filas una vez, separa válidas de inválidas y calcula todo **solo con las válidas**:

- `Counter` (de `collections`) cuenta categorías y estados en una línea.
- Los diccionarios de salida se construyen recorriendo `VALID_CATEGORIES` / `VALID_STATUSES`, así el **orden es siempre el del CONTEXT** y aparecen también las categorías con 0.
- La media se redondea a 2 decimales y es `None` si no hay tickets cerrados (evita dividir entre cero).

El resultado es un `@dataclass(frozen=True)` llamado `AnalysisResult`. `frozen=True` lo hace inmutable (nadie puede modificar el resultado por accidente) y `asdict()` lo convierte en diccionario, lo que la API usa para devolver JSON.

### 4.5 Privacidad por diseño

El módulo **nunca devuelve valores de campos**, solo **conteos y nombres de campo**. No es "tener cuidado de no imprimir emails": es que el email **no sale** del módulo, así que es imposible filtrarlo por error en la consola, la API o el CSV. Además, los tests comprueban que no aparece ninguna `@` en ninguna salida.

### 4.6 Errores de fichero

Hay dos tipos de "fallo" distintos, y conviene no mezclarlos:

| Situación | Qué pasa |
|---|---|
| Una **fila** está mal | Se marca inválida, se cuenta y el análisis continúa |
| El **fichero** no sirve (vacío, sin columnas obligatorias, solo cabecera) | Se lanza `CsvFormatError` / `EmptyCsvError` y no se analiza |

Antes de este trabajo, un CSV al que le faltaba una columna marcaba **todas** las filas como inválidas, lo que confunde. Ahora da un error claro: `The CSV is missing required columns: client_company, ...`.

El script convierte esos errores en un mensaje por `stderr` y **código de salida 1** (convención Unix: 0 = éxito, distinto de 0 = error), lo que permite usarlo en automatizaciones.

### 4.7 Presentación y exportación

- `analyze.py` imprime con separadores, `├─`/`└─` y puntos de relleno alineados, imitando la salida de referencia del CONTEXT.
- La consola está en inglés porque la salida de referencia del CONTEXT está en inglés; la pregunta final está en español porque el prompt da ese texto literal: `¿Deseas exportar los resultados a CSV? [s/n]` (acepta `s`, `si`, `sí`, `y`, `yes`).
- `results.csv` tiene **una métrica por fila** (`metric,value,description`), como pidió Roberto para pegarlo en su plantilla. Formato "largo" (una fila por dato) en lugar de "ancho" (una columna por dato): es más fácil de filtrar y de añadir métricas nuevas sin romper nada.
- `results.csv` está en `.gitignore`: es un fichero **generado**, no código fuente.

### 4.8 Verificación contra el CONTEXT

La Fase 1 no se dio por terminada hasta que **todos** los números coincidieron exactamente con el CONTEXT: 100/96/4, 28/18/21/17/12, 27/56/13, 2/5/10/22/17 y media 3.84. Esos mismos números están fijados en los tests, así que si alguien rompe algo, los tests fallan.

---

## 5. Fase 2: la API con FastAPI

Archivo: [`services/api/app/main.py`](../services/api/app/main.py).

### 5.1 Reutilizar el módulo

La API añade la carpeta `scripts/` al `sys.path` e importa las mismas funciones que el script. Hay un test (`test_api_uses_the_same_logic_as_the_script`) que compara la respuesta de la API con la del módulo y exige que sean idénticas.

> En un proyecto más grande, lo ideal sería convertir la lógica en un **paquete instalable** (`packages/incident_analysis` con `pyproject.toml`) en lugar de tocar `sys.path`. Aquí se mantuvo simple porque la estructura del monorepo pedía `scripts/`.

### 5.2 Endpoints

| Método y ruta | Qué hace |
|---|---|
| `GET /health` | Comprobar que la API está viva |
| `POST /api/incidents/analyze` | Recibe el CSV como `multipart/form-data`, devuelve el resumen en JSON |
| `GET /api/incidents/results/export` | Devuelve el último análisis como `results.csv` descargable |

`multipart/form-data` es el formato que usan los navegadores para enviar ficheros en formularios. FastAPI lo recibe con `UploadFile = File(...)` (necesita el paquete `python-multipart`).

El JSON incluye además un campo `labels` con los textos legibles de reglas, tipos y puntuaciones, para que un cliente pueda mostrarlos sin conocer las claves internas.

### 5.3 Códigos HTTP: elegir el correcto

Un buen API **explica qué ha fallado** con el código y el mensaje:

| Código | Significado | Cuándo lo devolvemos |
|---|---|---|
| 200 | OK | Análisis correcto |
| 400 | Bad Request | Fichero vacío, o no está en UTF-8 |
| 404 | Not Found | Pides exportar sin haber analizado nada |
| 413 | Payload Too Large | Fichero de más de 5 MB |
| 415 | Unsupported Media Type | No es `.csv` o el tipo de contenido no es de CSV |
| 422 | Unprocessable Entity | Es un CSV pero no se puede analizar (faltan columnas, sin filas); también si no envías el campo `file` |

La diferencia 400 vs 422 es sutil: **400** = la petición en sí es incorrecta (no hay nada que leer, o no se puede decodificar); **422** = se entendió la petición pero el contenido no cumple lo necesario. Lo importante es ser **coherente** y dar un `detail` descriptivo.

Por eso se creó `EmptyCsvError` como **subclase** de `CsvFormatError`: la API puede distinguir "vacío" (400) del resto (422) con dos `except`, mientras el script trata ambos igual. Es un uso típico de la **herencia de excepciones**.

El límite de 5 MB se aplica leyendo `MAX_UPLOAD_BYTES + 1` bytes: si llega a leer más de 5 MB, sabemos que se pasa sin tener que cargar un fichero gigante entero en memoria.

### 5.4 CORS

Un navegador **bloquea** por seguridad que una página de un origen (`http://localhost:3000`) lea respuestas de otro origen (`http://localhost:8000`) salvo que el servidor lo autorice con cabeceras CORS (*Cross-Origin Resource Sharing*). La API original no las enviaba, así que la interfaz no habría podido hablar con ella. Se añadió `CORSMiddleware` con los orígenes configurables por la variable de entorno `CORS_ORIGINS`.

(Luego se añadió un proxy que evita la necesidad de CORS en el uso normal; ver sección 8.)

### 5.5 "El último análisis"

La API guarda el último resultado en una variable global `_last_result` para que el endpoint de exportación sepa qué devolver. Es la solución más simple que cumple el enunciado, pero tiene límites importantes (ver sección 11).

---

## 6. Fase 2: el backoffice con Next.js

Carpeta: [`uis/backoffice/src/`](../uis/backoffice/src/).

### 6.1 Estructura

| Archivo | Papel |
|---|---|
| `app/layout.tsx` | Plantilla común: barra superior con el menú |
| `components/NavMenu.tsx` | Menú (Inicio / Análisis de incidencias); marca la página actual con `aria-current` |
| `app/page.tsx` | Página de inicio con enlace al análisis |
| `app/incidents/page.tsx` | Página de análisis: estado, carga y descarga |
| `components/FileDrop.tsx` | Zona de arrastrar y soltar + selector de fichero |
| `components/IncidentSummary.tsx` | Todo lo que se ve tras el análisis |
| `lib/incidentsApi.ts` | Tipos TypeScript y funciones que llaman a la API |
| `next.config.ts` | Proxy de `/api/incidents/*` hacia la API |

Separar **componentes de presentación** (`IncidentSummary`), **lógica de red** (`incidentsApi.ts`) y **página que coordina** (`incidents/page.tsx`) hace que cada pieza sea pequeña y fácil de cambiar.

### 6.2 Estado de la página

La página gestiona cuatro estados con `useState`: `result`, `error`, `loading` y `downloading`. Así la interfaz siempre refleja qué está pasando: "Analizando…", el mensaje de error, o el resumen. Los mensajes van dentro de `aria-live="polite"` para que los lectores de pantalla los anuncien.

### 6.3 Arrastrar y soltar

`FileDrop` es un `<label>` que envuelve un `<input type="file">` oculto visualmente (pero accesible). Eso da tres formas de subir el fichero con muy poco código: clic, teclado y arrastrar. Se usan los eventos `onDragOver` (hay que llamar a `preventDefault()` para permitir soltar), `onDragLeave` y `onDrop`. Tras elegir un fichero se vacía `input.value` para poder volver a subir el mismo archivo.

### 6.4 Qué se muestra

- **Métricas generales**: total, válidos, inválidos, satisfacción media.
- **Registros inválidos**: panel destacado "4 de 100", recuento por regla y por campo/tipo (con etiquetas de color *valor faltante* / *valor no permitido*), y aviso de que se excluyen de las métricas.
- **Desglose por categoría y por estado**: tabla con número, porcentaje y barra.
- **Índice de satisfacción**: media grande, cuántos tickets se usaron, reparto 1–5 con barras.
- **Botón de descarga** del CSV.

Las etiquetas se traducen al español en el frontend, con respaldo a las etiquetas que envía la API si aparece una clave nueva.

### 6.5 Descargar el CSV

En vez de un simple enlace, `downloadResultsCsv()` hace `fetch`, convierte la respuesta en un `Blob`, crea una URL temporal con `URL.createObjectURL` y simula un clic en un `<a download>`. Ventaja: si la API responde con error (p. ej. 404 porque se reinició), se muestra el mensaje en la página en lugar de descargar un fichero con el error dentro.

### 6.6 TypeScript

El tipo `AnalysisResult` en `incidentsApi.ts` describe exactamente el JSON de la API. Si usas un campo que no existe o con el tipo equivocado, `next build` falla **antes** de llegar al navegador. Se añadió el alias `@/` en `tsconfig.json` para importar como `@/components/FileDrop` en lugar de `../../components/FileDrop`.

---

## 7. Tests: cómo sabemos que funciona

24 tests con **pytest**, en dos ficheros:

**[`scripts/tests/test_incident_analysis.py`](../scripts/tests/test_incident_analysis.py)**

- Los valores exactos del CONTEXT (totales, reglas, categorías, estados, puntuaciones, media).
- Que "faltante" y "no permitido" se separan bien.
- Un CSV inventado con una fila que rompe **cada** regla, para comprobar que todas se detectan.
- Casos límite: puntuación en un ticket abierto (válida pero no cuenta para el índice), fichero vacío, solo BOM, columnas que faltan, solo cabecera. Usa `@pytest.mark.parametrize` para probar varios casos con un solo test.
- El **script real** ejecutado con `subprocess`, respondiendo `s`, comprobando la salida, el `results.csv` y que **no hay ni una `@`** en nada.

**[`services/api/tests/test_api.py`](../services/api/tests/test_api.py)**

- Con `TestClient` de FastAPI (hace peticiones HTTP sin arrancar un servidor).
- El análisis devuelve los valores del CONTEXT y no contiene emails.
- La API y el módulo dan **exactamente** el mismo resultado (prueba de que no hay lógica duplicada).
- La exportación es un CSV válido de 3 columnas con la cabecera correcta.
- Cada error devuelve su código (400, 404, 415, 422) con mensaje.
- CORS permite el origen del backoffice.

`conftest.py` es un fichero especial de pytest que se ejecuta antes de los tests; aquí prepara el `sys.path`.

**Además**, se hizo una prueba **de extremo a extremo** con **Playwright** (un navegador Chromium sin ventana controlado por código): abrir la web, navegar por el menú, subir el CSV, leer el resultado, descargar el CSV, subir un fichero erróneo y ver el error, y comprobar que en móvil no hay scroll horizontal. Los tests unitarios dicen "las piezas funcionan"; la prueba en navegador dice "el usuario puede usarlo". Las capturas del PR se generaron de la misma forma.

---

## 8. Problemas reales que aparecieron (y cómo se resolvieron)

### "No se pudo conectar con la API en http://localhost:8000"

**Síntoma:** en tu navegador, la web cargaba pero no podía analizar.

**Causa:** estás usando **GitHub Codespaces en el navegador**. El código corre en una máquina en la nube; tu navegador abre la web en `https://…-3000.app.github.dev`. Cuando la página pedía `http://localhost:8000`, ese `localhost` era **tu ordenador**, no el Codespace, y allí no hay ninguna API.

**Solución: un proxy inverso.** En `next.config.ts` se añadió una regla `rewrites`: cuando el navegador pide `/api/incidents/...` al **propio backoffice** (puerto 3000), Next.js reenvía la petición **desde el servidor** a `http://127.0.0.1:8000`. El navegador solo habla con un origen, así que:

- funciona igual en local, en Codespaces o detrás de cualquier dominio,
- no hace falta abrir el puerto 8000 a Internet,
- desaparece el problema de CORS en el uso normal.

Es exactamente lo que se hace en producción (con Nginx, un API Gateway, etc.). La variable `API_INTERNAL_URL` permite cambiar a dónde se reenvía.

**Lección:** "funciona en mi máquina" no basta; piensa **desde dónde** se hace cada petición (navegador vs servidor).

### `pkill -f` se mató a sí mismo

Para parar el servidor se usó `pkill -f "next-server"`. `pkill -f` busca el texto en la **línea de comandos completa** de cada proceso… y la propia shell que ejecutaba el comando contenía ese texto, así que se terminó a sí misma. Solución: listar con `ps` y matar por PID. Pequeña lección de Linux.

### Todas las filas inválidas si falta una columna

Comentado en 4.6: se pasó de "cada fila es inválida" a "el fichero no es válido", con un mensaje que dice qué columnas faltan.

---

## 9. Limpieza del repositorio

| Eliminado / movido | Motivo |
|---|---|
| `scripts/analyse.py` | Intento antiguo con columnas en español (`estado`, `tipo`) que no cumplía el CONTEXT; tenerlo junto a `analyze.py` confunde |
| `scripts/workspaces/…` | Copia anidada del repo creada por error: CSV duplicado (idéntico byte a byte, comprobado con `cmp`) y `CONTEXT-company.md` vacío |
| `CONTEXT-nexova.es.md` → raíz | Es la especificación del proyecto; debe estar donde se espera encontrarla |
| `uis/website/` | Solo contenía una carpeta `.next` (salida de compilación) suelta |
| `services/api/app/routers/` | Carpeta vacía |
| `__pycache__`, `results.csv` | Ficheros generados; ya estaban en `.gitignore` |
| `.pytest_cache/` añadido a `.gitignore` | Caché de pytest, no es código |

Regla general: **en git va el código fuente y lo necesario para reproducirlo; lo generado (builds, cachés, resultados) se ignora.** Y antes de borrar, se comprueba (por eso se verificó que el CSV era idéntico antes de eliminar la copia).

---

## 10. Git, PR y entrega

- Rama: `feat/incident-analyzer` (convención `feat/` para funcionalidades nuevas).
- Commits con mensajes del estilo *Conventional Commits* (`feat:`, `fix:`, `docs:`), que dicen **qué** y **por qué**:

| Commit | Contenido |
|---|---|
| `6476519` | Tu primera versión del analizador |
| `f1d7a68` | Script, API y backoffice completos + limpieza |
| `a210f2d` | Proxy para que la web funcione en Codespaces |
| `1742252` | Capturas de pantalla para la entrega |

- **PR #3** contra `main` de **tu fork** (`JesusMart007/...`), no contra el repo original de 4Geeks (`upstream`). Con `gh` hay que indicar `--repo` y `--base` explícitamente, porque en un fork `gh` tiende a apuntar al repositorio original.
- La descripción del PR incluye resumen, cómo probar, checklist y las dos capturas (guardadas en `docs/screenshots/`).
- **Decisión sobre datos:** el CSV se incluyó en el repo porque es ficticio y los tests lo necesitan. Con datos reales **nunca** se subiría a git: el historial es permanente aunque luego lo borres.

---

## 11. Limitaciones conocidas e ideas para mejorar

Buenas candidatas para practicar o para comentar en la revisión:

1. **`_last_result` es global y en memoria.** Si dos usuarios analizan a la vez, uno puede descargar el análisis del otro; si la API se reinicia, se pierde. Mejora: devolver un `analysis_id` en `/analyze` y exportar con `/results/{id}/export`, guardando en una base de datos o caché.
2. **Sin autenticación.** Cualquiera con acceso a la URL puede usar la API. En producción, el backoffice necesitaría login.
3. **`sys.path` en la API.** Convertir `incident_analysis` en un paquete instalable sería más limpio.
4. **Idioma mezclado.** Consola en inglés (por el CONTEXT) y web en español. Se podría añadir un parámetro `--lang`.
5. **Escalabilidad.** Para ficheros muy grandes, procesar en streaming o con pandas/polars, y hacer el análisis en segundo plano.
6. **Validación de email mínima.** El CONTEXT solo pide que contenga `@`; una validación real sería más estricta (pero cambiarlo alteraría los resultados esperados: el CONTEXT manda).
7. **Tests del frontend.** No hay tests automáticos de React; se podrían añadir con Playwright o Testing Library.

---

## 12. Glosario de conceptos

| Concepto | En una frase | Dónde aparece |
|---|---|---|
| **DRY** | No duplicar lógica: una sola fuente de verdad | `incident_analysis.py` usado por CLI y API |
| **Separación de responsabilidades** | Cada módulo hace una cosa | Lógica / consola / HTTP / UI |
| **Oráculo de pruebas** | Resultado correcto conocido para comparar | Valores esperados del CONTEXT |
| **Privacidad por diseño** | El dato sensible no puede salir, no "intentamos no sacarlo" | Solo se devuelven conteos |
| **`NamedTuple` / `dataclass`** | Estructuras de datos con nombre y tipos | `Issue`, `AnalysisResult` |
| **`Counter`** | Diccionario que cuenta ocurrencias | Categorías, estados, puntuaciones |
| **Expresión regular** | Patrón de texto | `NXV-\d{6}`, `AGT-\d{2}` |
| **Jerarquía de excepciones** | Subclases para distinguir errores | `EmptyCsvError(CsvFormatError)` |
| **Código de salida** | 0 éxito, ≠0 error en programas de consola | `analyze.py` devuelve 1 si falla |
| **multipart/form-data** | Formato para enviar ficheros por HTTP | `POST /analyze` |
| **Códigos HTTP** | Lenguaje estándar para describir el resultado | 200/400/404/413/415/422 |
| **CORS** | Permiso del servidor para peticiones desde otro origen | `CORSMiddleware` |
| **Proxy inverso / rewrite** | Un servidor reenvía peticiones a otro | `next.config.ts` |
| **Blob / Object URL** | Fichero en memoria del navegador descargable | Botón de descarga |
| **Accesibilidad (a11y)** | Que funcione con teclado y lector de pantalla | `label`, `aria-live`, `aria-current` |
| **pytest fixture / parametrize** | Preparación reutilizable / un test con muchos casos | Tests |
| **TestClient** | Probar una API sin arrancar servidor | `test_api.py` |
| **E2E con Playwright** | Probar como un usuario real en un navegador | Verificación y capturas |
| **`.gitignore`** | Qué no debe entrar en git | `results.csv`, cachés, builds |

---

## 13. Preguntas para repasar

Intenta responderlas sin mirar; las respuestas están en las secciones indicadas.

1. ¿Por qué la lógica está en `incident_analysis.py` y no dentro de `analyze.py`? (§3)
2. Una fila tiene la categoría vacía **y** el email sin `@`. ¿Cuánto suma al total de inválidos? ¿Y a cada regla? (§4.2)
3. ¿Qué diferencia hay entre "valor faltante" y "valor no permitido"? Pon un ejemplo de cada uno del CSV real. (§4.3)
4. ¿Por qué un ticket `OPEN` con puntuación 3 es válido pero no cuenta en el índice de satisfacción? (§7)
5. ¿Qué código HTTP devuelve la API si subes un PDF? ¿Y un CSV sin la columna `status`? (§5.3)
6. ¿Por qué la web funcionaba con Playwright dentro del Codespace pero no en tu navegador? (§8)
7. ¿Qué pasaría con `_last_result` si dos compañeros usan la web a la vez? ¿Cómo lo arreglarías? (§11)
8. ¿Cómo garantiza el diseño que ningún email se filtre, incluso en mensajes de error? (§4.5)

---

## 14. Chuleta de comandos

```bash
# Script (desde la carpeta scripts)
cd scripts && python analyze.py incidents-nexova.csv

# API (puerto 8000)
cd services/api && ../../.venv/bin/python -m uvicorn app.main:app --port 8000

# Backoffice (puerto 3000) → abrir /incidents
cd uis/backoffice && npm run dev

# Tests (desde la raíz)
.venv/bin/python -m pytest scripts/tests services/api/tests

# Compilar el frontend (detecta errores de TypeScript)
cd uis/backoffice && npx next build

# Probar la API a mano
curl -F "file=@scripts/incidents-nexova.csv;type=text/csv" localhost:8000/api/incidents/analyze
curl localhost:8000/api/incidents/results/export
```

---

# PARTE II — Los hitos posteriores

> Nota: la Parte I describe la primera versión del proyecto (con `app/main.py` y una variable global). Desde entonces el código se reorganizó: la API vive plana en `services/api/` (`main.py`, `database.py`, `routes/`…) y la lógica común en `packages/shared`. Aquí se explica el estado actual.

---

## 15. Hito 09: directorio de proveedores

**Qué se hizo:** un directorio de proveedores con API REST, base de datos y página en el backoffice. Commits: `2eb395a` (modelos), `6dc6726` (repositorio), `dcd48e9` (endpoints), `7dedae4` (página).

### 15.1 Capas, otra vez

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Modelo | `models.py` | Qué es un `Supplier` y qué datos son válidos (Pydantic) |
| Acceso a datos | `database.py` → `SupplierRepository` | Guardar y leer en TinyDB |
| HTTP | `routes/suppliers.py` | Códigos de estado, validación de entrada |
| UI | `uis/backoffice/.../suppliers` | Tabla, filtros, formulario |

**Idea clave: el patrón repositorio.** Las rutas solo hablan con `SupplierRepository`. Si mañana se cambia TinyDB por Postgres, se reescribe `database.py` y las rutas no se tocan. Es la misma separación de responsabilidades de la Parte I, aplicada a los datos.

### 15.2 Decisiones que merece la pena entender

- **TinyDB** guarda JSON en un archivo: suficiente para aprender sin instalar un servidor de base de datos. Las fechas se guardan como texto ISO 8601 y se convierten a objetos al leer.
- **Un `Lock` por repositorio.** FastAPI ejecuta las rutas síncronas en un *pool* de hilos y TinyDB no es seguro entre hilos. El `threading.Lock` evita que dos peticiones corrompan el archivo.
- **Códigos HTTP:** `201` al crear, `409` si el nombre ya existe, `404` si el id no existe, `422` si la entrada es inválida, `204` al borrar. Se prefiere *suspender* a borrar: un proveedor suspendido se conserva como historial.
- **Seed idempotente** (`uv run seed`): ejecutarlo dos veces no duplica datos. «Idempotente» = repetir la operación da el mismo resultado que hacerla una vez. Además la API siembra la base de datos al arrancar si está vacía.
- **Filtros** por país y categoría; combinarlos aplica ambos. Un valor inválido da `422`, no una lista vacía engañosa.
- **El proxy de Next.js** (sección 8) se amplió: `/api/suppliers` → `/suppliers`. El prefijo `/api` evita chocar con la *página* `/suppliers`.

---

## 16. AUTH-01: autenticación con JWT

**Qué se hizo:** registro, login, perfiles y protección de rutas. Módulos `users`, `profiles` y `auth` (`routes/`), con `user_service.py`, `security.py` y `dependencies.py`.

### 16.1 Autenticación vs autorización

| Concepto | Pregunta | En el proyecto |
|---|---|---|
| **Autenticación** | ¿Quién eres? | Login con email y contraseña → token JWT. Si falla: **401** |
| **Autorización** | ¿Qué puedes hacer? | Solo tú o un admin tocáis tu cuenta. Si falla: **403** |

### 16.2 Contraseñas

- Se guardan con **bcrypt** (librería `libpass`), nunca en texto plano. bcrypt es un hash **lento a propósito** y con **sal** aleatoria: dos usuarios con la misma contraseña tienen hashes distintos.
- bcrypt solo mira los **primeros 72 bytes**; por eso el modelo rechaza contraseñas más largas en vez de truncarlas en silencio.
- `hashed_password` solo existe en el modelo interno `User`. Los modelos de respuesta (`UserPublic`) no lo tienen, así que **no puede salir** en ninguna respuesta (privacidad por diseño, como en la §4.5).

### 16.3 El token JWT

Un JWT es texto firmado con tres partes: cabecera, **claims** (datos) y firma. Contiene `sub` (id del usuario), `exp` (cuándo caduca) y `type`. El servidor **no guarda sesiones**: cada petición trae el token y el servidor comprueba la firma. Eso es *stateless*.

El token se envía en `Authorization: Bearer <token>`. La dependencia `get_current_user` lo decodifica, busca al usuario y lanza **401** si el token falta, está mal firmado, caducó, el usuario no existe o está inactivo. Se aplica a una ruta con `Depends(...)`, y así queda protegida con una línea.

### 16.4 Reglas de seguridad del alta

- `UserCreate` usa `extra="forbid"`: si alguien envía `"role": "admin"` en el registro, recibe **422** y no se crea nada. Todo usuario nuevo es `user`.
- Solo un admin puede cambiar un `role`; los valores permitidos son `admin`, `manager` y `user`.
- Los emails se guardan en minúsculas, para que `Ana@x.com` y `ana@x.com` sean la misma cuenta.
- El login responde igual si falla la contraseña o si no existe el email, para que nadie pueda **averiguar qué cuentas existen** (enumeración de usuarios). Para que tampoco lo delate el tiempo, con un email inexistente se verifica igualmente contra un hash falso.

### 16.5 Frontend

- El token se guarda en `localStorage` (`lib/auth.ts`). Es sencillo, pero un script malicioso (XSS) podría leerlo; la alternativa más segura son cookies `HttpOnly`. Es un compromiso a conocer.
- `lib/apiClient.ts` añade el `Bearer` a cada llamada y, ante un **401**, borra el token y redirige a `/login`.
- `AuthGuard` protege las páginas privadas; hay vistas de login, registro y perfil, y un botón «Cerrar sesión».

---

## 17. Gestor de incidencias centralizado

**Qué se hizo:** de «analizar un CSV» a **gestionar** incidencias: crearlas, listarlas con filtros, cambiar su estado y ver un resumen. Commits `3451e74`…`029b77a`.

- **Paquete compartido `nexova_shared`** (`packages/shared`): ahí viven los valores permitidos y el ciclo de vida (`incidents.py`) y la validación del CSV (`csv_validation.py`). Es la solución que la sección 11 proponía en lugar de tocar `sys.path`. Un único sitio define los estados; API, seed y tests lo importan.
- **Máquina de estados.** Una incidencia pasa por `open` → `in_progress` → `resolved` o `discarded`, y `can_transition(actual, nuevo)` decide qué cambios están permitidos. Un cambio inválido da `400`. La comprobación y la actualización ocurren bajo el mismo `Lock`, así que dos peticiones simultáneas no pueden mover la misma incidencia a la vez.
- **`source_id` único** (el `ticket_id` del CSV): si se repite, `SourceIdAlreadyExists`. Gracias a ello el **seed histórico es idempotente**: inserta 96 incidencias, salta las ya existentes y rechaza 4 filas inválidas.
- **Errores propios.** Las rutas devuelven `400 {detail, errors:[{field, message}]}` con mensajes ya en español, para que el formulario marque cada campo.
- Frontend: formulario «Registrar incidencia», lista con filtros y cambio de estado, y panel de resumen.

---

## 18. AUTH-03: recuperación y cambio de contraseña

**Qué se hizo:** `forgot-password`, `reset-password` y `change-password`, con envío de email por **Resend**.

### 18.1 Flujo

1. El usuario pide el enlace con su email (`/auth/forgot-password`).
2. Si la cuenta existe y está activa, se crea un **token de reset** y se envía un email con el enlace `FRONTEND_URL/reset-password?token=…`.
3. El usuario abre el enlace y elige la nueva contraseña (`/auth/reset-password`).

### 18.2 Decisiones de seguridad

- **Misma respuesta siempre.** `forgot-password` contesta lo mismo exista o no el email. La búsqueda, el token y el email se hacen **después** de responder (`BackgroundTasks`), así que ni el contenido ni el tiempo de la respuesta revelan nada.
- **Tokens con tipo.** Cada JWT lleva `type`: `access` (sesión) o `password_reset`. Cada decodificador acepta **solo su tipo**: un enlace de reset no sirve como sesión ni al revés.
- **Un solo uso.** El token lleva un `jti` (identificador único) que se guarda en la base de datos. Al usarlo se marca `used_at`, y se comprueba y se marca bajo un mismo `Lock`, de modo que dos peticiones no pueden gastar el mismo enlace. Pedir un enlace nuevo invalida los anteriores, y cambiar la contraseña invalida los pendientes.
- **Caducidad** configurable (`RESET_TOKEN_EXPIRE_MINUTES`, 30 por defecto).
- **Resend nunca rompe la respuesta.** Si falla (clave inválida, red, límite), se registra en el log **sin** el destinatario, el enlace ni la clave, y el usuario ve la misma respuesta.
- `change-password` exige la contraseña actual: con una sesión robada no basta para cambiarla.

---

## 19. Auditoría de gestión de errores

**Qué se hizo:** una revisión sistemática de cómo falla todo el sistema, documentada en [`docs/error-handling-audit.md`](error-handling-audit.md). Dio **35 hallazgos** (0 críticos, 8 altos, 11 medios, 16 bajos): 34 corregidos y 1 que no aplicaba.

### 19.1 Método

Lectura de cada módulo con números de línea, barridos con `git grep` (secretos, `print`, `.env`) y **comprobaciones en vivo** (p. ej. enviar una contraseña corta y ver qué devolvía la API). Cada hallazgo tiene archivo:línea, categoría, gravedad, corrección sugerida y estado.

### 19.2 Los tres problemas de más peso

| Problema | Corrección |
|---|---|
| Los errores 500 salían como texto plano, y los **422 devolvían la contraseña y los tokens en `input`** (filtración de datos) | Un manejador global que devuelve un JSON genérico y registra el error; el 422 ya no repite lo enviado (`errors.py`) |
| El frontend mostraba `HTTP 500`, `Unexpected token '<'` o `Failed to fetch` | **Una sola función**, `getUserMessage(error)`, que traduce cualquier error a un mensaje para personas. Los componentes nunca muestran `error.message` |
| Sin `error.tsx` ni `not-found.tsx`: un fallo de renderizado dejaba la pantalla en blanco | Páginas de error con una **salida** (reintentar, ir a inicio, contacto) en las dos apps Next.js |

### 19.3 Otras ideas

- **Timeouts:** el cliente HTTP aborta tras 15 s (`AbortSignal.timeout`) y Resend tiene 10 s; sin límite, una API colgada deja la interfaz «cargando» para siempre.
- **Errores en capas:** un fallo de fichero en un script termina con mensaje claro y código de salida 1, no con un traceback; una BD corrupta falla **nombrando el archivo** (`DatabaseFileError`).
- **Estados de error con salida:** nunca un callejón sin salida; siempre hay un botón o enlace para continuar.
- **No fallar en silencio:** un `catch {}` vacío en `forgot-password` hacía creer al usuario que el correo salía aunque la API estuviera caída.

---

## 20. AUTH-088: batería de pruebas de autenticación

**Qué se hizo:** una suite de tests para la autenticación, backend y frontend, siguiendo un flujo en fases con **plan aprobado antes de escribir código**. El plan, los resultados, la cobertura y los bugs están en [`services/api/TESTING.md`](../services/api/TESTING.md).

### 20.1 Plan antes de código

La Fase 1 fue solo **leer el código y escribir un plan**: qué se prueba, qué no, y una tabla por endpoint con camino feliz, caso límite y modo de fallo, cada caso con su «por qué importa». También se listaron los **riesgos** detectados al leer el código, sin corregirlos, para decidir después. Esto evita escribir tests «de relleno».

### 20.2 Qué probar y qué no

- **Sí:** lógica de negocio (servicios, funciones de token, `get_current_user`, reglas de permisos).
- **No:** la forma del JSON ni los internos de FastAPI/Pydantic (no se prueba que `EmailStr` valide emails: eso ya lo prueba su autor).

Por eso los tests llaman **directamente** a `user_service.authenticate(...)` o a `get_current_user(token, repo)` y afirman la *decisión* (excepción lanzada, usuario creado, token marcado como usado). `TestClient` solo se usa cuando la decisión vive en la ruta (qué dependencias protegen un endpoint).

### 20.3 Técnicas útiles

| Técnica | Para qué |
|---|---|
| **Aislamiento** | Cada test usa su TinyDB en `tmp_path`: los tests nunca tocan `data/` y son independientes |
| **Fixtures y factorías** | `make_user`, `make_token`… crean usuarios y tokens (válido, caducado, mal firmado) en una línea |
| **Mock** | Resend se sustituye por un recolector con un fixture `autouse`: ningún test envía correos ni necesita `RESEND_API_KEY` |
| **Control del tiempo** (`freezegun`) | Congelar el reloj permite afirmar que `exp` = ahora + 30 min y que 1 s después se rechaza, **sin `sleep`** |
| **Parametrización** | Un test, muchos casos (`""`, `"abc"`, `"a.b.c"`…) |
| **Probar la frontera** | Un segundo antes de caducar el token sirve; un segundo después, no |
| **Nombres descriptivos** | `test_login_rejects_wrong_password_with_generic_error` explica el fallo sin abrir el test |

Detalle importante: `config.py` lee `SECRET_KEY` y los minutos **al importar**, así que `monkeypatch.setenv` llega tarde. El conftest fija el entorno antes de importar y los tests que necesitan otro valor parchean el atributo del módulo.

### 20.4 Un test que falla es una buena noticia

Regla acordada: **si un test revela un bug, no se ajusta el test al comportamiento erróneo; se corrige el código en un commit `fix:` aparte**. Así el historial muestra el test fallando y luego el arreglo mínimo.

| Bug | Qué pasaba | Arreglo |
|---|---|---|
| Token sin `exp` | Un JWT bien firmado sin caducidad se aceptaba para siempre; `jose` no exige `exp` por defecto | `options={"require_exp": True}` |
| Contraseña en blanco | `"        "` (8 espacios) cumplía `min_length=8` | Validador que rechaza las contraseñas solo con espacios |
| Email con espacios | El alta recortaba el email, pero el login no, y el usuario no podía entrar | `.strip()` al buscar por email |
| Reset vivo tras `PUT` | Cambiar la contraseña por `PUT /users/{id}` dejaba válidos los enlaces de reset | Invalidarlos al cambiar la contraseña |

También quedó **documentado sin cambiar** un riesgo de diseño: `PUT /users/{id}` permite cambiar la contraseña sin pedir la actual, y corregirlo cambiaría el contrato de la API, así que se deja a decisión de quien manda. Distinguir un *bug* de un *cambio de contrato* es parte del oficio.

### 20.5 Reutilizar lo que ya existe

La API ya tenía 174 tests, la mayoría por HTTP. En vez de reescribirlos se **añadió una capa unitaria** encima. Antes de crear trabajo, mira qué hay.

### 20.6 Jest en el frontend

En `uis/backoffice` se configuró **Jest** con `ts-jest` y el alias `@/`. 61 tests cubren el almacenamiento del token, la comprobación de caducidad (`exp` pasado, token mal formado, sin `exp`), el cliente de API (añade el Bearer; ante un 401 limpia el token y redirige; `fetch` mockeado), los mensajes de error y las traducciones de `authApi`.

Lecciones concretas:
- jsdom (el «navegador» de Jest) **no permite sustituir `window.location`**; la redirección se comprueba de otra forma o se *mockea el módulo* que la hace.
- El cliente HTTP necesita `Response` y `fetch`, que jsdom no trae: esos tests usan el entorno `node` (`/** @jest-environment node */`).
- `localStorage` bloqueado (modo privado) se simula haciendo que `getItem` lance una excepción: así se prueba el camino de fallo.

### 20.7 Cobertura: qué dice y qué no

Resultado: 98 % en los módulos de autenticación del backend y 86 % en las utilidades del frontend. La cobertura mide **qué líneas se ejecutaron**, no si los tests *afirman* algo útil. Sirve para encontrar ramas sin probar, no para demostrar que el código está bien.

---

## 21. Glosario ampliado y preguntas de repaso

| Concepto | En una frase | Dónde aparece |
|---|---|---|
| **Patrón repositorio** | Una capa que oculta cómo se guardan los datos | `SupplierRepository`, `UserRepository` |
| **Idempotencia** | Repetir la operación da el mismo resultado | Seeds |
| **`threading.Lock`** | Evita que dos hilos modifiquen a la vez | Repositorios |
| **Autenticación / autorización** | Quién eres / qué puedes hacer (401 / 403) | §16 |
| **Hash con sal (bcrypt)** | Huella lenta e irreversible de la contraseña | `security.py` |
| **JWT, claims** | Token firmado con `sub`, `exp`, `type` | §16.3 |
| **Stateless** | El servidor no guarda sesiones | JWT |
| **Enumeración de usuarios** | Descubrir qué cuentas existen por las respuestas | Login, forgot-password |
| **`jti` / un solo uso** | Identificador para que un token se gaste una vez | Reset |
| **Máquina de estados** | Qué cambios de estado están permitidos | Incidencias |
| **Auditoría** | Revisión sistemática con hallazgos y gravedad | §19 |
| **Mock / fixture / freezegun** | Sustituir una pieza / preparar datos / controlar el reloj | §20.3 |
| **Cobertura** | % de líneas ejecutadas por los tests | `pytest --cov`, `jest --coverage` |
| **Test de regresión** | Test que fija un bug corregido para que no vuelva | §20.4 |

### Preguntas

1. ¿Por qué las rutas hablan con un repositorio y no con TinyDB directamente? (§15.1)
2. ¿Cuándo devuelve la API 401 y cuándo 403? Pon un ejemplo de cada una. (§16.1)
3. ¿Por qué `forgot-password` responde igual si el email no existe y hace el trabajo *después* de responder? (§18.2)
4. ¿Qué impide que un enlace de reset sirva como token de sesión? (§18.2)
5. ¿Por qué el 422 que devolvía la contraseña era un problema de seguridad? (§19.2)
6. ¿Por qué se usa `freezegun` en vez de `sleep` para probar la caducidad? (§20.3)
7. Un test falla y descubre un bug. ¿Qué haces con el test y qué haces con el código? (§20.4)
8. ¿Por qué `monkeypatch.setenv("SECRET_KEY", …)` no cambia nada en este proyecto? (§20.3)
9. ¿Qué diferencia hay entre arreglar un bug y cambiar el contrato de una API? (§20.4)

---

## 22. Chuleta de comandos de la Parte II

```bash
# API (desde services/api)
uv run uvicorn main:app --reload        # http://localhost:8000/docs (Swagger)
uv run seed                             # carga los proveedores iniciales

# Tests del backend
uv run pytest                           # toda la suite
uv run pytest tests/test_token.py -q    # un módulo
uv run pytest --cov=security --cov=user_service --cov-report=term-missing

# Backoffice (desde uis/backoffice)
npm run dev                             # http://localhost:3000
npm test                                # Jest con cobertura
npx tsc --noEmit && npx eslint src      # tipos y lint
npx next build                          # compilar

# Git
git switch -c feature/auth-tests
git push -u origin feature/auth-tests
```

---

## 23. Hito 5: inventario con ORM y doble base de datos

### 23.1 Qué aporta este hito al bootcamp

Hasta ahora todo vivía en TinyDB, un fichero JSON. Una empresa real tiene varias bases de datos con funciones distintas, y este hito es el primer contacto con eso:

- **Dos bases a la vez.** TinyDB sigue guardando usuarios y autenticación; Supabase (PostgreSQL en la nube) guarda el inventario. Cada petición va al almacén que le toca.
- **Un ORM.** SQLModel convierte clases Python en tablas (clase → tabla, instancia → fila, atributo → columna). No sustituye saber SQL: hay que entender qué consulta genera por debajo.
- **Integridad por diseño.** La regla del negocio ("el stock no se edita, solo cambia con órdenes") se impone en el modelo de datos: no existe la columna.
- **Rendimiento.** El problema N+1 y cómo evitarlo con agregados y JOIN.
- **Concurrencia.** Qué pasa cuando dos peticiones intentan sacar el mismo stock a la vez.

### 23.2 Decisiones y por qué

| Decisión | Motivo |
| --- | --- |
| `Asset` sin columna de stock | Un número guardado puede desincronizarse del historial; uno calculado, no. |
| `user_uuid` sin clave foránea | Los usuarios están en otra base (TinyDB); Postgres no puede garantizar esa referencia, y copiar la tabla duplicaría datos. |
| Modelos (`inventory_models.py`) y schemas (`inventory_schemas.py`) separados | Una tabla es el almacenamiento; un schema es el contrato de la API. Mezclarlos filtraría campos internos y ataría la API a la base. |
| `models.py` no se reutiliza | Ya contiene los modelos de proveedores; se sigue el patrón del repo (`incident_models.py`, `user_models.py`). |
| Una sesión por petición (`get_db` con `yield`) | Una sesión global compartiría transacciones entre usuarios. |
| Engine perezoso, pool pequeño, `pool_pre_ping` | El pooler de Supabase ya agrupa conexiones; `pre_ping` descarta las que cerró. Los tests usan SQLite en memoria sin tocar la nube. |
| `postgresql+psycopg2://` forzado | SQLAlchemy 2.1 elige psycopg v3 con `postgresql://`; el proyecto instala psycopg2. |

### 23.3 El stock sin N+1

Cargar los productos y consultar el stock de cada uno en un bucle serían 1 + N consultas. Aquí:

- `GET /products`: **1 consulta**. Dos subconsultas agrupadas (`SUM ... GROUP BY asset_id`, una de entradas y otra de salidas) se unen con `LEFT JOIN` a `Asset`; `coalesce(..., 0)` da 0 a los activos sin órdenes.
- `GET /orders`: **2 consultas**, una por tipo de orden, cada una con `JOIN` al activo.
- Un test cuenta las consultas con 2 y con 8 activos y comprueba que el número no cambia.

### 23.4 La salida y las condiciones de carrera

Para rechazar una salida hay que leer el stock y luego escribir. Si dos peticiones leen "quedan 5" y cada una saca 4, el stock acabaría en −3. Solución: en una sola transacción, `SELECT ... FOR UPDATE` bloquea la fila del activo, de modo que la segunda petición espera a que acabe la primera y entonces ve el stock real. Si no hay stock se hace `rollback` y se responde 400 sin escribir nada. SQLite ignora `FOR UPDATE`, así que los tests no prueban la concurrencia; eso se comprueba a mano contra Postgres.

### 23.5 Seed idempotente sin columnas extra

El CONTEXT fija los campos de las órdenes, y no tienen identificador estable. En vez de añadir una columna fuera de la especificación, las órdenes sembradas llevan un `created_at` fijo y se identifican por (activo, cantidad, proveedor o tipo, destinatario, oficina, fecha). Ejecutarlo dos veces no duplica nada.

### 23.6 Preguntas de repaso

1. ¿Por qué el stock no es una columna? ¿Qué bug evita?
2. ¿Qué diferencia hay entre un modelo SQLModel y un schema Pydantic aquí?
3. ¿Por qué `user_uuid` no tiene clave foránea?
4. ¿Cuántas consultas hace `GET /inventory/products` con 1000 activos, y por qué?
5. ¿Qué haría el código sin `FOR UPDATE` si dos salidas llegan a la vez?
6. ¿Por qué los tests usan SQLite y qué NO pueden comprobar?
