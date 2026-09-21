# CODE_NEW_SDD_2

Documento de definicion previa a planning para un nuevo sistema SDD profesional, basado en el relevamiento consolidado de `CODEX_NEW_SDD.md` y `CLAUDE_NEW_SDD.md`, mas las decisiones ya cerradas para esta v2.

Este documento no es un plan de implementacion. Es la base para tomar decisiones, congelar contratos minimos y recien despues pasar a planning.

---

## Indice

1. Objetivo del documento
2. Decisiones ya cerradas
3. Vision del sistema
4. Arquitectura objetivo
5. Bootstrap e inicializacion de sesion
6. Objetivos activables y modos
7. Pipeline base y politica de shortcuts
8. Persistencia, artefactos y contexto
9. Contratos compartidos minimos
10. Interaccion con el usuario e idioma
11. Guardrails, validaciones y quality gates
12. Reutilizacion de la v1 y limites de compatibilidad
13. Criterios para quedar listo antes de planning
14. Alternativas diferibles
15. Resumen final

---

## 1. Objetivo del documento

El objetivo de esta v2 es definir un sistema SDD que:

- sea mas profesional y predecible que `agents-plan-v1`
- mantenga lo util de la v1
- tome del modelo SDD formal lo que realmente agrega disciplina operativa
- evite sobredisenar una primera version
- sea portable entre hosts, pero sin trabarse por neutralidad excesiva
- tenga una interaccion mas precisa con el usuario
- use artefactos y contratos como source of truth, no la memoria del chat

La idea central ya no es "tener varios subagentes sueltos", sino tener un sistema con:

- un orquestador fino
- skills por fase como fuente de verdad funcional
- bootstrap explicito
- contexto reusable
- artefactos persistentes
- verificaciones claras
- checkpoints utiles con el usuario

---

## 2. Decisiones ya cerradas

Estas decisiones quedan congeladas como base de la siguiente etapa.

| Decision | Resolucion |
|---|---|
| Estrategia base | `skills-first`, con wrappers por host |
| Forma del orquestador | un unico orquestador delgado, pero responsable de conducir el flujo y mantener una mini memoria operativa de sesion |
| Bootstrap | `sdd-init` corre fuera del orquestador |
| Alcance de `sdd-init` | project map + config base + validaciones + `skill-registry` + cache de compact rules |
| `skill-registry` | integrado al bootstrap y leido una vez por sesion |
| Layout de spec | `spec.md` unico por cambio como default |
| Pipeline | pipeline completo, con fases fusionables u opcionales segun complejidad |
| Shortcuts | permitidos solo con reglas explicitas y cuando la complejidad lo justifique |
| Modos | `lite`, `standard`, `deep`, con recomendacion sugerida al inicio |
| Objetivos iniciales | `new-feature`, `bug-fix`, `planner`, `refactor/rework` |
| Checkpoints | opciones + campo libre, sin sobrepreguntar |
| Idioma de conversacion | inferir `es/en`; si no se puede, pedir selector interactivo |
| Persistencia de idioma | `user_language` en config; estado dinamico en state |
| Contratos `_shared` | se definen desde v1 |
| Model routing | opcional como adapter; no parte obligatoria del nucleo |
| Project map | ruta neutral y versionable dentro del repo |
| Compatibilidad con v1 | arranque limpio; sin migracion automatica en v1 |
| Alcance de este documento | base de decisiones y contratos minimos, no planning |

### 2.1 Aclaraciones importantes sobre las decisiones

#### Orquestador con mini memoria operativa

El orquestador no debe depender de "recordar" toda la sesion, pero si debe mantener una memoria minima y precisa mientras trabaja. Esa mini memoria deberia incluir:

- objetivo activo
- modo activo
- `change-name` actual
- estado de la fase actual
- ultimas decisiones aprobadas por el usuario
- paths de artefactos principales
- snapshot de `compact rules`
- dudas aun no resueltas
- ultimo checkpoint y su resultado

Esta memoria es operativa, no semantica. El source of truth sigue estando en config, state y artefactos.

#### Arranque limpio respecto de v1

La primera version no deberia intentar migrar automaticamente `SURVEY` y `PLAN` viejos a los nuevos artefactos. Eso agrega complejidad demasiado temprano.

Se toma esta postura:

