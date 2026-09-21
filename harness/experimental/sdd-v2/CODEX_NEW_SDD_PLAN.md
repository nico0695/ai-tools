# CODEX_NEW_SDD_PLAN

Plan detallado para implementar el nuevo SDD v2 a partir del relevamiento consolidado en `CODE_NEW_SDD_2.md`, contrastado con `CODEX_NEW_SDD.md`, `CLAUDE_NEW_SDD.md`, `orchestrator-skills-deep-dive.md` y la implementacion real de `agents-plan-v1`.

---

## 1. Objetivo y alcance

Este documento traduce la base de decisiones de `CODE_NEW_SDD_2.md` a un plan ejecutable de implementacion.

Alcance de este plan:

- definir que partes del relevamiento ya estan suficientemente validadas
- cerrar los ajustes operativos necesarios para evitar drift durante la implementacion
- describir como debe quedar formado el nuevo SDD v2
- ordenar la construccion por stages y substeps controlables
- dejar explicitas dependencias, opcionales, riesgos de secuencia y criterio de avance

Fuera de alcance de este plan:

- implementar el sistema ahora mismo
- reestructurar `agents-plan-v1`
- mover assets fuera de `sdd/sdd-v2`
- hacer compatibilidad automatica con `SURVEY` y `PLAN` de v1

---

## 2. Conclusion ejecutiva

La base de `CODE_NEW_SDD_2.md` es solida y alcanza para empezar implementacion real, pero no conviene bajar a codigo sin cerrar algunos detalles operativos para evitar que el sistema nazca con drift.

La recomendacion final es esta:

- mantener `skills-first` como decision central
- mantener un solo orquestador, fino pero con criterio y mini memoria operativa
- implementar bootstrap explicito (`sdd-init`) fuera del flujo normal del orquestador
- usar artefactos y estado persistido como source of truth
- implementar primero un MVP serio con `openspec` como unico modo realmente operativo
- incubar todo el sistema nuevo dentro de `sdd/sdd-v2` para no mezclarlo temprano con v1 ni con roots globales del repo
- dejar `hybrid`, wrappers multi-host y exports legacy como capas posteriores, no como bloqueantes

En otras palabras: la arquitectura esta bien; lo que falta no es rediscutirla, sino secuenciarla con disciplina.

---

## 3. Validacion de decisiones tomadas en `CODE_NEW_SDD_2.md`

