# Git Workflow

## Ramas

- Partir de una rama actualizada y usar ramas cortas con propósito único.
- Formato recomendado: `feat/<alcance>`, `fix/<alcance>`, `docs/<alcance>` o `chore/<alcance>`.
- No mezclar refactors o formateo no relacionados con el objetivo de la rama.
- No reescribir historia compartida ni forzar pushes sin autorización explícita.

## Commits

Usar Conventional Commits:

```text
<tipo>(<alcance opcional>): <descripción imperativa>
```

Tipos admitidos: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore` y `revert`.

- Mantener cada commit enfocado y ejecutable.
- Explicar en el cuerpo el motivo y los efectos incompatibles cuando existan.
- Marcar cambios incompatibles con `!` y un pie `BREAKING CHANGE:`.
- No incluir secretos, credenciales, PII, dependencias vendorizadas ni artefactos generados.

## Pull requests

- Describir problema, solución, alcance fuera de la PR y riesgos.
- Enumerar las verificaciones ejecutadas y sus resultados.
- Incluir capturas para cambios visuales relevantes.
- Mantener la PR pequeña; dividir cambios independientes.
- Requerir revisión para contratos compartidos, seguridad, datos, infraestructura y arquitectura.
- Resolver conversaciones con evidencia del cambio o una decisión documentada.
- Integrar solo con lint, tipos, builds y pruebas aplicables en verde.