- usar v1 como referencia funcional
- reutilizar ideas, envelopes, prompts y criterios de calidad
- permitir mas adelante vistas derivadas o importacion manual
- no meter compatibilidad automatica como requisito de la fundacion

---

## 3. Vision del sistema

La vision recomendada es:

- un sistema centrado en artifacts
- con skills en ingles como contratos estables
- con UX conversacional en `es` o `en`
- con bootstrap explicito antes de usar el orquestador
- con un orquestador que decide, valida, resume y enruta
- con fases claras y calidad incremental

### 3.1 Principios rectores

1. El orquestador coordina y decide; no hace trabajo pesado por defecto.
2. Cada skill tiene una responsabilidad principal y entradas/salidas claras.
3. El sistema debe poder recuperar contexto sin depender del chat.
4. Toda decision relevante debe quedar reflejada en artefactos o estado persistido.
5. Hay que preguntar al usuario cuando la decision cambia scope, riesgo o direccion.
6. No hay que preguntar lo que el sistema puede descubrir leyendo proyecto y artefactos.
7. El sistema interno debe estar en ingles para evitar drift entre hosts.
8. La UX debe ser directa, breve y util.
9. El modo y la profundidad deben adaptarse a la tarea, no imponerse siempre.
10. Verify y cierre no son opcionales en flujos de implementacion reales.

### 3.2 Modelo conceptual recomendado

La topologia recomendada queda asi:

- `sdd-init` prepara el entorno de trabajo y deja contexto reusable
- `sdd-orchestrator` toma la tarea, detecta objetivo y modo, y coordina fases
- skills core ejecutan trabajo por fase
- skills soporte resuelven contexto, calidad, git y utilidades
- los artefactos y estados persistidos actuan como memoria estable del sistema

---

## 4. Arquitectura objetivo

## 4.1 Orquestador principal

Debe existir un unico orquestador principal.

### Responsabilidades del orquestador

- entender el input del usuario
- inferir o confirmar objetivo
- inferir o confirmar modo
- recuperar contexto ya persistido
- leer `skill-registry` una vez por sesion y cachear compact rules
- elegir la siguiente fase
- decidir si conviene delegar o resolver inline
- resumir resultados de cada fase
- pedir confirmacion en checkpoints relevantes
- mantener mini memoria operativa de sesion
- conducir la iteracion hasta cierre o pausa

### Lo que el orquestador no deberia hacer como regla

- hacer exploraciones profundas largas si existe una skill mejor para eso
- implementar lotes grandes de cambios cuando `sdd-apply` puede hacerlo mejor
- reemplazar `sdd-verify`
- actuar como unica memoria del sistema

### Recomendacion de diseño

- orquestador fino
- con mas criterio que un simple router
- pero sin absorber la logica de las fases

La idea no es un dispatcher ciego. La idea es un coordinador con criterio, estado minimo y checkpoints fuertes.

## 4.2 Skills core

Set inicial recomendado:

- `sdd-explore`
- `sdd-propose`
- `sdd-spec`
- `sdd-design`
- `sdd-tasks`
- `sdd-apply`
- `sdd-verify`
- `sdd-archive`

### Responsabilidad resumida por skill

| Skill | Responsabilidad |
|---|---|
| `sdd-explore` | relevar contexto, restricciones, hallazgos, riesgos y area afectada |
| `sdd-propose` | convertir hallazgos en opcion u orientacion de cambio |
| `sdd-spec` | fijar comportamiento esperado, alcance y criterios de aceptacion |
| `sdd-design` | bajar el enfoque tecnico cuando haga falta |
| `sdd-tasks` | convertir spec/design en unidades de trabajo ejecutables |
| `sdd-apply` | implementar cambios aprobados y registrar progreso |
| `sdd-verify` | comprobar comportamiento, integridad y cobertura esperada |
| `sdd-archive` | cerrar el cambio y dejar los artefactos ordenados |

## 4.3 Skills de soporte

Set inicial recomendado:

- `sdd-init`
- `skill-registry`
- `project-map-init`
- `stage-qa`
- `git-checkpoint`
- `judgment-day` o equivalente de review profunda opcional
- `branch-pr`
- `issue-creation`

### Rol de cada una