| Decision cerrada | Estado | Validacion | Accion en implementacion |
|---|---|---|---|
| `skills-first`, con wrappers por host | Validada | Es la decision mas correcta para bajar mantenimiento, evitar drift y dejar el sistema portable. | Implementar skills canonicas dentro de `sdd/sdd-v2` y dejar wrappers como adaptadores posteriores. |
| Unico orquestador delgado con mini memoria operativa | Validada con precision | Correcto, pero el orquestador debe ser una maquina de fases con reglas, no un router ciego ni un ejecutor pesado. | Definir estado minimo, ladder de contexto, reglas de checkpoint y transiciones de fase antes de escribir skills core. |
| `sdd-init` corre fuera del orquestador | Validada | Es coherente con un bootstrap explicito y evita side effects escondidos. | El orquestador debe detectar bootstrap faltante y bloquear o degradar de forma controlada, no intentar reemplazarlo. |
| Alcance de `sdd-init` = project map + config + validaciones + `skill-registry` + compact rules | Validada | El alcance es correcto y consistente con el modelo relevado. | Separar internamente `project-map-init` y `skill-registry`, pero ejecutarlos desde `sdd-init`. |
| `skill-registry` integrado al bootstrap y leido una vez por sesion | Validada con ajuste menor | Es correcto, pero necesita reglas de refresh e invalidacion. | Definir triggers de relectura en Stage 3. |
| `spec.md` unico por cambio como default | Validada | Correcto para una v1 seria sin sobrefragmentacion. | Mantenerlo como default y posponer multiples specs a backlog opcional. |
| Pipeline completo con fases fusionables u opcionales | Validada | Correcto, pero necesita una matriz exacta por objetivo y modo para no derivar en shortcuts arbitrarios. | Definir una policy matrix en contracts y en el orquestador. |
| Shortcuts solo con reglas explicitas | Validada | Correcto y alineado con rigor operativo. | Persistir cada shortcut autorizado en `state.yaml`. |
| Modos `lite`, `standard`, `deep` | Validada | Correcto y suficiente para la v1. | Definir gates minimos por modo y reglas de fusion/skip. |
| Objetivos iniciales `new-feature`, `bug-fix`, `planner`, `refactor/rework` | Validada con normalizacion | La lista esta bien, pero el id interno no deberia usar slash. | Usar `refactor-rework` como valor canonico interno. |
| Checkpoints con opciones + campo libre | Validada | Correcto para UX util sin cerrar al usuario. | Formalizar contrato de checkpoint y storage de decisiones. |
| Inferencia de idioma `es/en` y selector si no se puede inferir | Validada | Correcto y pragmatico. | Resolverlo en `sdd-init` y reusarlo en el orquestador. |
| Persistencia de idioma en config y estado dinamico en state | Validada | Correcto. | Guardar preferencia en `openspec/config.yaml` y lo dinamico del cambio en `state.yaml`. |
| Contratos `_shared` desde v1 | Validada con extension | Correcto, pero el set minimo debe incluir tambien convencion de `openspec`. | Crear `_shared` antes de escribir skills operativas. |
| Model routing opcional, no nuclear | Validada | Correcto. No debe bloquear fundacion ni contaminar contratos. | Dejar hooks de extension, no comportamiento obligatorio. |
| Project map neutral y versionable dentro del repo | Validada | Correcto, y mejor que un path host-specific. | Fijar `.sdd/project-map.md` como path canonico por default. |
| Compatibilidad con v1 por arranque limpio | Validada | Correcto. Intentar migracion automatica ahora seria ruido y deuda temprana. | Reutilizar ideas y logica, no artefactos legacy como contrato activo. |
| Este documento no es planning | Validada y ya cumplida | Era correcto como base previa. Este plan la extiende sin cambiar esa premisa. | Usar este archivo como puente entre definicion y ejecucion. |

### Lectura consolidada de la validacion

No encontre ninguna decision estructural que obligue a replantear la arquitectura.

Los ajustes necesarios no son conceptuales, sino operativos:

- fijar nombres canonicos y enums internos
- elegir el alcance real del MVP
- definir reglas de refresh del bootstrap
- cerrar el comportamiento de `planner` y `archive`
- ampliar levemente el envelope minimo para soportar decisiones bloqueantes y evidencia

---

## 4. Cierres operativos recomendados antes de escribir codigo

| Tema | Recomendacion | Motivo | Momento de cierre |
|---|---|---|---|
| Ubicacion de implementacion | Implementar todo el sistema nuevo primero dentro de `sdd/sdd-v2` | Aisla v2, evita mezclarla temprano con v1 y cumple el alcance pedido | Stage 0 |
| Persistencia MVP | Hacer `openspec` el unico modo realmente operativo en la primera version usable | Reduce superficie y evita inflar bootstrap y archive demasiado temprano | Stage 0 |
| `hybrid` y `none` | Dejar schema/hook preparados, pero no volverlos bloqueantes del primer release usable | Son utiles, pero no son fundacionales | Stage 0 / Stage 9 |
| Canonical ids | Usar `proposal.md`, `refactor-rework`, `project-map.md`, `verify-report.md`, `archive-report.md` | Evita drift entre docs, state y prompts | Stage 0 |
| `planner` | Cortar en `tasks.md` y dejar `state.yaml` en estado `planned`; no correr `apply`, `verify` ni `archive` | El flujo planner no debe fingir cierre de implementacion | Stage 0 |
| `archive` MVP | Mover carpeta activa a `openspec/changes/archive/YYYY-MM-DD-{change-name}/` y generar `archive-report.md`; diferir merge a specs globales | Mantiene trazabilidad sin sobrecargar la primera implementacion | Stage 0 |
| Compact rules cache | No persistir un segundo archivo separado en v1; usar `.sdd/skill-registry.md` + cache de sesion del orquestador | Evita duplicacion y problemas de invalidacion tempranos | Stage 3 |
| Envelope comun | Mantener el envelope minimo propuesto y agregar campos opcionales `decision_required`, `decision_options`, `evidence`, `errors` | Sin eso, el orquestador queda corto para fases bloqueadas y verify | Stage 2 |
| Freshness de bootstrap | Definir triggers claros para sugerir rerun: cambio grande de lockfile, nuevas tools, nuevos dirs relevantes, ausencia de artefactos, falla de resolucion de skills | Si no se define, `sdd-init` se vuelve manual y fragil | Stage 3 |
| `git-checkpoint` | Arrancar con la logica embebida en `sdd-apply`; extraer skill separada solo si realmente simplifica | Esta fuertemente acoplado a apply y no conviene forzar mas piezas de las necesarias | Stage 6 |

