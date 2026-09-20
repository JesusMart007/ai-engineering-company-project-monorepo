# Deployment Preflight

## Objetivo claro

Verificar que una aplicación o servicio del monorepo está listo para integrarse o desplegarse, con evidencia reproducible y sin modificar el entorno de producción.

## Inputs requeridos

- Ruta del componente objetivo.
- Entorno de destino: local, preview, staging o producción.
- Referencia o rama que se desea verificar.
- Lista de variables de entorno requeridas, indicando solo sus nombres.
- Comandos de build, lint, tipos y pruebas declarados por el componente.

Si falta un input o existen instrucciones contradictorias, detenerse y preguntar. Nunca solicitar ni imprimir valores secretos.

## Pasos de ejecución y reglas

1. Leer `CONTEXT.md`, `memory-bank/` y el README del componente.
2. Revisar el estado Git y separar cambios relacionados de cambios ajenos.
3. Confirmar que las dependencias y versiones requeridas están documentadas.
4. Verificar que cada variable requerida está definida por nombre, sin mostrar su valor.
5. Ejecutar la comprobación más específica primero y detener la secuencia ante errores atribuibles al cambio.
6. Ejecutar typecheck, lint, pruebas y build aplicables usando scripts del repositorio.
7. Para servicios HTTP, comprobar el endpoint de salud y que no exponga datos sensibles.
8. Revisar que no haya secretos, PII, artefactos generados o logs de depuración en el diff.
9. Registrar comandos, resultado y riesgos pendientes; no desplegar ni crear commits salvo petición explícita.

## Output esperado

Un informe breve con:

- Componente y referencia verificados.
- Entorno objetivo.
- Tabla de checks con comando y estado `PASS`, `FAIL` o `SKIP` justificado.
- Bloqueadores y riesgos residuales.
- Veredicto final: `READY` o `NOT READY`.

## Criterios de aceptación y verificación

- `npm run typecheck` finaliza con código 0 cuando aplica.
- `npm run lint` finaliza con código 0 cuando aplica.
- `npm run build` finaliza con código 0 cuando aplica.
- `npm run test:api` finaliza con código 0 para `services/api`.
- El endpoint `GET /api/v1/health` responde HTTP 200 con un estado saludable cuando el API forma parte del alcance.
- No existen secretos o PII añadidos al control de versiones.
- El informe incluye toda omisión con una razón verificable.

La skill solo devuelve `READY` cuando todos los checks obligatorios aplicables pasan.