| Skill | Rol |
|---|---|
| `sdd-init` | bootstrap del proyecto y la sesion |
| `skill-registry` | resolver skills disponibles y generar compact rules |
| `project-map-init` | generar mapa de proyecto usable por el sistema |
| `stage-qa` | validacion rapida por lote o checkpoint tecnico |
| `git-checkpoint` | ayudar a batching, snapshots y checkpoints de integracion |
| `judgment-day` | review mas profunda cuando el riesgo amerita segunda capa |
| `branch-pr` | soporte operativo de ramas y PR |
| `issue-creation` | soporte operativo para bajar hallazgos o trabajo pendiente |

## 4.4 Skills vs agents

Decision recomendada:

- las skills son la fuente de verdad funcional
- los wrappers por host son adaptadores finos

### Por que esta decision es mejor para esta v2

- evita drift semantico entre hosts
- permite `_shared`
- baja mantenimiento
- facilita versionado
- deja abierta la puerta a `.claude`, `.codex`, `.cursor` u otros

### Alternativa posible

Como alternativa futura, cada host puede tener:

- un wrapper de orquestador propio
- wrappers minimos para skills con necesidades especiales de tools/model

Pero no deberian convertirse en el source of truth.

---

## 5. Bootstrap e inicializacion de sesion

Esta es una de las decisiones mas importantes de la v2.

## 5.1 Regla principal

`sdd-init` no forma parte del flujo normal del orquestador.

Se ejecuta:

- al comienzo de una nueva sesion en un proyecto
- cuando el usuario quiera refrescar contexto
- cuando el sistema detecte que el contexto persistido quedo viejo y recomiende relanzarlo

La responsabilidad primaria de ejecutarlo es del usuario.

El orquestador puede:

- detectar que falta bootstrap
- avisarlo
- sugerir correrlo

Pero no deberia esconder ese paso ni meter side effects fuertes sin explicitarlo.

## 5.2 Que hace `sdd-init`

`sdd-init` deberia hacer todo esto en una sola inicializacion:

1. detectar stack del proyecto
2. detectar docs y fuentes de contexto relevantes
3. detectar patrones y convenciones del repo
4. detectar herramientas de test, build, lint y package manager
5. generar o actualizar project map
6. generar o actualizar `.sdd/skill-registry.md`
7. compactar reglas reutilizables para la sesion
8. crear o actualizar config base
9. guardar configuracion minima del usuario
10. dejar listo el estado para que el orquestador arranque rapido

## 5.3 Resultado esperado del bootstrap

Despues de `sdd-init`, el sistema deberia contar como minimo con:

- config persistida del proyecto
- user config minima
- project map versionable
- skill registry
- compact rules listas para inyeccion
- paths base de artefactos
- metadata del stack y convenciones detectadas

## 5.4 Integrar `skill-registry` al bootstrap

Decision recomendada:

- `skill-registry` se integra al bootstrap
- se lee una vez por sesion
- se cachea en una forma compacta y util para el orquestador

Esto evita:

- relecturas innecesarias
- redescubrimiento de skills
- inconsistencias entre fases
- gasto de tokens por contexto repetido

### Recomendacion operativa

Durante `sdd-init`:

- se genera o refresca `.sdd/skill-registry.md`
- se deriva una version compacta util para la sesion
- el orquestador la toma al comenzar y la conserva en su mini memoria

## 5.5 Interaccion recomendada de `sdd-init`

`sdd-init` deberia tener una interaccion corta pero suficientemente guiada.

Secuencia recomendada:

1. detectar stack y presentarlo para confirmar o corregir
2. mostrar docs y contexto detectado
3. sugerir modo de persistencia
4. sugerir ruta y nombre del project map
5. informar que se va a generar o refrescar `skill-registry`
6. guardar config minima de usuario
7. devolver resumen final de bootstrap

### Configuracion minima de usuario

El archivo principal de config deberia tener una seccion `user` o `user_config` con al menos:

- `language`
- `preferred_mode` opcional
- `artifact_root` elegido si no usa default
- otras preferencias minimas que surjan en init

No conviene exagerar esta seccion. Debe ser simple.

## 5.6 Project map

El project map es una pieza central del sistema.

Contenido minimo recomendado:

- stack
- package manager
- frameworks y tooling principal
- patrones arquitectonicos
- carpetas importantes
- donde buscar frontend, backend, tests, config, scripts y docs
- convenciones detectadas
- rarezas o riesgos del repo

