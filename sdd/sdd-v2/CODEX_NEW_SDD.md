# CODEX_NEW_SDD

Fecha: 2026-04-02

## Índice

1. Resumen ejecutivo
2. Fuentes analizadas
3. Qué define realmente el SDD relevado
4. Cómo funciona hoy `agents-plan-v1`
5. Comparativa estructural y operativa
6. Qué está bien en tu v1 y qué no alcanza
7. Recomendación central: skills vs agents
8. Arquitectura objetivo para un nuevo SDD profesional
9. Objetivos soportados y modos de profundidad
10. Guardrails, validaciones y puntos de confirmación
11. Persistencia, artefactos y contexto de proyecto
12. Breaking changes respecto de `agents-plan-v1`
13. Roadmap de migración recomendado
14. Decisiones recomendadas
15. Resumen final

---

## 1. Resumen ejecutivo

El relevamiento de `orchestrator-skills-deep-dive.md` describe un sistema SDD bastante más formal y profesional que `agents-plan-v1`.

La diferencia principal no es "más agentes" ni "más prompts". La diferencia real es esta:

- el SDD relevado separa claramente **orquestación**, **fases**, **artefactos**, **persistencia**, **estándares del proyecto** y **cierre auditable**
- tu v1 resuelve bien **control operativo**, **interacción con el usuario**, **stage execution** y **quality gate incremental**
- pero tu v1 todavía concentra demasiado en dos artefactos (`SURVEY` y `PLAN`) y no llega a un SDD formal completo

Lectura sintética:

- `agents-plan-v1` es un muy buen **motor operativo**
- Agent Teams Lite aporta un mejor **modelo de sistema**
- la mejor v2 no debería copiar ATL literal ni descartar tu v1
- la mejor v2 debería tomar la disciplina operativa de tu v1 y montarla sobre un SDD más formal, con skills, contratos compartidos, `skill-registry`, artefactos por fase y `verify/archive` serios

Estimación global:

- alineación conceptual de tu v1 con SDD: **65%**
- alineación estructural/operativa real con SDD: **40%**

Mi recomendación fuerte es:

- usar **un único orquestador principal**
- modelar los subagentes como **skills canónicas por fase**
- usar **wrappers/agents host-specific** solo cuando el host lo requiera
- estandarizar **skills, prompts, contratos, artefactos y documentación del sistema en inglés**
- mantener dos capas de QA:
  - `stage-qa` incremental
  - `sdd-verify` final y obligatorio
- mantener `SURVEY` y `PLAN` solo como vistas derivadas o exportables, no como source of truth principal

---

## 2. Fuentes analizadas

### Material tuyo

- `sdd/sdd-v1/orchestrator-skills-deep-dive.md`
- `sdd/sdd-v1/agents-plan-v1-vs-sdd-deep-dive.md`
- `agents/agents-plan-v1/README.md`
- `agents/agents-plan-v1/technical-orchestrator.agent.md`
- `agents/agents-plan-v1/structure-scanner.agent.md`
- `agents/agents-plan-v1/deep-context-analyzer.agent.md`
- `agents/agents-plan-v1/survey-generator.agent.md`
- `agents/agents-plan-v1/strategic-planner.agent.md`
- `agents/agents-plan-v1/stage-executor.agent.md`
- `agents/agents-plan-v1/qa-validator.agent.md`

### Material SDD / Agent Teams Lite

- `AI/agent-teams-lite/docs/orchestrator-skills-deep-dive.md`
- `AI/agent-teams-lite/docs/architecture.md`
- `AI/agent-teams-lite/docs/sub-agents.md`
- `AI/agent-teams-lite/docs/persistence.md`
- `AI/agent-teams-lite/docs/token-economics.md`
- `AI/agent-teams-lite/examples/codex/agents.md`
- `AI/agent-teams-lite/skills/_shared/*.md`
- `AI/agent-teams-lite/skills/skill-registry/SKILL.md`
- `AI/agent-teams-lite/skills/sdd-*/SKILL.md`

---

## 3. Qué define realmente el SDD relevado

## 3.1 Naturaleza del sistema

El SDD relevado no es un runtime backend de agentes. Es un **pack de distribución e integración** que aporta:

- skills por fase
- prompt/regla del orquestador
- contratos compartidos
- persistencia por artefactos
- `skill-registry`
- ejemplos/adaptadores por host

El host AI ejecuta. El repo define comportamiento, contratos y estructura.