---

## 5. Analisis profundo: como debe quedar formado el nuevo SDD v2

## 5.1 Principio estructural

El nuevo SDD v2 no debe nacer como "otro bundle de agentes". Debe nacer como un sistema con cinco capas bien separadas:

1. Bootstrap del proyecto y la sesion
2. Orquestacion y decision de flujo
3. Skills de fase con contratos compartidos
4. Persistencia y artefactos del cambio
5. Calidad y cierre auditable

Si estas capas se mezclan, el sistema vuelve a parecerse a v1: util, pero demasiado informal.

## 5.2 Topologia recomendada

Flujo base de implementacion:

```text
sdd-init
  -> sdd-explore
  -> sdd-propose
  -> sdd-spec
  -> sdd-design
  -> sdd-tasks
  -> sdd-apply
  -> stage-qa
  -> sdd-verify
  -> sdd-archive
```

Flujo planner:

```text
sdd-init
  -> sdd-explore
  -> sdd-propose
  -> sdd-spec
  -> sdd-design
  -> sdd-tasks
  -> stop(planned)
```

Reglas clave:

- `stage-qa` no reemplaza `sdd-verify`
- `sdd-archive` no corre si no hubo `verify` aprobatorio
- `planner` no debe fabricar cierre falso
- `spec` y `design` pueden paralelizarse solo despues de `proposal`

## 5.3 Limites correctos del orquestador

El orquestador debe:

- detectar objetivo, modo y `change-name`
- cargar contexto en un orden estable
- decidir la siguiente fase
- decidir si una fase va inline o delegada
- resumir resultados en formato corto
- pedir confirmaciones solo cuando cambian scope, riesgo o direccion
- mantener mini memoria operativa de sesion
- persistir checkpoints y decisiones relevantes

El orquestador no debe:

- releer medio repo si ya existe bootstrap y artefactos
- absorber la logica de cada skill
- reemplazar `sdd-apply` o `sdd-verify`
- transformar el chat en source of truth

## 5.4 Modelo recomendado de artefactos

| Artefacto | Nivel | Writer principal | Rol |
|---|---|---|---|
| `.sdd/project-map.md` | proyecto | `project-map-init` | mapa durable del repo |
| `.sdd/skill-registry.md` | proyecto | `skill-registry` | skills descubiertas + compact rules |
| `openspec/config.yaml` | proyecto | `sdd-init` | stack, paths, preferencias y modo de persistencia |
| `openspec/changes/{change-name}/state.yaml` | cambio | orquestador + skills | estado de fases, shortcuts, riesgos y checkpoints |
| `explore.md` | cambio | `sdd-explore` | hallazgos, restricciones, area afectada |
| `proposal.md` | cambio | `sdd-propose` | intencion, alcance, alternativa elegida, rollback |
| `spec.md` | cambio | `sdd-spec` | comportamiento esperado y criterios de aceptacion |
| `design.md` | cambio | `sdd-design` | enfoque tecnico, modulos y riesgos de implementacion |
| `tasks.md` | cambio | `sdd-tasks` | unidades ejecutables y dependencias |
| `apply-progress.md` | cambio | `sdd-apply` | progreso real, batches y observaciones |
| `verify-report.md` | cambio | `sdd-verify` | evidencia, matriz de compliance y veredicto |
| `archive-report.md` | archivo | `sdd-archive` | cierre y trazabilidad final |