### Regla de ubicacion

Debe vivir en una ruta neutral y versionable dentro del repo.

Opciones recomendables:

- `.sdd/project-map.md`
- `docs/ai/PROJECT_SDD_CONTEXT.md`
- `docs/context/PROJECT_SDD_CONTEXT.md`

### Recomendacion

Usar por default:

- `.sdd/project-map.md`

Y permitir override del usuario en `sdd-init`.

No conviene usar una ruta host-specific como fuente principal del proyecto.

---

## 6. Objetivos activables y modos

## 6.1 Objetivos iniciales

El sistema deberia soportar desde v1 estos objetivos:

- `new-feature`
- `bug-fix`
- `planner`
- `refactor/rework`

### Descripcion resumida

| Objetivo | Enfoque principal |
|---|---|
| `new-feature` | comportamiento nuevo o expansion funcional |
| `bug-fix` | correccion con analisis de causa, impacto y regresion |
| `planner` | llegar hasta artefactos de decision y tareas sin implementar |
| `refactor/rework` | mejorar estructura o diseno preservando integridad |

## 6.2 Modos de profundidad

Modos iniciales:

- `lite`
- `standard`
- `deep`

### Reglas recomendadas

| Modo | Uso sugerido |
|---|---|
| `lite` | cambios chicos, fixes puntuales, tareas acotadas |
| `standard` | default para la mayoria de los trabajos reales |
| `deep` | cambios de alto riesgo, incertidumbre o impacto amplio |

### Comportamiento recomendado

Al iniciar el flujo, el sistema deberia:

1. inferir objetivo y modo sugerido
2. mostrarselo al usuario
3. permitir confirmacion o cambio

No deberia imponer `deep` por defecto. Tampoco deberia usar `lite` sin chequear que el riesgo sea realmente bajo.

---

## 7. Pipeline base y politica de shortcuts

## 7.1 Pipeline base recomendado

Pipeline completo:

`explore -> propose -> spec -> design -> tasks -> apply -> verify -> archive`

Este pipeline es la referencia. No significa que todas las fases sean siempre obligatorias en todos los casos.

## 7.2 Fases fusionables u opcionales

Reglas recomendadas:

- `design` puede omitirse en cambios triviales o fixes bien acotados
- `propose` y `spec` pueden fusionarse si el cambio es simple y la intencion es clara
- `planner` se detiene antes de `apply`
- `archive` puede esperar si el usuario quiere revisar primero el cierre

## 7.3 Cuando usar shortcuts

Los shortcuts solo deberian activarse si:

- la complejidad es baja
- el riesgo es bajo
- el scope esta claro
- no hay ambiguedades importantes
- el usuario confirma cuando corresponde

Si la complejidad no se puede inferir con confianza:

- el sistema debe consultarlo
- o elegir la opcion mas segura

## 7.4 Recomendacion sobre `planning-lite`

Existe una alternativa valida:

- crear una variante `planning-lite`

Pero no la recomiendo como pieza central de v1.

Es mejor arrancar con:

- un unico pipeline
- reglas de shortcut claras
- sugerencias contextuales del orquestador

Si mas adelante la UX lo pide, `planning-lite` puede existir como alias o preset, no como segundo sistema.

## 7.5 Confirmaciones en fases opcionales

Cuando una fase sea fusionable u opcional, el sistema deberia:

- explicar en una o dos lineas por que sugiere saltarla o fusionarla
- pedir confirmacion si el impacto no es trivial
- dejar rastro de esa decision en `state.yaml` o artefacto equivalente

---

## 8. Persistencia, artefactos y contexto

## 8.1 Principio base

El source of truth del sistema debe vivir en:

- `config`
- `state`
- artefactos de cambio
- project map
- skill registry

No en la memoria del chat.

## 8.2 Recomendacion de persistencia

Default recomendado:

- `openspec` o layout equivalente, versionable en repo

Alternativas:

- `hybrid` si realmente se necesita memoria cross-session adicional
- `none` solo para exploraciones o sesiones descartables

### Recomendacion practica

Tomar `openspec` como default productivo y dejar `hybrid` como opcion, no como base obligatoria.

## 8.3 Layout recomendado de artefactos

Layout base recomendado:

