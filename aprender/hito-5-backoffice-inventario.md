# Hito 5 · Backoffice de inventario

## 1. Resumen en 5 líneas

1. Nexova no sabía qué equipos y materiales había en stock ni quién los tenía; el hito anterior creó la API `/inventory`.
2. Este hito añade al backoffice existente (`uis/backoffice`) la interfaz para usar esa API.
3. Son cuatro pantallas: **Activos** (con su stock), **Entrada de activos**, **Salida de activos** e **Historial de órdenes**.
4. Está pensado para el equipo de IT y operaciones, que registra entregas, asignaciones y consumos.
5. El stock nunca se edita a mano: solo cambia al registrar una entrada (suma) o una salida (resta).

## 2. Mapa de archivos

Todos bajo `uis/backoffice/` salvo que se indique.

| Archivo | Papel |
|---|---|
| `src/lib/inventory.ts` | **Capa de integración**: tipos de la API, las cinco funciones (`getProducts`, `getProduct`, `createInboundOrder`, `createOutboundOrder`, `getOrders`) y `stockLevel()` con los umbrales. |
| `src/lib/apiClient.ts` (modificado) | Dos opciones nuevas: `baseUrl` (llamar a otra URL base) y `exposeDetailFor` (mostrar el `detail` de ciertos estados, como el 400). |
| `src/lib/useAssets.ts` | Hook que carga la lista de activos para los formularios, con estados de carga y error. |
| `src/lib/__tests__/inventory.test.ts` | Tests: cabecera `Authorization`, errores 400/422/500, red caída, 401 y `stockLevel`. |
| `src/app/(protected)/inventory/products/page.tsx` | Pantalla Activos: tabla, nivel de stock y botones de entrada/salida por fila. |
| `src/app/(protected)/inventory/orders/inbound/page.tsx` | Formulario de entrada. |
| `src/app/(protected)/inventory/orders/outbound/page.tsx` | Formulario de salida, con stock reactivo. |
| `src/app/(protected)/inventory/orders/page.tsx` | Historial de solo lectura. |
| `src/components/AssetSelect.tsx` | Desplegable de activos por nombre y SKU. |
| `src/components/StockBadge.tsx` | Etiqueta de nivel: icono + texto + color. |
| `src/components/LoadError.tsx` | Mensaje de error con botón «Reintentar». |
| `src/components/NavMenu.tsx` (modificado) | Enlaces de Inventario. |
| `src/app/globals.css` (modificado) | Estilos de las etiquetas. |
| `next.config.ts` (modificado) | Proxy `/api/inventory` de respaldo si no hay URL directa. |
| `jest.config.ts` (modificado) | Incluye `inventory.ts` en la cobertura. |
| `.env.example` | Documenta `NEXT_PUBLIC_INVENTORY_API_URL` sin valor. |

Rutas finales: `/inventory/products`, `/inventory/orders/inbound`, `/inventory/orders/outbound` y `/inventory/orders`. El backoffice no tiene `basePath`, por eso no llevan `/backoffice`.

## 3. El viaje de una petición: «Registrar salida»

1. **Componente** (`outbound/page.tsx`): al enviar, `validate()` comprueba en el navegador que la cantidad sea un entero mayor que 0 y que «Asignado a» esté relleno si es una asignación.
2. **`lib/inventory.ts`**: `createOutboundOrder(data)` prepara la llamada a `/inventory/orders/outbound` con la URL base de `NEXT_PUBLIC_INVENTORY_API_URL`.
3. **Cliente con token** (`apiClient.ts`): lee el token de `localStorage` y añade `Authorization: Bearer <token>`. Si la API responde 401, borra el token y manda a `/login`.
4. **FastAPI** (`routes/inventory.py`): comprueba el token, valida el cuerpo y saca el `user_uuid` del token, no del formulario.
5. **Supabase**: `create_exit` bloquea la fila del activo, calcula el stock (entradas − salidas) y, si alcanza, guarda la salida.
6. **Respuesta**: 201 con la orden, o 400 con el texto `Insufficient stock for asset '…'. Available: X, requested: Y.`.
7. **De vuelta**: el cliente devuelve la orden o lanza un `ApiError`. La pantalla muestra «Salida registrada…» y vuelve a pedir el stock, o muestra el mensaje del 400 junto al campo de cantidad.

## 4. Conceptos clave

