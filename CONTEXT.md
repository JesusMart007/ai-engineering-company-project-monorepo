# Contexto canónico de Nexova - AgentHub

Este documento es la fuente de verdad de negocio para el monorepo. Consolida el briefing de AgentHub, la selección de empresa y las restricciones vigentes del producto.

## Identidad de la empresa

Nexova Solutions es una consultora de recursos humanos y adquisición de talento que opera en Chile y Argentina. Cuenta con una base sólida de clientes, experiencia y reputación, pero todavía depende de procesos manuales que limitan la eficiencia, la visibilidad y la velocidad de decisión.

Las áreas iniciales de transformación son Marketing y Comunicación y Dirección Ejecutiva:

- Marketing produce contenido de forma manual y carece de visibilidad suficiente sobre las acciones que generan resultados.
- Dirección Ejecutiva depende de informes semanales preparados manualmente, con un coste operativo alto e información que puede quedar desactualizada.

## Producto: AgentHub

AgentHub es el producto de operaciones ejecutivas de Nexova. Centraliza indicadores operativos de departamentos clave y ofrece:

- Snapshots de KPIs por departamento.
- Alertas ejecutivas basadas en umbrales y rangos.
- Reportes ejecutivos semanales para dirección.
- Un dashboard ejecutivo unificado con datos actualizados.
- Una interfaz conversacional para consultar el estado del negocio en lenguaje natural.

El asistente recopilará información de las áreas de la empresa a través de sus sistemas y herramientas existentes, analizará tendencias, riesgos y oportunidades, y avisará cuando un KPI importante supere los umbrales definidos. Entre las consultas esperadas están "¿Qué departamento ha tenido el peor rendimiento esta semana?" y "¿Cómo evolucionaron las oportunidades comerciales durante el último mes?".

## Usuario administrador principal

- Nombre: Laura Mendoza.
- Rol: CEO.
- Objetivo principal: monitorear la salud del negocio, detectar cambios relevantes y anticipar riesgos con información actualizada.

También podrán participar directores de área y managers con permisos acordes a su rol.

## Departamentos base

- `sales`
- `recruiting`
- `training`
- `support`
- `hr`
- `marketing`

## Entidades canónicas

### AdministratorUser

- `id: string`
- `createdAt: string` (fecha-hora ISO)
- `updatedAt: string` (fecha-hora ISO)
- `fullName: string`
- `email: string`
- `role: "ceo" | "director" | "manager"`
- `darkModeEnabled: boolean`
- `activeSkills: string[]`

### KpiSnapshot

- `id: string`
- `createdAt: string` (fecha-hora ISO)
- `updatedAt: string` (fecha-hora ISO)
- `department: "sales" | "recruiting" | "training" | "support" | "hr" | "marketing"`
- `snapshotDate: string` (fecha ISO)
- `revenueUSD: number`
- `openRoles: number`
- `avgTimeToHireDays: number`
- `slaCompliancePct: number`
- `leadsGenerated: number`

### ExecutiveAlert

- `id: string`
- `createdAt: string` (fecha-hora ISO)
- `updatedAt: string` (fecha-hora ISO)
- `department: Department`
- `severity: "low" | "medium" | "high" | "critical"`
- `message: string`
- `detectedAt: string` (fecha-hora ISO)
- `resolvedAt?: string` (fecha-hora ISO)

### WeeklyExecutiveReport

- `id: string`
- `createdAt: string` (fecha-hora ISO)
- `updatedAt: string` (fecha-hora ISO)
- `periodStart: string` (fecha ISO)
- `periodEnd: string` (fecha ISO)
- `generatedAt: string` (fecha-hora ISO)
- `totalRevenueUSD: number`
- `departmentSnapshots: KpiSnapshot[]`
- `highPriorityAlerts: ExecutiveAlert[]`

## Reglas y restricciones de negocio

- Los campos obligatorios deben estar presentes antes de procesar o almacenar datos.
- `revenueUSD`: de 0 a 10.000.000 por snapshot.
- `openRoles`: de 0 a 10.000.
- `avgTimeToHireDays`: de 0 a 365.
- `slaCompliancePct`: de 0 a 100.
- `leadsGenerated`: de 0 a 1.000.000.
- `totalRevenueUSD`: de 0 a 100.000.000 por reporte semanal.
- Debe cumplirse `periodStart <= periodEnd <= generatedAt`.
- Debe cumplirse `detectedAt <= resolvedAt` cuando una alerta esté resuelta.
- Las interfaces deben ser accesibles, responsive y navegables por teclado.
- Las decisiones ejecutivas deben basarse en datos trazables; no se inventarán métricas ni fuentes.
- Los datos sensibles, credenciales y PII no se almacenarán en el repositorio.

## Operaciones requeridas

### Colecciones

- Filtrar colecciones por predicados.
- Ordenar colecciones en orden ascendente o descendente.
- Agrupar por categoría o departamento.
- Usar búsqueda lineal para arrays no ordenados.
- Usar búsqueda binaria para arrays ordenados.
- Manejar arrays vacíos y elementos no encontrados como comportamiento base.

### Transformaciones y agregaciones

- Conteo por categoría o departamento.
- Suma de valores numéricos.
- Cálculo de mínimos, máximos y promedios.
- Construcción de salidas ejecutivas tipadas.

## Restricciones técnicas vigentes

- Código TypeScript modular para utilidades y contratos compartidos.
- Tipado explícito en interfaces y firmas de funciones.
- Funciones pequeñas, con responsabilidad única y nombres descriptivos.
- Frontends y backend separados mediante contratos explícitos.
- Backend centralizado en FastAPI, organizado en capas y por dominios; no crear microservicios prematuramente.
- API versionada bajo `/api/v1`, con Pydantic para contratos de entrada y salida.
- Las UIs viven en `uis/`; los servicios y workers viven en `services/`.
- `agents/` y `skills/` contienen código de producto. `.agents/` contiene solamente configuración para asistentes de desarrollo.
- En el hito de prototipo visual definido por `SPECS.md`, la UI de referencia usa HTML semántico, Tailwind vía CDN, JavaScript vanilla, datos simulados y ninguna API real. Las aplicaciones posteriores pueden evolucionar el stack mediante una decisión de arquitectura documentada.

## Hoja de ruta del producto

1. **Fundación del monorepo:** contexto canónico, memory bank, protocolos para agentes, scripts reproducibles y límites claros entre configuración y producto.
2. **Superficie inicial:** sitio público, backoffice visible y API central con endpoint de salud.
3. **Operaciones ejecutivas:** dashboard de KPIs, alertas, actividad y acciones operativas para Laura Mendoza.
4. **Integración de datos:** conectar ventas, selección, formación, soporte, RR. HH. y marketing mediante contratos y pipelines trazables.
5. **Automatización:** generar reportes semanales y alertas configurables según umbrales.
6. **Asistente inteligente:** habilitar consultas en lenguaje natural respaldadas por datos actualizados y evaluaciones de calidad.
7. **Producción:** seguridad, observabilidad, pruebas, despliegue, recuperación y gobierno de datos.

## Criterios de éxito

- La dirección consulta la salud del negocio desde una única interfaz.
- Los indicadores y alertas respetan los rangos y reglas canónicas.
- Los reportes semanales reducen el trabajo manual y conservan trazabilidad.
- Las aplicaciones pueden ejecutarse y verificarse con comandos documentados.
- Cada nueva capacidad se ubica en la carpeta responsable y evita duplicación.