```text
openspec/
  config.yaml
  changes/
    {change-name}/
      state.yaml
      explore.md
      proposal.md
      spec.md
      design.md
      tasks.md
      apply-progress.md
      verify-report.md
    archive/
      YYYY-MM-DD-{change-name}/

.sdd/
  project-map.md
  skill-registry.md
```

### Razon de esta decision

- mantiene simpleza
- evita sobrefragmentacion
- hace mas facil navegar cambios
- alcanza para una v1 seria

## 8.4 Regla sobre `spec.md`

Se toma como default:

- un `spec.md` por cambio

Si un cambio crece mucho:

- primero usar secciones internas o anexos
- solo despues evaluar multiples specs
- esa escalada deberia ser explicita y, de ser posible, validada por el usuario

## 8.5 `config.yaml`

`config.yaml` deberia contener como minimo:

- metadata del proyecto
- stack detectado
- package manager
- modo de persistencia
- artifact root
- preferencias del sistema
- seccion `user` o `user_config`

Ejemplo de estructura minima:

```yaml
project:
  name: example-project
  stack:
    language: typescript
    framework: nextjs
    package_manager: pnpm

sdd:
  persistence_mode: openspec
  artifact_root: openspec
  project_map_path: .sdd/project-map.md
  skill_registry_path: .sdd/skill-registry.md

user:
  language: es
  preferred_mode: standard
```

## 8.6 `state.yaml`

`state.yaml` deberia registrar:

- fase actual
- fases completadas
- decisiones de checkpoint
- riesgos abiertos
- atajos o fusiones autorizadas
- proximos pasos recomendados

No deberia convertirse en un dump del chat.

## 8.7 Escalera de contexto

El orquestador deberia recuperar contexto en este orden:

1. `config.yaml`
2. `state.yaml` del cambio actual
3. `.sdd/project-map.md`
4. `.sdd/skill-registry.md` y compact rules cacheadas
5. artefactos del cambio actual
6. docs del proyecto
7. pregunta breve al usuario

Este orden baja tokens y mejora precision.

---

## 9. Contratos compartidos minimos

Estos contratos deberian existir desde el arranque.

## 9.1 `sdd-phase-common.md`

Debe definir:

- envelope comun de salida
- reglas de lectura de artefactos
- reglas de devolucion resumida
- manejo de `skill_resolution`
- convenciones de estados y errores

## 9.2 `artifact-contract.md`

Debe definir:

- que artefactos lee cada fase
- que artefactos escribe cada fase
- prerequisitos por fase
- si una fase puede actualizar o solo crear

## 9.3 `persistence-contract.md`

Debe definir:

- ubicacion y forma de `config.yaml`
- ubicacion y forma de `state.yaml`
- reglas de escritura
- que cosas son persistentes por sesion y por cambio

## 9.4 `user-interaction-contract.md`

Debe definir:

- tipos de checkpoint
- formato de opciones
- campo libre
- cuando preguntar y cuando no
- como registrar respuestas del usuario

## 9.5 `project-standards-contract.md`

Debe definir:

- como representar convenciones de stack
- reglas de naming
- testing standards
- linting/formatting
- fuentes de verdad del proyecto

## 9.6 Envelope comun recomendado

Toda skill deberia devolver un envelope compatible con:

| Campo | Uso |
|---|---|
| `status` | `success`, `partial`, `blocked` |
| `executive_summary` | resumen corto |
| `artifacts` | paths o ids afectados |
| `next_recommended` | siguiente paso sugerido |
| `risks` | riesgos activos |
| `skill_resolution` | como resolvio skill/contexto |

---

## 10. Interaccion con el usuario e idioma

## 10.1 Regla general de interaccion

La interaccion debe ser:

- clara
- breve
- contextual
- util para destrabar decisiones reales

No debe ser:

- verborragica
- mecanica
- redundante
- llena de confirmaciones irrelevantes

## 10.2 Checkpoints obligatorios vs condicionales

### Checkpoints obligatorios

- antes de `apply`
- cuando hay dos alternativas razonables con trade-offs distintos
- cuando se detecta impacto grande o riesgo alto
- cuando una fase sugiere shortcut no trivial
- antes de cerrar y archivar si hubo observaciones relevantes

### Checkpoints condicionales

- cuando falta contexto importante
- cuando la complejidad no se puede inferir
- cuando una fase encuentra algo que cambia el scope

