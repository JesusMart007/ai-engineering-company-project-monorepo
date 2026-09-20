# AgentHub Backoffice

Aplicación interna inicial para supervisión ejecutiva de KPIs, alertas y actividad operativa.

## Desarrollo

Desde la raíz del monorepo:

```bash
npm install
npm run dev:backoffice
```

Next.js usará `http://localhost:3000` o el siguiente puerto disponible.

## Verificación

```bash
npm run lint --workspace @nexova/backoffice
npm run build --workspace @nexova/backoffice
```