## 3.2 Principio rector

La regla maestra del orquestador es:

- si la tarea infla contexto sin necesidad, se delega

Eso implica un orquestador **delgado, no dogmático**:

| Caso | Inline | Delegado |
|---|---|---|
| leer 1-3 archivos para decidir algo | sí | opcional |
| explorar 4+ archivos para entender un problema | no | sí |
| leer como preparación para escribir | no | sí |
| cambio mecánico de un archivo | sí | opcional |
| cambio multiarchivo o con lógica nueva | no | sí |
| tests/build/install | no | sí |

## 3.3 Pipeline SDD real

El flujo SDD relevado es:

`init -> explore -> propose -> spec/design -> tasks -> apply -> verify -> archive`

Notas importantes:

- `spec` y `design` pueden correr en paralelo después de `proposal`
- cada fase produce un artefacto concreto
- las fases downstream leen artefactos, no dependen de memoria del chat

## 3.4 Componentes no negociables del modelo

| Componente | Propósito | Valor real |
|---|---|---|
| `sdd-init` | bootstrap de proyecto y persistencia | inicializa contexto y registry |
| `skill-registry` | resolver skills y convenciones una vez | baja tokens y evita redescubrimiento |
| compact rules | inyectar estándares resumidos | hace delegación barata y consistente |
| `_shared` contracts | protocolizar comportamiento de todas las fases | evita prompts divergentes |
| `sdd-verify` | validación con evidencia ejecutada | evita falso cierre |
| `sdd-archive` | cierre y auditoría | deja trazabilidad formal |
| `engram/openspec/hybrid/none` | estrategia de persistencia | recuperación y portabilidad |

## 3.5 Lo más valioso del modelo relevado

Lo más fuerte del sistema no es el DAG. Es la combinación de:

- artefactos explícitos
- skill registry
- compact rules
- contratos compartidos
- verify con evidencia real
- archive como fase obligatoria

Eso es lo que vuelve al sistema realmente reusable y profesional.

---

## 4. Cómo funciona hoy `agents-plan-v1`

## 4.1 Topología actual

Tu v1 tiene:

- `technical-orchestrator`
- `structure-scanner`
- `deep-context-analyzer`
- `survey-generator`
- `strategic-planner`
- `stage-executor`
- `qa-validator`

## 4.2 Flujo operativo actual

Flujo real:

1. Phase 0: detectar stack, docs y `project_context`
2. Phase 1: `structure-scanner` + `deep-context-analyzer`
3. Phase 2: `survey-generator` produce `SURVEY_[Topic].md`
4. Phase 3: `strategic-planner` produce `PLAN_[Topic].md`
5. Phase 4: loop `stage-executor` + `qa-validator`

## 4.3 Virtudes reales de la v1

Tu v1 hace varias cosas muy bien:

- separación de responsabilidades bastante clara
- interacción con el usuario muy controlada
- aprobaciones explícitas antes de avanzar
- source of truth fuera del chat
- `project_context` explícito
- purga de contexto entre fases
- snapshot/checkpoint antes de tocar código
- triggers de escalado concretos
- QA incremental inmediato después de ejecutar

## 4.4 Debilidad conceptual principal

Tu v1 no es un SDD completo.

Hoy expresa mejor este modelo:

- discovery
- consolidación
- planificación
- ejecución iterativa
- QA incremental

Eso sirve. Pero es más corto que un SDD formal.

---

## 5. Comparativa estructural y operativa

## 5.1 Mapeo directo

| SDD relevado | Equivalente v1 | Estado |
|---|---|---|
| `sdd-init` | Phase 0 | parcial |
| `sdd-explore` | `structure-scanner` + `deep-context-analyzer` | parcial |
| `sdd-propose` | no existe | faltante |
| `sdd-spec` | no existe | faltante |
| `sdd-design` | parcialmente dentro de `strategic-planner` | parcial |
| `sdd-tasks` | parcialmente dentro de `PLAN` | parcial |
| `sdd-apply` | `stage-executor` | parcial |
| `sdd-verify` | `qa-validator` | parcial y más débil |
| `sdd-archive` | no existe | faltante |
| `skill-registry` | no existe | faltante |
| compact rules | no existe | faltante |
| `_shared` contracts | JSON por agente, pero no shared formal | parcial |
| persistencia declarativa | `SURVEY`/`PLAN` + `docs/temp` | parcial y ad hoc |

## 5.2 Diferencias de fondo

