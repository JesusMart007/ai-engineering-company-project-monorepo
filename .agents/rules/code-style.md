# Code Style

## Principios generales

- Favorecer soluciones pequeñas, legibles y alineadas con patrones existentes.
- Mantener responsabilidades únicas y nombres descriptivos.
- Evitar abstracciones anticipadas, duplicación significativa y dependencias innecesarias.
- Tratar entradas externas como no confiables y validarlas en el límite del sistema.
- No registrar secretos, tokens, PII ni cuerpos completos con datos sensibles.

## TypeScript y React

- Mantener `strict` habilitado y evitar `any`; usar `unknown` con narrowing cuando el tipo sea incierto.
- Definir interfaces o tipos explícitos para contratos compartidos y firmas públicas.
- Preferir funciones puras para transformaciones y agregaciones.
- Usar componentes funcionales y Server Components por defecto en Next.js.
- Añadir estado cliente solo cuando exista interacción real.
- Usar HTML semántico, etiquetas accesibles, foco visible y navegación por teclado.
- No duplicar contratos compartidos; promoverlos a `packages/` cuando tengan dos o más consumidores.

## Python y FastAPI

- Usar type hints en funciones públicas y modelos Pydantic en límites HTTP.
- Mantener routers delgados y lógica de negocio en services.
- Separar persistencia mediante repositories cuando se incorpore una base de datos.
- Usar nombres `snake_case`, imports explícitos y módulos pequeños.
- Devolver errores HTTP intencionales sin filtrar detalles internos.

## Formato y calidad

- Respetar la configuración local de ESLint, TypeScript y las herramientas Python del servicio.
- Añadir pruebas para comportamiento nuevo y regresiones.
- No silenciar reglas de lint o tipos sin justificar la excepción localmente.
- Mantener README y comandos de ejecución actualizados.