Regla importante:

- `state.yaml` registra estado operativo
- los `.md` registran decision y contenido semantico
- `config.yaml` registra defaults y contexto de proyecto

No hay que mezclar estos roles.

## 5.5 Layout recomendado de implementacion dentro de `sdd/sdd-v2`

```text
sdd/sdd-v2/
  orchestrator/
    SDD-ORCHESTRATOR.md
  skills/
    _shared/
      sdd-phase-common.md
      artifact-contract.md
      persistence-contract.md
      user-interaction-contract.md
      project-standards-contract.md
      openspec-convention.md
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
  schemas/
    envelope.schema.yaml
    config.schema.yaml
    state.schema.yaml
  templates/
    artifacts/
      explore.md
      proposal.md
      spec.md
      design.md
      tasks.md
      apply-progress.md
      verify-report.md
      archive-report.md
  examples/
    codex/
  docs/
    decisions/
```

Motivo de esta forma:

- mantiene todo v2 encapsulado
- deja clara la capa canonica (`skills/`, `_shared/`, `schemas/`)
- separa prompts de contratos y de templates
- permite despues exportar a roots globales sin remezclar fundacion

## 5.6 Matriz recomendada por objetivo

| Objetivo | Flujo minimo recomendado | Artefactos minimos | Corte de flujo |
|---|---|---|---|
| `new-feature` | explore -> propose -> spec -> design -> tasks -> apply -> verify -> archive | proposal, spec, tasks, verify-report | archivo completado |
| `bug-fix` | explore focalizado -> propose -> spec -> tasks -> apply -> verify -> archive | proposal, spec, tasks, verify-report | archivo completado |
| `planner` | explore -> propose -> spec/design -> tasks | proposal, spec o design, tasks, state | estado `planned` |
| `refactor-rework` | explore -> propose -> design -> tasks -> apply -> verify -> archive | proposal, design, tasks, verify-report | archivo completado |

Notas:

- en `refactor-rework`, `spec.md` puede ser liviano, pero no conviene eliminarlo si hay invariantes funcionales
- `planner` no debe simular `Done`; debe quedar como cambio planificado

## 5.7 Matriz recomendada por modo

| Modo | Shortcuts permitidos | Gates minimos | Recomendacion |
|---|---|---|---|
| `lite` | merge `propose + spec`, `design` opcional, `explore` mas focalizado | checkpoint antes de `apply`, `stage-qa` y `verify` si hubo cambios | para fixes chicos o cambios acotados |
| `standard` | flujo base; `design` solo se omite si el cambio es trivial | proposal clara, tasks ordenadas, verify real | default productivo |
| `deep` | sin shortcuts implicitos; `spec` y `design` separados; review adicional si el riesgo lo amerita | riesgos explicitados, alternativas resumidas, verify fuerte, opcional `judgment-day` | para cambios sensibles o inciertos |

Regla dura:

- si hubo modificacion de codigo, `verify` no se negocia

## 5.8 Distincion correcta entre `stage-qa` y `sdd-verify`

| Capa | Momento | Alcance | Resultado esperado |
|---|---|---|---|
| `stage-qa` | despues de cada batch o stage aplicado | smoke checks, regresiones rapidas, alertas tempranas | aprobar seguir o pedir correccion |
| `sdd-verify` | al final del cambio | tests, build, type-check, evidence matrix contra spec/tasks | PASS, PASS WITH WARNINGS o FAIL |

Esta separacion es obligatoria.

Si no se implementa asi, la v2 va a heredar el punto mas debil de v1: creer que QA incremental ya equivale a validacion final.

---

## 6. Plan detallado de implementacion

## Stage 0. Fundacion y cierres de arquitectura

**Objetivo**

Congelar todo lo que, si queda ambiguo, va a contaminar nombres, schemas, prompts y artefactos.

**Substeps**