### A. Artefactos

SDD separa:

- propuesta
- especificación
- diseño
- tareas
- implementación
- verificación
- archivo

Tu v1 concentra demasiado en:

- `SURVEY`
- `PLAN`

Efecto:

- menor trazabilidad
- menor precisión contractual
- menor contexto formal para el ejecutor

### B. Skill system

ATL está pensado como:

- skills por fase
- shared contracts
- registry
- compact rules
- adaptadores por host

Tu v1 hoy es:

- bundle de prompts/agentes especializados
- sin `SKILL.md` por fase
- sin `_shared`
- sin registry
- sin packaging reusable

### C. Verificación

ATL exige:

- tests ejecutados
- build/type-check si aplica
- compliance matrix contra spec
- verify-report formal

Tu v1 tiene QA incremental útil, pero no un `verify` integral del cambio.

### D. Cierre

ATL cierra con `archive`.

Tu v1 termina cuando el plan queda en `Done` y QA no bloquea. Falta:

- cierre formal del change
- consolidación de specs
- carpeta/history de archivado
- auditoría limpia

### E. Contexto y estándares del proyecto

ATL resuelve una vez:

- skills relevantes
- convenciones del repo
- compact rules

Tu v1 comparte `project_context`, pero eso solo cubre:

- package manager
- lenguaje
- framework
- bundler
- runner
- docs dir

Faltan:

- reglas de arquitectura
- estilo de implementación
- restricciones por framework
- convenciones locales del proyecto

---

## 6. Qué está bien en tu v1 y qué no alcanza

## 6.1 Qué conviene conservar casi textual

### Del orquestador

- Phase 0 de detección inicial
- control explícito de fases
- respuestas sintetizadas
- aprobación del usuario antes de avanzar
- purga de contexto entre fases

### Del ejecutor

- checkpoint/snapshot previo
- verificación de precondiciones
- detección de side effects fuera de scope
- no auto-advance

### Del QA

- quality gate incremental
- validación runtime con confirmación del usuario
- clasificación `approved/warning/rejected`

### De la interacción

- preguntas cerradas con opciones
- escalado cuando hay ambigüedad real
- no asumir cuando el riesgo es alto

## 6.2 Qué no alcanza para un SDD profesional

### A. `SURVEY` y `PLAN` están sobrecargados

Problema:

- `SURVEY` mezcla exploración, hallazgos, restricciones y parte de la intención del cambio
- `PLAN` mezcla diseño técnico, estrategia y checklist

Consecuencia:

- revisión más difícil
- apply subalimentado
- verify sin contrato claro

### B. `stage-executor` está subespecificado

Hoy lee:

- `PLAN`
- código actual

Debería leer:

- `proposal`
- `spec`
- `design`
- `tasks`
- estándares del proyecto

### C. `qa-validator` no reemplaza `sdd-verify`

Debe quedar como QA incremental. No como único quality gate.

### D. Persistencia demasiado lateral

`docs/temp/[agent]-context.md` es útil como cache auxiliar. No como backbone del sistema.

### E. Inconsistencias internas

Casos claros detectados:

- `strategic-planner` fuerza `pnpm`, contradiciendo `project_context`
- el orquestador declara delegación absoluta, pero Phase 0 ya rompe esa regla
- naming/packaging todavía no expresan bien la diferencia entre coordinador, ejecutores y soporte

---

## 7. Recomendación central: skills vs agents

## 7.1 Respuesta corta

Para los subagentes, **sí: es mejor skills que agents** como modelo canónico.

## 7.2 Por qué

### Skills

Ventajas:

- son portables entre hosts
- son versionables como contrato
- permiten `_shared`
- permiten registry y compact rules
- separan conocimiento de ejecución host-specific
- reducen drift entre implementaciones

Desventajas:

- si el host necesita aislamiento de tools/model, igual hay que envolverlas

### Agents

Ventajas:

- permiten restricciones concretas de tools/model
- sirven como wrappers operativos del host
- mejoran UX si el host soporta subagentes nativos

Desventajas:

- tienden a duplicar lógica
- generan drift entre hosts
- son peor source of truth semántico que una skill bien definida

## 7.3 Recomendación práctica

Modelo recomendado:

- **source of truth funcional**: `SKILL.md` por fase
- **source of truth de orquestación**: `SDD-ORCHESTRATOR.md`
- **wrappers host-specific**: agentes/reglas livianas que llaman a esas skills o siguen esos contratos

