# agents-plan-v1 — Sistema Multi-Agente de Análisis y Migración Técnica

> Relevamiento completo del sistema. Versión v1.

---

## Índice

1. [Descripción General](#descripción-general)
2. [Mapa de Agentes](#mapa-de-agentes)
3. [El Orquestador: technical-orchestrator](#el-orquestador-technical-orchestrator)
4. [Interacción entre Agentes y Sub-agentes](#interacción-entre-agentes-y-sub-agentes)
5. [El Flujo Completo (State Machine)](#el-flujo-completo-state-machine)
6. [Protocolo de Comunicación (I/O)](#protocolo-de-comunicación-io)
7. [Sistema de Memoria](#sistema-de-memoria)
8. [Análisis Crítico: Pros, Contras y Mejoras](#análisis-crítico-pros-contras-y-mejoras)

---

## Descripción General

Este sistema implementa un **pipeline multi-agente** para gestionar tareas técnicas complejas: migraciones de arquitectura, refactoring masivo, resolución de deuda técnica, análisis de proyectos. El diseño central es una máquina de estados de 4 fases donde **ninguna fase puede saltarse sin aprobación explícita del usuario**.

El sistema produce dos artefactos persistentes como fuente de verdad:
- `SURVEY_[Topic].md` — relevamiento del estado actual del código
- `PLAN_[Topic].md` — roadmap ejecutable con stages y tabla de status

---

## Mapa de Agentes

| Agente | Archivo | Modelo | Rol | Scope |
|--------|---------|--------|-----|-------|
| `technical-orchestrator` | `technical-orchestrator.agent.md` | opus | Conductor principal | Orquestación y UX |
| `structure-scanner` | `structure-scanner.agent.md` | sonnet | Scanner de estructura | Read-only |
| `deep-context-analyzer` | `deep-context-analyzer.sub-agent.md` | opus | Análisis línea a línea | Read-only |
| `survey-generator` | `survey-generator.agent.md` | sonnet | Redactor técnico | Write (docs only) |
| `strategic-planner` | `strategic-planner.agent.md` | opus | Arquitecto de plan | Write (docs only) |
| `stage-executor` | `stage-executor.agent.md` | opus | Ejecutor de código | Write (code + plan) |
| `qa-validator` | `qa-validator.agent.md` | sonnet | Inspector de calidad | Read-only + Bash |

---

## El Orquestador: technical-orchestrator

### ¿Qué es y qué hace?

El `technical-orchestrator` es el **único punto de entrada** del sistema y actúa como Project Manager técnico. No lee ni escribe código directamente. Su función exclusiva es:

1. **Recibir el objetivo** del usuario (qué migrar, refactorizar, o analizar)
2. **Delegar** toda operación técnica a los sub-agentes especializados
3. **Sintetizar** los resultados en respuestas breves (máx. 3-4 líneas)
4. **Presentar opciones** al usuario antes de avanzar de fase
5. **Gestionar el estado** del workflow a través de los archivos SURVEY/PLAN (no la memoria del chat)

### Guardrails del orquestador

El orquestador tiene reglas de comportamiento muy estrictas:

- **Delegación absoluta**: Nunca escanea directorios, analiza código, ni escribe documentos él mismo.
- **Protección de contexto**: Los payloads JSON que retornan los sub-agentes nunca se imprimen en el chat. Solo se sintetizan.
- **Context Purge**: Cuando una fase se cierra (SURVEY o PLAN generado), esa fase queda sellada. El orquestador confia exclusivamente en el archivo generado.
- **Autorización explícita**: No avanza de fase sin aprobación del usuario.
- **Límite de 25 turnos**: Si el contexto se degrada, sugiere reiniciar la conversación referenciando los archivos existentes.
- **Herramienta Write restringida**: Solo puede usarse para guardar memoria del agente, nunca para crear código o documentos.

### Capacidad de Skip

- Si ya existe un `SURVEY_[Topic].md` → puede saltear a Fase 3
- Si ya existe un `PLAN_[Topic].md` → puede saltear a Fase 4

---

## Interacción entre Agentes y Sub-agentes

El orquestador invoca a cada agente con **parámetros estructurados explícitos** usando templates predefinidos. Cada sub-agente retorna un **JSON estructurado** que el orquestador sintetiza.

### Diagrama de flujo

```
Usuario
  │
  ▼
technical-orchestrator
  │
  ├─── Fase 1 ──► structure-scanner  (mapeo rápido)
  │               └─► deep-context-analyzer (análisis profundo)
  │                       └─► [JSON findings] ──► orquestador sintetiza
  │
  ├─── Fase 2 ──► survey-generator (recibe: raw_analysis_data)
  │               └─► escribe SURVEY_[Topic].md
  │                       └─► [JSON confirm] ──► orquestador confirma
  │
  ├─── Fase 3 ──► strategic-planner (lee: SURVEY_[Topic].md)
  │               └─► escribe PLAN_[Topic].md
  │                       └─► [JSON confirm] ──► orquestador resume stages
  │
  └─── Fase 4 (loop) ──► stage-executor (ejecuta 1 stage)
                          └─► qa-validator (valida cambios)
                                  └─► [JSON verdict] ──► orquestador reporta
                                          └─► (repite por cada stage)
```

### Contratos de I/O por agente

| Agente | Input clave | Output clave |
|--------|-------------|--------------|
| `structure-scanner` | target_directories, patterns_to_search | JSON: findings, god_files, circular_deps |
| `deep-context-analyzer` | target_files, documentation_files, analysis_goal | JSON: findings, dependency_map |
| `survey-generator` | raw_analysis_data, topic_objective, output_path | JSON: status, file_path |
| `strategic-planner` | survey_file_path, output_plan_path, user_directives | JSON: status, file_path |
| `stage-executor` | plan_file_path, stage_id, target_files | JSON: status, files_modified, alerts |
| `qa-validator` | modified_files, regression_docs, stage_executed | JSON: verdict, alerts, severity |

---

## El Flujo Completo (State Machine)

### Fase 1: Discovery & Analysis
1. Orquestador solicita objetivo y directorios al usuario
2. Invoca `structure-scanner` → mapeo de estructura
3. Invoca `deep-context-analyzer` → análisis de archivos críticos
4. Presenta hallazgos sintetizados y pregunta si generar Survey

### Fase 2: Documentation
1. Invoca `survey-generator` con los datos raw
2. Se genera `SURVEY_[Topic].md`
3. **FASE CERRADA** — los datos raw se purgan del contexto

### Fase 3: Strategic Planning
1. Recibe directivas del usuario (opcional)
2. Invoca `strategic-planner` con el SURVEY
3. Se genera `PLAN_[Topic].md`
4. **FASE CERRADA** — el survey se purga del contexto

### Fase 4: Execution & QA Loop
Por cada stage en el plan:
1. Lee la tabla de status del PLAN.md (source of truth)
2. Presenta el stage siguiente y **espera autorización**
3. Invoca `stage-executor` para ese stage
4. Invoca `qa-validator` inmediatamente después
5. Reporta resultado: ✅ Success / ⚠️ Warning / ❌ Error
6. Avanza solo si el usuario confirma

---

## Protocolo de Comunicación (I/O)

### Triggers de interactividad

Cada sub-agente tiene **triggers de escalado** que detienen la ejecución y requieren decisión del usuario:

| Trigger | Agente | Condición |
|---------|--------|-----------|
| Conflicto directiva vs realidad | `strategic-planner` | Las directivas del usuario contradicen un bloqueante del survey |
| Múltiples caminos válidos | `strategic-planner` | >1 estrategia válida con trade-offs distintos |
| Desincronización código/plan | `stage-executor` | El código no está en el estado que el plan espera |
| Efecto colateral masivo | `stage-executor` | El cambio afecta archivos fuera del scope del stage |
| Ambigüedad en instrucciones | `stage-executor` | Las instrucciones del plan son vagas o contradictorias |
| Critical/High en QA | `qa-validator` | Se detecta regresión confirmada o memory leak |
| Datos contradictorios | `survey-generator` | Scanner y analyzer producen datos incompatibles |
| Volumen alto (>100 findings) | `survey-generator` | Sin directiva de agrupamiento clara |

### Manejo de errores del orquestador

Si un sub-agente retorna error, el orquestador presenta:
- [A] Reintentar
- [B] Saltear y continuar
- [C] Abortar workflow

---

## Sistema de Memoria

Cada agente implementa **memoria persistente por proyecto**, guardada en archivos `.md` con frontmatter estructurado. La memoria se comparte vía control de versiones (excepto `survey-generator`, que usa memoria local).

| Agente | Tipo de memoria | Qué guarda |
|--------|----------------|------------|
| `technical-orchestrator` | project | Estructura del proyecto, preferencias de workflow del usuario |
| `structure-scanner` | project | Patrones recurrentes, anti-patrones comunes encontrados |
| `deep-context-analyzer` | project | Variables globales, hotspots de acoplamiento, archivos de alto riesgo |
| `survey-generator` | **local** | Estrategias de agrupamiento, naming conventions de categorías |
| `strategic-planner` | project | Patrones arquitectónicos, estrategias de resolución efectivas |
| `stage-executor` | project | Responsabilidades de archivos, resoluciones de triggers previos |
| `qa-validator` | project | Archivos frecuentemente flaggeados, reglas de regresión violadas |

---

## Análisis Crítico: Pros, Contras y Mejoras

### Pros

**Diseño arquitectónico sólido**
- Separación de responsabilidades muy clara: cada agente tiene un único propósito
- El principio de "external source of truth" (archivos, no chat) es correcto y robusto
- La máquina de estados explícita evita que el sistema avance sin control
- Protección activa del contexto del LLM (purge de fases, síntesis máx. 3-4 líneas)

**Seguridad y control**
- Ningún agente ejecuta código sin autorización explícita del usuario
- `stage-executor` es el único con permisos de write en código fuente
- `qa-validator` actúa como safety net antes de cada avance
- Rollback definido en caso de fallo parcial (`git checkout -- [files]`)

**Interactividad estructurada**
- Todos los agentes tienen triggers de escalado bien definidos con opciones concretas [A], [B], [C]
- Los agentes no adivina: si hay duda, escalan
- La detección de context drift (>25 turnos) y la sugerencia de reinicio es una solución pragmática

**Memoria institucional**
- El sistema de memoria por agente acumula conocimiento entre conversaciones
- Compartida por version control (excepto survey-generator)

---

### Contras

**Paths hardcodeados y no portables**
Los archivos de los sub-agentes están referenciados con rutas absolutas dentro del orquestador:
```
/Users/nicolasschmidt/Documents/SIA/widgets - tpl/widgets-builder/.claude/agents/...
```
Esto rompe el sistema en cualquier otro contexto o máquina. Las rutas deberían ser relativas al proyecto activo o configurables.

**Inconsistencia de naming**
- `deep-context-analyzer.sub-agent.md` usa el sufijo `.sub-agent.md`
- Todos los demás usan `.agent.md`
Sin distinción real entre "agent" y "sub-agent" en el sistema: todos se invocan igual vía el `Agent` tool.

**Inconsistencia de memoria**
- `survey-generator` tiene `memory: local` mientras todos los demás tienen `memory: project`
- Esto puede causar que el survey-generator "olvide" preferencias de agrupamiento que otros agentes sí recuerdan

**Orquestador con tools que no debería usar**
El orquestador declara `tools: Bash, Glob, Grep, Read, Write` pero sus guardrails dicen que no debe usarlos (excepto Write para memoria). Mejor sería solo declarar `tools: Write` para reforzar el contrato por diseño en lugar de por instrucción.

**No hay snapshot previo a la ejecución**
El `stage-executor` hace rollback con `git checkout -- [files]` en caso de fallo parcial, pero no hay una instrucción explícita de hacer un `git commit` o `git stash` *antes* de ejecutar el stage. Sin ese snapshot, el rollback puede tener consecuencias inesperadas si hay cambios no commiteados previos.

**Dependencia implícita en herramientas externas**
`qa-validator` ejecuta `pnpm tsc --noEmit`, `pnpm lint` y `pnpm vitest run` pero no valida primero que esas herramientas existan en el proyecto. En proyectos sin TypeScript o sin Vitest, esto generaría errores falsos.

**No hay fase de verificación post-completado**
El workflow termina cuando la tabla de status muestra todo "Done", pero no hay una fase de smoke test o verificación funcional del resultado final del proyecto completo.

---

### Cosas a Mejorar

**1. Parametrizar las rutas de los agentes**
En lugar de hardcodear rutas absolutas en el orquestador, usar una variable de entorno o una convención relativa al directorio `.claude/agents/` del proyecto activo.

**2. Unificar el naming convention**
Decidir un solo sufijo: `.agent.md` o `.sub-agent.md`. Si se quiere distinguir el orquestador de sus subordinados, usar una carpeta `sub-agents/` en lugar de un sufijo en el nombre de archivo.

**3. Pre-execution git snapshot**
Agregar en el protocolo del `stage-executor` un step previo: `git stash` o `git add -A && git commit -m "pre-stage-X checkpoint"` para garantizar rollback seguro.

**4. Validación de ambiente en qa-validator**
Antes de ejecutar `pnpm tsc`, `pnpm lint` o `pnpm vitest`, verificar que los scripts existen en `package.json`. Si no, omitirlos y documentarlo en el reporte.

**5. Estandarizar `memory: project` en survey-generator**
No hay razón técnica para que el survey-generator use memoria local si los demás agentes usan memoria de proyecto. Unificar.

**6. Límite de 25 turnos más robusto**
La detección de context drift basada en contador de turnos es frágil. Sería mejor que el orquestador se autoevalúe por señales de calidad (inconsistencias en sus respuestas, referencias a stages incorrectos) más que por un número fijo.

---

### Cosas a Agregar

**`dependency-checker` sub-agente**
Un agente que valide que las dependencias entre stages en el PLAN sean correctas antes de iniciar la Fase 4. Ejemplo: detectar si el Stage 3 depende del Stage 2 pero el Stage 2 está marcado como "Blocked".

**Modo dry-run para stage-executor**
Un parámetro `dry_run: true` que liste los cambios que haría sin aplicarlos, útil para revisión manual antes de la ejecución real.

**Fase 5: Smoke Test**
Una fase final opcional que ejecute tests de integración o un build completo del proyecto para validar que el conjunto de stages produjo un sistema funcional.

**Soporte para PLAN parciales**
Posibilidad de generar un PLAN solo para un subconjunto de findings del SURVEY (por prioridad, por módulo, por riesgo).

**Notificación de context drift proactiva**
En lugar de solo sugerirlo pasadas las 25 turns, que el orquestador emita una advertencia activa cuando detecte que está respondiendo con información inconsistente con el PLAN.md actual.

---

### Cosas a Quitar o Cambiar

**Rutas absolutas hardcodeadas en el orquestador**
Son un smell de diseño que hace el sistema frágil y no reutilizable. Eliminarlas en favor de rutas relativas o configuración externa.

**La restricción de idioma embedded**
La instrucción `The primary user communicates in Spanish` está hardcodeada en el orquestador. Mejor que el orquestador detecte el idioma dinámicamente (como ya hace) sin esa referencia fija que asume un usuario específico.

**El comentario `<!-- Keep these templates in sync... -->`**
Es un recordatorio de mantenimiento que debería estar en una guía de desarrollo de los agentes, no en el prompt del orquestador en producción.

---

## Resumen ejecutivo

El sistema `agents-plan-v1` implementa un pipeline multi-agente bien diseñado con separación de responsabilidades clara y mecanismos de control sólidos. Su mayor fortaleza es el modelo de autorización explícita y la protección del contexto del LLM mediante purge de fases y fuente de verdad externa (archivos). Sus principales debilidades son la falta de portabilidad por los paths hardcodeados, inconsistencias menores de naming y memoria, y la ausencia de un snapshot pre-ejecución que garantice rollback seguro.

Con los ajustes propuestos — especialmente la parametrización de rutas, el snapshot previo a ejecución y la unificación de naming — el sistema estaría listo para usarse en proyectos distintos al de origen sin modificaciones manuales.
