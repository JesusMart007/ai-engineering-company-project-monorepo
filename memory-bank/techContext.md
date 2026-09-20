# Technical Context

## Tecnologías

- Node.js 24 y npm 11 disponibles en el entorno actual.
- TypeScript 5 con `strict` y resolución `NodeNext` en la raíz.
- Next.js 16, React 19, Tailwind CSS 4 y ESLint 9 en la UI existente.
- Python 3.12 para el backend.
- FastAPI, Uvicorn, Pydantic y pytest como stack previsto de `services/api`.

## Dependencias y workspace

- El paquete raíz coordina workspaces npm bajo `uis/*` y `packages/*`.
- `packages/shared` publica los contratos internos como `@repo/shared-types`.
- Cada UI conserva sus propios scripts `dev`, `lint`, `build` y `start`.
- La API mantiene dependencias Python y pruebas dentro de `services/api`.

## Scripts esperados

- `npm run typecheck`: valida el TypeScript raíz y los tipos compartidos.
- `npm run lint`: ejecuta el lint de las UIs.
- `npm run build`: construye las UIs.
- `npm run dev:website`, `npm run dev:backoffice` y `npm run dev:talent`: inician cada frontend.
- `npm run dev:api`: inicia FastAPI con recarga usando `.venv`.
- `npm run test:api`: ejecuta las pruebas del servicio usando `.venv`.

## Requisitos del entorno

- Instalar dependencias JavaScript con `npm install` desde la raíz.
- Crear un entorno virtual Python e instalar `services/api/requirements-dev.txt` antes de ejecutar o probar la API.
- Configurar secretos mediante variables de entorno; nunca versionarlos.
- Ejecutar lint, build, tipos y pruebas antes de integrar cambios.