En otras palabras:

- skills primero
- agents como adaptadores

Esto te deja:

- reutilización
- menor mantenimiento
- más compatibilidad con `.claude`, `.codex`, `.cursor`, etc.

---

## 8. Arquitectura objetivo para un nuevo SDD profesional

## 8.1 Principios de diseño

1. El orquestador coordina; no ejecuta trabajo pesado.
2. Cada skill de fase tiene una responsabilidad única.
3. El estado vive en artefactos y estado persistido, no en memoria del chat.
4. La delegación es selectiva, no absoluta.
5. Los estándares del proyecto se resuelven una vez y luego se inyectan como compact rules.
6. Ningún cambio se considera cerrado sin verify y archive.
7. La interacción con el usuario debe ser directa, breve y relevante.

## 8.2 Topología recomendada

### Orquestador principal

- `sdd-orchestrator`

Responsabilidades:

- detectar objetivo y modo
- iniciar `sdd-init` si falta bootstrap
- resolver `skill-registry`
- decidir inline vs delegar
- lanzar la fase correcta
- pasar referencias a artefactos y compact rules
- resumir resultados
- pedir aprobación en checkpoints clave

### Skills core

- `sdd-init`
- `sdd-explore`
- `sdd-propose`
- `sdd-spec`
- `sdd-design`
- `sdd-tasks`
- `sdd-apply`
- `sdd-verify`
- `sdd-archive`

### Skills soporte

- `skill-registry`
- `project-map-init`
- `stage-qa`
- `git-checkpoint`
- `judgment-day` o review profunda opcional
- `branch-pr`
- `issue-creation`

## 8.3 Reutilización directa desde tu v1

| Pieza v1 | Destino recomendado |
|---|---|
| Phase 0 | `sdd-init` |
| `structure-scanner` | backend operativo de `sdd-explore` |
| `deep-context-analyzer` | backend operativo de `sdd-explore` |
| `survey-generator` | writer auxiliar para resúmenes ejecutivos |
| `strategic-planner` | split en `sdd-propose`, `sdd-design`, `sdd-tasks` |
| `stage-executor` | núcleo de `sdd-apply` |
| `qa-validator` | `stage-qa` incremental |

## 8.4 Estructura de carpetas recomendada

```text
sdd/
  orchestrator/
    SDD-ORCHESTRATOR.md
  skills/
    _shared/
      sdd-phase-common.md
      artifact-contract.md
      persistence-contract.md
      skill-resolver.md
      openspec-convention.md
      project-standards-contract.md
    skill-registry/
      SKILL.md
    project-map-init/
      SKILL.md
    sdd-init/
      SKILL.md
    sdd-explore/
      SKILL.md
    sdd-propose/
      SKILL.md
    sdd-spec/
      SKILL.md
    sdd-design/
      SKILL.md
    sdd-tasks/
      SKILL.md
    sdd-apply/
      SKILL.md
    stage-qa/
      SKILL.md
    sdd-verify/
      SKILL.md
    sdd-archive/
      SKILL.md
  examples/
    codex/
    claude/
    cursor/
    opencode/
  scripts/
    install.sh
    setup.sh
```

## 8.5 Envelope común recomendado

Todas las fases deberían devolver el mismo contrato:

| Campo | Uso |
|---|---|
| `status` | `success`, `partial`, `blocked` |
| `executive_summary` | resumen corto para el orquestador |
| `artifacts` | paths/topic_keys escritos o actualizados |
| `next_recommended` | siguiente fase sugerida |
| `risks` | riesgos detectados |
| `skill_resolution` | `injected`, `fallback-registry`, `fallback-path`, `none` |

Sin esto, el orquestador termina parseando respuestas heterogéneas y se degrada.

---

## 9. Objetivos soportados y modos de profundidad

## 9.1 Recomendación de producto

No recomiendo varios orquestadores como punto de partida.

Recomiendo:

- **un único orquestador**
- con **router de objetivo**
- y **modos de profundidad**

Eso baja mantenimiento y evita drift.

Si querés UX separada, podés agregar aliases o comandos, pero que apunten al mismo núcleo.

## 9.2 Objetivos soportados