1. Normalizar ids y nombres canonicos internos.
2. Declarar el alcance real del MVP: `openspec` operativo; `hybrid` y exports legacy diferidos.
3. Cerrar semantica de `planner` y `archive`.
4. Cerrar reglas base de `change-name`, `phase`, `status` y `skill_resolution`.
5. Congelar el layout de `sdd/sdd-v2` como area de incubacion v2.

**Entregables**

- decisiones de nombres y enums congeladas
- frontera MVP/no-MVP congelada
- semantica de cierre por objetivo congelada

**Dependencias**

- ninguna

**Criterio de cierre**

- ningun stage downstream necesita inventar nombres, paths o estados

**Observacion**

- este stage queda practicamente resuelto por este documento y no deberia reabrirse salvo blocker real

## Stage 1. Skeleton del paquete v2

**Objetivo**

Crear la estructura canonica de carpetas y placeholders para que la implementacion no arranque desordenada.

**Substeps**

1. Crear `orchestrator/`, `skills/`, `_shared/`, `schemas/`, `templates/`, `examples/` y `docs/decisions/`.
2. Crear placeholders de `SKILL.md` para cada skill core y soporte.
3. Crear placeholders de schemas y templates de artefactos.
4. Crear un `README` o documento de package interno para v2.
5. Dejar listos paths estables para futuros wrappers de host.

**Entregables**

- arbol base de `sdd/sdd-v2`
- paths canonicos estables
- placeholders que permitan trabajo incremental sin drift

**Dependencias**

- Stage 0

**Criterio de cierre**

- la estructura final ya no necesita cambios de naming para avanzar con contratos

## Stage 2. Contratos compartidos y schemas

**Objetivo**

Definir el contrato comun antes de escribir comportamiento por skill.

**Substeps**

1. Escribir `sdd-phase-common.md` con envelope, estados y convenciones de lectura/escritura.
2. Escribir `artifact-contract.md` con matriz de prerequisitos y outputs por fase.
3. Escribir `persistence-contract.md` con reglas para `config.yaml`, `state.yaml` y artefactos.
4. Escribir `user-interaction-contract.md` con checkpoint types, formato y storage.
5. Escribir `project-standards-contract.md` y `openspec-convention.md`.
6. Definir `envelope.schema.yaml`, `config.schema.yaml` y `state.schema.yaml`.
7. Definir matriz de shortcuts por `objetivo x modo`.
8. Definir reglas de `blocked`, `partial`, `decision_required` y `evidence`.

**Entregables**

- contratos `_shared` completos
- schemas minimos
- matriz de artefactos y estados

**Dependencias**

- Stage 1

**Criterio de cierre**

- cada skill futura puede escribirse sin adivinar inputs, outputs, status ni paths

**Paralelizacion posible**

- `artifact-contract.md` y `persistence-contract.md` pueden avanzarse en paralelo una vez congelado el naming

## Stage 3. Bootstrap del proyecto y de sesion

**Objetivo**

Construir la base que hace barato y confiable el resto del sistema.

**Substeps**

1. Implementar `project-map-init` con estructura minima fija para `.sdd/project-map.md`.
2. Implementar `skill-registry` para descubrir skills y compactar reglas de proyecto.
3. Implementar `sdd-init` como skill orquestadora del bootstrap.
4. Resolver deteccion de stack, docs, tooling, package manager y convenciones.
5. Persistir `openspec/config.yaml`, `.sdd/project-map.md` y `.sdd/skill-registry.md`.
6. Implementar deteccion/persistencia de idioma y preferencias minimas de usuario.
7. Definir y probar triggers de refresh de bootstrap.
8. Definir el resumen final esperado de `sdd-init`.

**Entregables**

- `sdd-init`
- `project-map-init`
- `skill-registry`
- bootstrap funcional sobre un repo real

**Dependencias**

- Stage 2

**Criterio de cierre**

- una corrida de `sdd-init` deja el proyecto listo para que el orquestador arranque sin redescubrir contexto

**Riesgo principal**

- hacer de `sdd-init` un mega skill verborragico y demasiado invasivo; debe ser fuerte, pero acotado

## Stage 4. Orquestador principal y motor de fases

**Objetivo**

Implementar la pieza que decide el flujo sin absorber la logica de las fases.

**Substeps**

