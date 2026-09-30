# Nexova Website

Sitio público inicial de Nexova Solutions. Presenta la propuesta de valor, las áreas de servicio y AgentHub.

## Desarrollo

Desde la raíz del monorepo:

```bash
npm install
npm run dev:website
```

La aplicación estará disponible en `http://localhost:3000`.

## Verificación

```bash
npm run lint --workspace @nexova/website
npm run build --workspace @nexova/website
```