| Objetivo | Flujo recomendado | Notas |
|---|---|---|
| nueva feature | `init -> explore -> propose -> spec/design -> tasks -> apply -> verify -> archive` | flujo completo por defecto |
| bug fix | `init -> explore -> propose -> spec -> design? -> tasks -> apply -> verify -> archive` | `design` opcional si el fix es simple |
| planificador | `init -> explore -> propose -> spec/design -> tasks` | se detiene antes de apply |
| rework/refactor | `init -> explore -> propose -> spec -> design -> tasks -> apply -> verify -> archive` | spec debe enfatizar comportamiento preservado |
| auditoría/relevamiento | `init -> explore -> propose?` | sin apply |
| otros workflows reutilizables | usar `explore`, `propose`, `tasks`, `stage-qa`, `verify` según caso | no todo requiere el DAG completo |

## 9.3 Modos de profundidad

### `lite`

Para:

- cambios chicos
- decisiones tácticas
- relevamientos acotados

Comportamiento:

- menos artefactos o artefactos mínimos
- verify acotado
- menos pasos de confirmación
- no usar para refactors riesgosos ni bugs ambiguos

### `standard`

Debe ser el default.

Comportamiento:

- pipeline formal
- artefactos por fase
- QA incremental + verify final
- checkpoints normales

### `deep`

Para:

- cambios grandes
- alta ambigüedad
- riesgo de regresión
- impacto transversal

Comportamiento:

- exploración más profunda
- más validaciones
- comparación de alternativas
- posibilidad de `judgment-day`
- confirmaciones adicionales antes de cerrar fases críticas

## 9.4 Cómo decidir el modo

Recomendación:

- el orquestador propone el modo
- el usuario confirma o cambia

Heurística útil:

| Señal | Modo sugerido |
|---|---|
| 1 archivo, cambio mecánico | `lite` |
| feature o fix localizado | `standard` |
| módulo nuevo, rework grande, bug difícil, blast radius alto | `deep` |

---

## 10. Guardrails, validaciones y puntos de confirmación

## 10.1 Guardrails no negociables

1. No ejecutar `apply` serio sin `proposal`.
2. No considerar un cambio cerrado sin `verify`.
3. No correr `archive` con issues críticas abiertas.
4. No pasar cuerpos completos de artefactos largos si alcanza con referencias.
5. No hardcodear package manager, framework o runner.
6. No usar `docs/temp/*` como source of truth principal.
7. No permitir que cada skill invente su propio envelope.
8. No dejar que el orquestador relea medio repo inline si eso infla contexto.

## 10.2 Confirmaciones que sí conviene pedir

El sistema debe ser cauteloso, no histérico.

Pedir confirmación cuando:

- se va a crear estructura persistente (`openspec/`, `.atl/`, project map)
- hay múltiples enfoques válidos con trade-offs reales
- se detecta blast radius mayor al esperado
- hay que ejecutar comandos potencialmente costosos o invasivos
- se va a pasar de planificación a implementación
- se cierra un batch de apply y se propone continuar
- se va a archivar el cambio

No pedir confirmación para:

- lectura de archivos
- búsquedas internas
- resumen intermedio
- cambios triviales ya autorizados dentro del batch
- reintento inmediato de un test ya aprobado

## 10.3 Checkpoints recomendados

| Momento | Qué se resume | Qué se pregunta |
|---|---|---|
| después de `init` | stack, docs, persistencia, paths | confirmar contexto y storage |
| después de `explore` | hallazgos, alcance, riesgos | confirmar que se formaliza el change |
| después de `proposal` | scope, rollback, criterio de éxito | confirmar rumbo |
| después de `spec/design` | comportamiento esperado y enfoque técnico | validar antes de tareas |
| antes de `apply` | batch, archivos, impacto esperado | aprobar ejecución |
| después de `stage-qa` | estado del batch y alertas | continuar, revisar o corregir |
| antes de `archive` | verify verdict y riesgos restantes | cerrar o reabrir |

## 10.4 Validaciones internas por fase

| Fase | Validación mínima |
|---|---|
| `sdd-init` | stack detectado, path válido, registry generado |
| `sdd-explore` | archivos relevantes leídos, riesgos explicitados |
| `sdd-propose` | scope claro, rollback plan, success criteria |
| `sdd-spec` | requisitos y escenarios testeables |
| `sdd-design` | decisiones con rationale y file changes concretos |
| `sdd-tasks` | tareas chicas, verificables y ordenadas por dependencia |
| `sdd-apply` | checkpoint, precondiciones, impacto, progreso |
| `stage-qa` | smoke/regression del batch |
| `sdd-verify` | tests/build/type-check/compliance matrix |
| `sdd-archive` | verify ok, merge de specs, estado archivado |