1. Crear `SDD-ORCHESTRATOR.md` con rol, guardrails y politica de delegacion.
2. Definir la mini memoria operativa de sesion.
3. Implementar ladder de contexto: `config -> state -> project-map -> skill-registry -> artefactos -> docs -> user`.
4. Implementar inferencia de `objetivo`, `modo` y `change-name`.
5. Implementar selector de siguiente fase y transiciones por estado.
6. Implementar checkpoints y storage de decisiones del usuario.
7. Implementar politica de shortcuts y confirmaciones.
8. Implementar deteccion de bootstrap faltante, incompleto o vencido.
9. Implementar flujo de resume sobre `state.yaml`.
10. Implementar corte correcto para `planner`.

**Entregables**

- orquestador canonico v2
- maquina de fases estable
- reglas de resume y pause

**Dependencias**

- Stage 3

**Criterio de cierre**

- el orquestador puede llevar una tarea hasta `tasks.md` sin depender de memoria informal del chat

## Stage 5. Discovery y formalizacion

**Objetivo**

Construir la parte del sistema que transforma problema difuso en cambio formalizable.

**Substeps**

1. Implementar `sdd-explore` reutilizando la disciplina util de `structure-scanner` y `deep-context-analyzer`.
2. Implementar `sdd-propose` para formalizar alcance, alternativa elegida, riesgos y rollback.
3. Implementar `sdd-spec` para comportamiento esperado, acceptance criteria y no-goals.
4. Implementar `sdd-design` para enfoque tecnico, impacto por modulo y riesgos de implementacion.
5. Implementar `sdd-tasks` para descomposicion ejecutable y ordenada.
6. Crear templates de artefactos para estas fases.
7. Implementar validaciones minimas por skill.
8. Asegurar que `spec` y `design` puedan correr en paralelo solo cuando `proposal` ya existe.

**Entregables**

- `sdd-explore`
- `sdd-propose`
- `sdd-spec`
- `sdd-design`
- `sdd-tasks`

**Dependencias**

- Stage 4

**Criterio de cierre**

- el sistema puede dejar un cambio completamente formalizado y listo para aplicar o quedar en estado `planned`

**Paralelizacion posible**

- despues de `proposal`, `sdd-spec` y `sdd-design` pueden desarrollarse en paralelo

## Stage 6. Ejecucion controlada del cambio

**Objetivo**

Convertir el plan formalizado en cambios reales sin perder control de scope ni trazabilidad.

**Substeps**

1. Migrar la logica util de `stage-executor` a `sdd-apply`.
2. Mantener Step 0 de snapshot/checkpoint antes de tocar codigo.
3. Implementar validacion de precondiciones y deteccion de desincronizacion codigo/plan.
4. Implementar analisis de impacto y deteccion de blast radius fuera de scope.
5. Definir batching y actualizacion de `tasks.md`, `apply-progress.md` y `state.yaml`.
6. Integrar `stage-qa` como control incremental obligatorio despues de cada batch relevante.
7. Persistir shortcuts y decisiones de continue/pause/replanificar.
8. Resolver manejo de working tree sucio y triggers interactivos.

**Entregables**

- `sdd-apply`
- `stage-qa`
- progresion real por batch con trazabilidad

**Dependencias**

- Stage 5

**Criterio de cierre**

- el sistema puede ejecutar al menos un batch aprobado y dejar evidencia consistente de progreso

**Riesgo principal**

- meter demasiada inteligencia nueva en `sdd-apply` y romper la cualidad mas fuerte heredada de v1: control estricto del scope

## Stage 7. Verificacion final y archivado

**Objetivo**

Cerrar el cambio con evidencia real y trazabilidad de auditoria.

**Substeps**

1. Implementar `sdd-verify` con matriz de compliance contra `spec.md` y `tasks.md`.
2. Resolver deteccion/uso de comandos de test, build, lint y type-check desde `config.yaml`.
3. Definir verdicts y severidades de `verify-report.md`.
4. Implementar `sdd-archive` con guardrails estrictos.
5. Mover cambio activo a `openspec/changes/archive/YYYY-MM-DD-{change-name}/`.
6. Generar `archive-report.md`.
7. Implementar excepcion correcta para `planner`: sin archive.
8. Dejar hook opcional para `judgment-day` en cambios sensibles.

