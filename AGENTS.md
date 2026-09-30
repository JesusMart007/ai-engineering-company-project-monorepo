# Protocolo global para agentes

Estas instrucciones aplican a todo el repositorio. Un `AGENTS.md` más cercano puede añadir reglas específicas, pero no puede contradecir las restricciones de negocio de `CONTEXT.md`.

## Inicio obligatorio de sesión

Antes de proponer o modificar código:

1. Leer `CONTEXT.md` completo.
2. Leer los cinco archivos de `memory-bank/`.
3. Leer el README de cada carpeta que vaya a modificarse.
4. Revisar el estado Git y preservar cambios ajenos.
5. Confirmar si existe un `AGENTS.md` más cercano al archivo objetivo.

## Límites del repositorio

- `.agents/` configura asistentes de desarrollo como Cursor, Windsurf o Claude Code.
- `agents/` contiene agentes de IA que forman parte del producto.
- `skills/` contiene capacidades reutilizables de los agentes del producto.
- No copiar reglas de `.agents/` a `agents/` o `skills/`, ni importar lógica de producto desde `.agents/`.
- Cada app o servicio nuevo debe vivir en una subcarpeta propia y documentar propósito, instalación, ejecución y verificación.

## Flujo de trabajo

1. Identificar la fuente de verdad y el componente propietario del comportamiento.
2. Formular una hipótesis verificable y realizar el cambio mínimo necesario.
3. Ejecutar primero la comprobación más específica del componente modificado.
4. Ejecutar las verificaciones globales aplicables antes de integrar.
5. Actualizar `memory-bank/activeContext.md` cuando cambie el foco o una decisión activa.
6. Actualizar `memory-bank/progress.md` con trabajo completado, validaciones y próximos pasos.

## Checks pre-commit obligatorios

Desde la raíz, ejecutar cuando corresponda:

```bash
npm run typecheck
npm run lint
npm run build
npm run test:api
```

Además:

- Revisar que no se hayan incluido secretos, PII, artefactos de build ni cambios no relacionados.
- Confirmar que la documentación y el memory bank reflejan las decisiones vigentes.
- Usar Conventional Commits según `.agents/rules/git-workflow.md`.
- No crear commits ni publicar ramas sin una petición explícita del usuario.

## Stop-and-ask

Detenerse y solicitar confirmación antes de continuar cuando:

- Existan fuentes de verdad contradictorias sobre negocio o arquitectura.
- El cambio requiera borrar, mover o reemplazar datos o archivos existentes.
- Haya que elegir entre límites de dominio plausibles sin una decisión registrada.
- Se proponga introducir un framework, servicio externo, proveedor de IA o almacenamiento nuevo.
- El cambio altere contratos públicos, autenticación, permisos, tratamiento de PII o despliegue.
- Las pruebas fallen por causas ajenas al cambio y oculten su validez.

Documentar la decisión acordada en `memory-bank/activeContext.md` o en un ADR bajo `docs/` cuando tenga impacto duradero.