## 10.5 Contrato de interacción con el usuario

La interacción no debería depender del estilo del prompt de turno. Debería tener un contrato estable.

Reglas recomendadas:

1. En cada checkpoint hacer **1 a 3 preguntas máximo**.
2. Ofrecer **2 o 3 opciones claras** y permitir siempre un campo libre.
3. Agrupar decisiones relacionadas en una sola interacción.
4. No preguntar lo que el sistema puede descubrir leyendo el proyecto.
5. Registrar la decisión del usuario en `state.yaml`, `proposal`, `design` o `tasks` según corresponda.

Formato sugerido:

| Tipo de checkpoint | Formato recomendado |
|---|---|
| elección de objetivo | opciones + campo libre |
| elección de modo (`lite/standard/deep`) | recomendación explícita + override |
| conflicto técnico | mini tabla de trade-offs + opción |
| aprobación de ejecución | resumen de batch + aprobar/pausar/replanificar |
| cierre de iteración | resumen de verify/stage-qa + continuar/corregir/cerrar |

## 10.6 Política de idioma

Recomendación fuerte:

- todo el **sistema interno** debe estar en **inglés**
- la **interacción con el usuario** debe estar en el idioma inferido de la conversación

### Qué debe quedar en inglés

- `SKILL.md`
- `_shared` contracts
- prompts del orquestador
- templates de artefactos
- `proposal`, `spec`, `design`, `tasks`, `verify-report`, `archive-report`
- `PROJECT_SDD_CONTEXT.md` o el project map equivalente
- `SURVEY` y `PLAN` si se mantienen como vistas derivadas
- nombres de campos, envelopes, estados, labels internas y keys persistidas

Esto conviene por tres razones:

- reduce drift semántico entre hosts
- simplifica mantenimiento y reutilización
- evita mezclar contratos técnicos con localización de UX

### Qué sí puede variar por idioma

- mensajes del orquestador al usuario
- resúmenes de checkpoint
- preguntas de confirmación
- selectores interactivos y microformularios

### Regla operativa

- artefactos y contratos: **siempre en inglés**
- capa conversacional: **idioma inferido del usuario**

## 10.7 Cuándo preguntar y cuándo no

### Sí preguntar

- si la decisión cambia arquitectura, API, persistencia o blast radius
- si hay contradicción entre artefactos
- si el costo de equivocarse es alto
- si el sistema detecta dos caminos razonables con trade-offs distintos

### No preguntar

- si el dato ya está en `docs/`, `openspec/`, `project map` o `skill-registry`
- si la acción es exploratoria y read-only
- si el cambio es mecánico y ya estaba aprobado dentro del batch

## 10.8 Inicio de conversación e inferencia de idioma

Al iniciar una conversación nueva, el sistema debería resolver idioma antes de avanzar con el workflow.

Orden recomendado:

1. Si el primer mensaje del usuario está claramente en español, usar `es`.
2. Si el primer mensaje del usuario está claramente en inglés, usar `en`.
3. Si el primer mensaje no existe, está vacío o el idioma no se puede inferir con confianza, pedir selección explícita.

Selector interactivo recomendado:

- `Español`
- `English`

Reglas:

- guardar la selección en el estado de sesión
- reutilizarla durante toda la conversación
- si luego el usuario cambia claramente de idioma, el orquestador puede adaptarse en la conversación, pero **sin cambiar el idioma de los artefactos**, que siguen en inglés
- si hay reanudación de sesión, restaurar primero el idioma previo; si no existe, volver a inferir o preguntar

Implementación UX recomendada:

- no hacer una pregunta abierta
- usar un select simple `es/en`
- mostrarlo solo cuando realmente no se puede inferir

---

## 11. Persistencia, artefactos y contexto de proyecto

## 11.1 Modo de persistencia recomendado

Para una versión profesional:

- `openspec` si querés todo versionable y humano
- `hybrid` si además tenés memoria tipo Engram y te sirve recovery cross-session

No usaría `none` como default productivo.

## 11.2 Layout de artefactos recomendado

```text
openspec/
  config.yaml
  specs/
    {domain}/spec.md
  changes/
    {change-name}/
      state.yaml
      exploration.md
      proposal.md
      specs/
        {domain}/spec.md
      design.md
      tasks.md
      verify-report.md
    archive/
      YYYY-MM-DD-{change-name}/
```