**Entregables**

- `sdd-verify`
- `sdd-archive`
- cierre auditable del cambio

**Dependencias**

- Stage 6

**Criterio de cierre**

- cualquier cambio implementado puede terminar con evidencia, verdict y archivo consistente

## Stage 8. Wrapper y packaging minimo para Codex

**Objetivo**

Volver usable el sistema nuevo en el host actual sin abrir todavia el frente multi-host completo.

**Substeps**

1. Crear wrapper o ejemplo operativo para Codex a partir del orquestador canonico.
2. Documentar como invocar `sdd-init` y luego el orquestador.
3. Crear ejemplo minimo de flujo sobre un repo de prueba o ejemplo local.
4. Definir convenciones de instalacion local dentro del repo.
5. Validar que el wrapper no duplique reglas que ya viven en las skills o en `_shared`.

**Entregables**

- example/wrapper de Codex
- docs minimas de uso
- entrada operativa real para probar v2

**Dependencias**

- Stage 7

**Criterio de cierre**

- se puede correr v2 en Codex sin depender de interpretacion informal del plan

## Stage 9. Multi-host y exports legacy

**Objetivo**

Agregar portabilidad y compatibilidad derivada solo despues de tener un nucleo estable.

**Substeps**

1. Crear wrappers equivalentes para Claude, Cursor u otros hosts si sigue siendo necesario.
2. Evaluar scripts de setup/install.
3. Implementar export opcional a `SURVEY` y `PLAN` como vistas derivadas, no como artefactos canonicos.
4. Evaluar soporte real para `hybrid` y `none`.
5. Verificar que no aparezca drift semantico entre hosts.

**Entregables**

- wrappers adicionales
- exports opcionales
- extensiones no fundacionales

**Dependencias**

- Stage 8

**Criterio de cierre**

- el nucleo no cambia y las extensiones no generan duplicacion de contratos

**Opcional**

- si el objetivo inmediato es tener v2 util en Codex, este stage puede diferirse completo

## Stage 10. Validacion end-to-end y hardening

**Objetivo**

Probar que el sistema funciona como sistema, no solo como suma de prompts y skills.

**Substeps**

1. Ejecutar escenarios completos por objetivo: `new-feature`, `bug-fix`, `planner`, `refactor-rework`.
2. Probar al menos los modos `lite`, `standard` y `deep`.
3. Probar resume desde `state.yaml`.
4. Probar errores de bootstrap faltante o vencido.
5. Probar desincronizacion entre artefactos y codigo.
6. Probar fallo de `verify` y bloqueo de `archive`.
7. Revisar token discipline, claridad de checkpoints y verbosidad del orquestador.
8. Ajustar docs, contracts y templates segun hallazgos.

**Entregables**

- matriz de escenarios probados
- lista de bugs y ajustes de hardening
- criterio claro de "v2 usable"

**Dependencias**

- Stage 8

**Criterio de cierre**

- el sistema puede sostener un ciclo real de trabajo de punta a punta sin apoyarse en supuestos informales

---

## 7. Alternativas y opciones con recomendacion

| Tema | Opcion A | Opcion B | Recomendacion |
|---|---|---|---|
| Lugar de implementacion | Implementar directo en roots globales `skills/` y `agents/` | Incubar todo en `sdd/sdd-v2` | Recomiendo `sdd/sdd-v2` primero. Reduce riesgo y separa v2 de v1. |
| Persistencia inicial | `openspec` solamente | `openspec + hybrid + none` desde el dia 1 | Recomiendo `openspec` operativo primero y dejar hooks para el resto. |
| Documento de contexto de proyecto | `.sdd/project-map.md` | `PROJECT_INDEX.md` host-specific | Recomiendo `.sdd/project-map.md` como canonico. |
| `archive` MVP | mover carpeta + `archive-report.md` | mover carpeta + merge inmediato a specs globales | Recomiendo el cierre simple primero; el merge global puede venir despues. |
| `git-checkpoint` | embebido en `sdd-apply` | skill separada desde el arranque | Recomiendo embebido primero y extraer luego si de verdad simplifica. |
| Compatibilidad legacy | sin exports `SURVEY`/`PLAN` al inicio | export derivado desde la primera version | Recomiendo diferir exports para no recentralizar el sistema en artefactos viejos. |
| Packaging | Codex primero | multi-host desde el inicio | Recomiendo Codex primero. La portabilidad se prueba mejor sobre un nucleo ya estable. |
| `hybrid` | backlog opcional | feature bloqueante del MVP | Recomiendo backlog opcional. |