### Checkpoints a evitar

- decisiones mecanicas
- elecciones obvias ya determinadas por el proyecto
- preguntas cuya respuesta ya esta en docs o artefactos

## 10.3 Formato recomendado de interaccion

Formato recomendado:

- resumen ejecutivo corto
- estado
- opciones claras
- campo libre siempre disponible

El campo libre no implica preguntar de mas. Solo garantiza que el usuario pueda corregir o ampliar contexto sin quedar encerrado en opciones.

## 10.4 Politica de idioma

Regla cerrada:

- sistema interno en ingles
- conversacion con el usuario en idioma inferido

### Debe quedar en ingles

- `SKILL.md`
- contratos `_shared`
- prompts del sistema
- nombres de artefactos
- fields y keys de persistencia
- project map
- `proposal`, `spec`, `design`, `tasks`, `verify-report`

### Puede variar por idioma

- mensajes del orquestador
- preguntas
- resumentes ejecutivos
- selectores interactivos

## 10.5 Inicio de conversacion

Al iniciar una sesion nueva:

1. inferir `es` o `en` por el primer mensaje si es claro
2. si no se puede inferir, mostrar selector interactivo simple
3. guardar el idioma elegido o detectado en config

Selector recomendado:

- `Español`
- `English`

No conviene usar una pregunta abierta si el idioma no se pudo inferir.

---

## 11. Guardrails, validaciones y quality gates

## 11.1 Guardrails del sistema

1. No avanzar a `apply` sin artefactos minimos aprobados o shortcut valido.
2. No asumir stack, package manager ni convenciones si `sdd-init` ya las detecto.
3. No confiar en memoria de chat cuando existe estado persistido.
4. No usar `deep` salvo que el riesgo o incertidumbre lo justifiquen.
5. No ejecutar shortcuts si la complejidad no es claramente baja.
6. No cerrar un cambio sin alguna forma de verify.
7. No mover contexto critico a rutas host-specific como fuente principal.

## 11.2 Validaciones por fase

### `sdd-init`

- stack detectado
- docs detectadas
- config persistida
- project map generado
- skill registry generado o refrescado

### `sdd-explore`

- area afectada identificada
- hallazgos principales claros
- riesgos iniciales listados

### `sdd-propose`

- intencion del cambio clara
- alternativa recomendada explicitada
- trade-offs resumidos

### `sdd-spec`

- alcance
- comportamiento esperado
- criterios de aceptacion
- no objetivos si corresponden

### `sdd-design`

- enfoque tecnico
- impacto en modulos
- riesgos de implementacion

### `sdd-tasks`

- unidades de trabajo ejecutables
- orden sugerido
- dependencias claras

### `sdd-apply`

- batch actual definido
- progreso registrado
- stage QA cuando aplique

### `sdd-verify`

- evidencia de verificacion
- issues pendientes
- veredicto de cierre o reproceso

### `sdd-archive`

- artefactos completos
- estado final consistente
- ubicacion de archivo resuelta

## 11.3 Segunda capa de calidad

La v2 deberia contemplar dos niveles:

- `stage-qa` para control incremental
- `sdd-verify` para validacion final

Opcionalmente:

- una review profunda adicional para cambios sensibles

## 11.4 Breaking assumptions que hay que aceptar

Para que el sistema funcione bien, hay que aceptar estas reglas nuevas:

- el bootstrap es explicito
- el project map pasa a ser pieza central
- `skill-registry` deja de ser opcional
- los artefactos pasan a ser source of truth
- `SURVEY` y `PLAN` dejan de ser el centro del sistema
- el orquestador ya no puede apoyarse solo en chat y criterio informal

---

## 12. Reutilizacion de la v1 y limites de compatibilidad

## 12.1 Lo que conviene reutilizar

De la v1 conviene preservar:

- disciplina de fases
- orientacion a contexto antes de ejecutar
- separacion entre pensar, ejecutar y validar
- criterio de batching
- QA incremental
- forma de interactuar con el usuario cuando hay ambiguedad real

## 12.2 Como reutilizar piezas concretas

| Pieza v1 | Nuevo destino sugerido |
|---|---|
| Phase 0 | `sdd-init` |
| structure scanner | `sdd-explore` |
| deep context analyzer | `sdd-explore` |
| strategic planner | `sdd-propose` + `sdd-design` + `sdd-tasks` |
| stage executor | `sdd-apply` |
| qa validator | `stage-qa` |