## 11.3 Qué hacer con `SURVEY` y `PLAN`

Recomendación:

- mantenerlos, pero como **artefactos derivados**

Mapa recomendado:

| Documento v1 | Nuevo rol |
|---|---|
| `SURVEY_[Topic].md` | vista ejecutiva de `explore + proposal` |
| `PLAN_[Topic].md` | vista ejecutiva de `design + tasks` |

Eso preserva UX sin volver a mezclar el source of truth.

## 11.4 Skill de inicialización de contexto de proyecto

Tu requerimiento acá es correcto y conviene incorporarlo.

Sugiero una skill extra:

- `project-map-init`

Objetivo:

- generar un mapa simple y reusable del proyecto para guiar al orquestador

Contenido mínimo:

- stack
- package manager
- test runner
- arquitectura percibida
- carpetas importantes
- docs relevantes
- convenciones detectadas
- dónde buscar backend, frontend, tests, config y scripts
- notas de riesgos o rarezas del repo

Salida recomendada:

- preguntar al usuario dónde guardarlo
- sugerir opciones

Opciones sugeridas:

- `docs/ai/PROJECT_SDD_CONTEXT.md`
- `.sdd/project-map.md`
- `docs/context/AI_PROJECT_MAP.md`

Mi recomendación:

- no guardarlo dentro de `.claude` o `.codex` como fuente principal del proyecto
- sí podés tener adaptadores host-specific ahí
- pero el **mapa del proyecto** debería vivir en una ruta neutral y versionable del repo

## 11.5 `skill-registry` y compact rules

Esto debería existir desde la primera iteración seria.

Sin registry:

- el orquestador depende demasiado de lo que recuerde
- cada delegado redescubre reglas
- se desperdician tokens
- hay más drift

Con registry:

- resolvés una vez skills y convenciones
- inyectás compact rules en cada fase
- el sistema se vuelve más consistente y más barato

## 11.6 Escalera de contexto recomendada

El orquestador debería usar siempre esta prioridad para juntar contexto:

1. `openspec/config.yaml` o estado persistido equivalente
2. `project-map-init` / `PROJECT_SDD_CONTEXT.md`
3. `skill-registry` y compact rules
4. artefactos del change actual (`proposal`, `spec`, `design`, `tasks`, `verify`)
5. `docs/`, `README`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, etc.
6. pregunta breve al usuario

La idea es simple:

- primero recuperar contexto ya estructurado
- después leer documentación del proyecto
- recién al final preguntar al usuario lo que realmente no está resuelto

## 11.7 Optimización de tokens sin perder veracidad

Reglas recomendadas:

1. Resolver registry una vez por sesión.
2. Pasar referencias a artefactos, no cuerpos largos.
3. Mantener presupuestos de tamaño por artefacto.
4. Usar `lite` solo en tareas realmente chicas.
5. Correr `spec` y `design` en paralelo solo cuando el host y el contexto lo permitan.
6. Reutilizar `state.yaml` o equivalente para recuperación.
7. No usar deep search salvo en modo `deep` o cuando el riesgo lo justifique.

Presupuestos útiles heredados del SDD relevado:

| Artefacto | Presupuesto orientativo |
|---|---|
| `proposal` | < 400 palabras |
| `spec` | < 650 palabras |
| `design` | < 800 palabras |
| `tasks` | < 530 palabras |

---

## 12. Breaking changes respecto de `agents-plan-v1`

## 12.1 Cambios conceptuales

| Cambio | Impacto |
|---|---|
| `SURVEY` y `PLAN` dejan de ser source of truth principal | mejora trazabilidad, cambia UX interna |
| `strategic-planner` se divide | más precisión, más artefactos |
| `qa-validator` deja de ser el único gate | aparece `stage-qa` + `sdd-verify` |
| el orquestador deja la delegación absoluta | gana eficiencia en casos chicos |
| `docs/temp/*` pasa a ser auxiliar | reduce fragmentación de estado |

## 12.2 Cambios operativos

| Cambio | Riesgo | Mitigación |
|---|---|---|
| más artefactos por change | más complejidad inicial | usar templates y contracts compartidos |
| split de planner en varias fases | sensación de mayor latencia | usar vistas derivadas y modo `lite` |
| verify final obligatorio | flujo más largo | mantener `stage-qa` para feedback rápido |
| registry obligatorio | costo inicial de bootstrap | se amortiza rápido y baja tokens después |