- **Capa de integración.** Todo lo que sabe cómo hablar con la API vive en `lib/inventory.ts`. Si la API cambia, se toca un archivo. Ejemplo: `getProducts()` devuelve `Asset[]` ya tipado.
- **Por qué ningún componente hace `fetch`.** Si cada página llamara a `fetch`, cada una tendría que acordarse del token, del 401 y de los errores. Pasando todo por un único cliente, esas reglas se escriben una vez. Se comprueba con `git grep "fetch("`: no aparece en las vistas.
- **Estado reactivo.** En la salida, un `useEffect` depende de `assetId`: cuando cambias de activo vuelve a pedir `getProduct(id)` y actualiza el stock disponible. El `current = false` del final evita que una respuesta antigua pise a la nueva.
- **Validación en cliente vs regla real.** El aviso «Supera el stock disponible» es una ayuda: el stock puede haber cambiado desde que lo viste. La regla de verdad está en la API (400). Por eso el aviso no bloquea el envío y el 400 también se muestra.
- **Guard de rutas.** Las cuatro páginas están en la carpeta `(protected)`, cuyo `layout.tsx` envuelve todo en `AuthGuard`. Sin sesión válida, redirige a `/login`. No hubo que añadir nada por página.
- **Errores 400/401/500.**
  - 400: se muestra el texto de la API (opción `exposeDetailFor`).
  - 401: sesión caducada, se limpia el token y se va a `/login`.
  - 422: un mensaje por campo.
  - 500 o servidor caído: mensaje genérico legible, nunca el texto interno del servidor.
- **Cargando / vacío / error.** Cada pantalla de datos cubre los tres casos: «Cargando…» con spinner, «Todavía no hay…» si la lista está vacía y el error con «Reintentar». Nunca queda una pantalla en blanco.

## 5. Decisiones y por qué

- **Umbrales de stock.** El briefing no define ninguno. Elegí 0 = Agotado, 1–5 = Stock bajo y 6 o más = Saludable. Están en `LOW_STOCK_MAX` (`lib/inventory.ts`) y es fácil cambiarlos.
- **Etiqueta con icono y texto.** El color solo no basta para quien no distingue colores: ✖ Agotado, ▲ Stock bajo, ✔ Saludable.
- **Errores.** La API de inventario usa `detail` como texto (400, 404) o como lista (422). El cliente antiguo escondía los textos del servidor por seguridad; ahora cada llamada elige qué estados se muestran tal cual.
- **URL.** La URL directa sale de `NEXT_PUBLIC_INVENTORY_API_URL`. Con URL directa hace falta CORS; si la variable está vacía, se usa el proxy de Next (`/api/inventory`), que no lo necesita.
- **Oficina.** Cada activo pertenece a una oficina, así que el formulario la rellena sola (solo lectura) y no se puede contradecir.
- **Rutas.** Sin `basePath`, las URLs son `/inventory/...`.

## 6. Preguntas del instructor

1. **¿Por qué `current_stock` no se guarda?** Un número guardado puede desincronizarse del historial; uno calculado (entradas − salidas) siempre cuadra.
2. **¿Por qué avisas de stock insuficiente si la API ya lo rechaza?** Para ahorrar un viaje al usuario. Pero la regla real es la de la API, porque el stock puede cambiar entre que lo ves y que envías.
3. **¿Dónde se pone el `user_uuid`?** En el servidor, a partir del token. Si lo enviara el formulario, cualquiera podría firmar como otro.
4. **¿Qué pasa si caduca el token en mitad de una operación?** La API responde 401; el cliente borra el token y redirige a `/login`.
5. **¿Por qué ningún componente llama a `fetch`?** Para tener el token, los errores y la URL en un solo sitio y poder testearlos sin pantallas.

## 7. Glosario

- **Activo (`Asset`)**: equipo o material inventariado, con SKU único.
- **Entrada**: compra o entrega recibida; suma stock.
- **Salida**: asignación a un empleado o consumo; resta stock.
- **Asignación / Consumo**: los dos tipos de salida. La asignación exige «Asignado a».
- **SKU**: código único de un activo, por ejemplo `NXV-IT-001`.
- **Stock actual**: entradas menos salidas, calculado por la API.
- **Bearer token**: JWT que viaja en la cabecera `Authorization`.
- **CORS**: regla del navegador que decide qué orígenes pueden llamar a una API.
- **Guard**: componente que deja ver una página solo con sesión válida.
- **`user_uuid`**: id del usuario (de TinyDB) que registró la orden.