## 12.3 Lo que no conviene arrastrar tal cual

- `SURVEY` y `PLAN` como source of truth
- dependencia excesiva de memoria del chat
- falta de skill registry
- poca formalizacion de artefactos por fase
- validacion final demasiado liviana

## 12.4 Compatibilidad con v1

Postura recomendada para v1 del nuevo sistema:

- no hacer migracion automatica
- si hace falta, usar artefactos viejos como referencia humana
- evaluar despues una importacion manual o vistas derivadas

---

## 13. Criterios para quedar listo antes de planning

No conviene entrar a planning si esto no esta claro.

## 13.1 Minimos ya resueltos

Estos puntos quedan suficientemente resueltos para pasar despues a planning:

- arquitectura `skills-first`
- orquestador unico y fino
- bootstrap fuera del orquestador
- `skill-registry` integrado al init
- project map neutral y versionable
- `spec.md` unico por cambio
- modos `lite/standard/deep`
- objetivos iniciales
- idioma y user config
- contratos `_shared` como requisito

## 13.2 Lo que planning va a tener que bajar a detalle

Planning todavia debera definir:

- nombres finales de carpetas y archivos
- contenidos exactos de cada `SKILL.md`
- prompts finales del orquestador
- schemas concretos de `config.yaml` y `state.yaml`
- formato exacto de checkpoint UX
- envelope final y codigos de estado
- criterios exactos de shortcut por nivel de complejidad

## 13.3 Definition of Ready recomendada

Se puede pasar a planning cuando exista acuerdo sobre:

1. layout final de carpetas base
2. schema minimo de config/state
3. contenido minimo del project map
4. envelope comun
5. lista inicial de skills core y soporte
6. regla de checkpoints
7. politica de shortcuts
8. quality gates minimos

---

## 14. Alternativas diferibles

Estas decisiones no bloquean la fundacion y pueden diferirse si hace falta.

## 14.1 Model routing

Alternativas:

- dejarlo fuera de v1
- documentarlo como adapter opcional
- fijarlo por fase desde el inicio

Recomendacion:

- dejarlo como adapter opcional y solo incorporarlo si no complica demasiado

## 14.2 Persistencia `hybrid`

Alternativas:

- solo `openspec`
- `openspec` + `hybrid`
- agregar `none` como modo trivial

Recomendacion:

- `openspec` como default
- `hybrid` como opcion
- `none` solo para sesiones descartables

## 14.3 `planning-lite`

Alternativas:

- no tenerlo
- tenerlo como alias de shortcuts
- tenerlo como flujo separado

Recomendacion:

- no separarlo en v1
- si hace falta, resolverlo como alias o preset

## 14.4 Multiple specs

Alternativas:

- `spec.md` unico
- multiples specs por dominio
- esquema hibrido

Recomendacion:

- `spec.md` unico en v1
- escalar solo cuando el cambio realmente lo pida

---

## 15. Resumen final

La recomendacion consolidada para esta v2 es construir un sistema SDD con:

- un orquestador unico, fino y con mini memoria operativa
- skills en ingles como fuente de verdad funcional
- bootstrap explicito por `sdd-init` antes de usar el orquestador
- `skill-registry` y project map generados en la inicializacion
- artefactos persistentes simples y versionables
- `spec.md` unico por cambio como default
- modos `lite`, `standard` y `deep`
- checkpoints utiles pero no invasivos
- user config minima con idioma y preferencias basicas
- verify real antes de cierre

La postura correcta para arrancar no es copiar literal ninguno de los relevamientos previos, sino combinarlos asi:

- tomar del relevamiento mas estructurado la disciplina de contratos, bootstrap, artefactos y verify
- tomar de la v1 el criterio practico, la interaccion directa y la utilidad real para trabajar
- evitar, en esta etapa, sobrecargar la fundacion con migraciones automaticas, host lock-in o model routing obligatorio

Si esta base se mantiene, la etapa de planning ya puede enfocarse en bajar a detalle:

- estructura final
- contratos exactos
- contenido de cada skill
- prompt del orquestador
- orden real de implementacion

Ese deberia ser el siguiente paso. No antes.