## 12.3 Riesgos de implementación

1. Crear demasiadas skills demasiado rápido y sin shared contracts.
2. Duplicar lógica entre skills y agents wrappers.
3. Reintroducir decisiones hardcodeadas por stack.
4. Sobrecargar al usuario con confirmaciones triviales.
5. Mantener `SURVEY`/`PLAN` primarios y artefactos SDD secundarios.

---

## 13. Roadmap de migración recomendado

## 13.1 Iteración 1: fundación

- crear `sdd-orchestrator`
- extraer `_shared`
- definir envelope común
- crear `sdd-init`
- crear `skill-registry`
- crear `project-map-init`

Resultado esperado:

- bootstrap sólido
- project map
- standards resueltos

## 13.2 Iteración 2: discovery y formalización

- convertir `structure-scanner` + `deep-context-analyzer` en motor de `sdd-explore`
- crear `sdd-propose`
- crear `sdd-spec`
- crear `sdd-design`
- crear `sdd-tasks`

Resultado esperado:

- separación correcta de intención, comportamiento, diseño y ejecución

## 13.3 Iteración 3: ejecución

- migrar `stage-executor` a `sdd-apply`
- mantener snapshot, precondiciones e impacto
- hacer que `apply` lea `proposal/spec/design/tasks`

Resultado esperado:

- implementación mejor guiada y menos implícita

## 13.4 Iteración 4: calidad

- convertir `qa-validator` en `stage-qa`
- crear `sdd-verify`
- agregar compliance matrix y verify-report

Resultado esperado:

- dos niveles de control de calidad

## 13.5 Iteración 5: cierre y packaging

- crear `sdd-archive`
- agregar examples por host
- agregar scripts de setup/install
- opcional: exports a `SURVEY` y `PLAN`

Resultado esperado:

- sistema reusable y distribuible

---

## 14. Decisiones recomendadas

## 14.1 Decisiones que tomaría ya

1. Mantener un solo orquestador principal.
2. Modelar subagentes como skills, no como agentes canónicos.
3. Introducir `skill-registry` desde el inicio.
4. Mantener `SURVEY` y `PLAN` solo como export/report opcional.
5. Implementar `stage-qa` y `sdd-verify` como capas distintas.
6. Usar `openspec` como layout base.
7. Crear una skill separada para `project-map-init`.
8. Fijar inglés como idioma obligatorio de skills, contratos y artefactos.
9. Resolver idioma conversacional por inferencia al inicio, con fallback a selector `es/en`.

## 14.2 Alternativas viables

### Opción A: un orquestador con modos y router

Pros:

- menos drift
- menos mantenimiento
- más claridad

Contras:

- el prompt del orquestador exige más disciplina

Veredicto:

- **recomendada**

### Opción B: varios orquestadores por objetivo

Pros:

- UX muy guiada

Contras:

- duplicación de reglas
- más drift
- más mantenimiento

Veredicto:

- útil solo más adelante si el producto ya está estable

### Opción C: varios orquestadores por profundidad

Pros:

- diferencia fuerte de comportamiento

Contras:

- innecesario al principio
- puede fragmentar decisiones

Veredicto:

- no recomendado como punto de partida

## 14.3 Recomendación final de diseño

Si el objetivo es armar un sistema serio y a tu gusto:

- quedate con la **disciplina operativa** de `agents-plan-v1`
- adoptá la **formalidad estructural** del SDD relevado
- usá **skills por fase** y **agents wrappers** solo como adaptadores
- priorizá `project-map-init`, `skill-registry`, `sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `stage-qa`, `sdd-verify`, `sdd-archive`

---

## 15. Resumen final

Tu v1 ya tiene varias piezas correctas para producción:

- control del flujo
- checkpoints con el usuario
- aislamiento del ejecutor
- QA incremental
- rollback/checkpoint

Lo que le falta para transformarse en un SDD profesional reusable es:

- separar artefactos por fase
- incorporar `skill-registry` y compact rules
- unificar contratos compartidos
- formalizar persistencia
- agregar verify final con evidencia
- agregar archive como cierre obligatorio

La v2 correcta no es "tirar la v1". Es **redistribuirla** dentro de una arquitectura SDD más fuerte.

Síntesis final:

- **motor operativo**: tu v1
- **modelo sistémico**: SDD relevado
- **recomendación**: fusionarlos con skills-first, un orquestador fino, artefactos formales, QA en dos capas y cierre auditable