---

## 8. Orden recomendado de ejecucion real

Si hubiera que empezar manana, el orden correcto seria este:

1. Stage 0
2. Stage 1
3. Stage 2
4. Stage 3
5. Stage 4
6. Stage 5
7. Stage 6
8. Stage 7
9. Stage 8
10. Stage 10
11. Stage 9 solo si sigue siendo necesario

Motivo:

- primero se congelan contratos
- despues bootstrap y orquestacion
- despues formalizacion
- recien despues ejecucion, verify y archive
- por ultimo packaging y extensiones

No conviene adelantar `sdd-apply`, `sdd-verify` ni wrappers multi-host antes de Stage 2 y Stage 4.

---

## 9. Resumen final

El relevamiento de `CODE_NEW_SDD_2.md` esta bien orientado y, en lo importante, ya tomo las decisiones correctas.

La implementacion del nuevo SDD v2 no necesita otra vuelta de arquitectura; necesita disciplina de secuencia.

La recomendacion final es construir v2 como un sistema encapsulado dentro de `sdd/sdd-v2`, con este orden:

- fundacion y contratos
- bootstrap estable
- orquestador con maquina de fases
- skills core de formalizacion
- apply con control de scope
- verify real y archive auditable
- wrapper minimo para Codex
- multi-host y exports solo despues

Si este orden se respeta, la v2 puede nacer mas profesional que `agents-plan-v1` sin perder lo mejor de v1: control operativo, criterio de ejecucion y checkpoints utiles.

---

## 10. Tabla de status y seguimiento

| ID | Stage | Depende de | Habilita | Opcional | Status actual |
|---|---|---|---|---|---|
| S0 | Fundacion y cierres de arquitectura | - | S1, S2, S3, S4 | No | Resuelto a nivel plan |
| S1 | Skeleton del paquete v2 | S0 | S2 | No | No iniciado |
| S2 | Contratos compartidos y schemas | S1 | S3, S4, S5, S6, S7 | No | No iniciado |
| S3 | Bootstrap (`project-map-init`, `skill-registry`, `sdd-init`) | S2 | S4, S5, S6, S7, S10 | No | No iniciado |
| S4 | Orquestador principal y motor de fases | S3 | S5, S6, S7, S8, S10 | No | No iniciado |
| S5 | Discovery y formalizacion (`explore`, `propose`, `spec`, `design`, `tasks`) | S4 | S6, S10 | No | No iniciado |
| S6 | Ejecucion controlada (`sdd-apply`, `stage-qa`) | S5 | S7, S10 | No | No iniciado |
| S7 | Verificacion final y archivado (`sdd-verify`, `sdd-archive`) | S6 | S8, S10 | No | No iniciado |
| S8 | Wrapper y packaging minimo para Codex | S7 | S10, S9 | No | No iniciado |
| S9 | Multi-host y exports legacy | S8 | ampliacion futura | Si | Backlog opcional |
| S10 | Validacion end-to-end y hardening | S8 | release usable | No | No iniciado |

### Lectura de dependencias

- S2 bloquea casi todo el sistema: no conviene saltearlo.
- S3 y S4 forman la base runtime real: bootstrap + orquestador.
- S5 debe existir antes de S6 porque `apply` no debe trabajar sin artefactos formales.
- S7 depende de S6 porque `verify` y `archive` no tienen sentido sin ejecucion real.
- S8 es obligatorio porque el host actual es Codex.
- S9 es totalmente diferible.
- S10 es el gate real para considerar que v2 esta lista para uso serio.
