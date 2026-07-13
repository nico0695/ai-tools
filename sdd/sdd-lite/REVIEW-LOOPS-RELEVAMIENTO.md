# Relevamiento: Nuevos Loops de Review para SDD-Lite

> Fecha: 2026-07-12
> Objetivo: incorporar 2 flujos nuevos a sdd-lite — **code review 4R** y **judgment day** (review adversarial con jueces paralelos) — integrados con el orquestador y usables de forma independiente.
> Fuentes: análisis de `sdd/sdd-lite/` (estado actual) y de `gentle-ai` (`internal/assets/` — agentes, skills, orquestadores).
> Estado: **IMPLEMENTADO** (2026-07-12). Este documento es el registro histórico del análisis; la fuente de verdad es el paquete mismo (`orchestrator/SDDL-ORCHESTRATOR.md`, `skills/`, `schemas/`, contratos `_shared/`).

## ⚠️ Correcciones aplicadas en la implementación final

Una validación posterior contra los archivos reales corrigió estos puntos del relevamiento (la implementación siguió las versiones corregidas):

1. **Instalación**: la premisa "cero mecánica nueva" era falsa — el symlink/copy de `sddl-init` solo manejaba `SKILL.md`. Se extendió el mecanismo a **directorio completo del skill** (incluye `references/`), y el contrato del ledger se ubicó en `skills/_shared/sddl-review-ledger-contract.md` (prefijo ya cubierto por la reescritura del copy).
2. **Fix routing (D7)**: `sddl-executor` NO se modificó — sus preconditions exigen proposal+spec+plan y su única fuente es la Stage Plan. **Todo fix pasa por `plan.md`**: rerun de `sddl-plan` con un "fix stage request" (ids confirmados del ledger) → `stage_approval` → executor. El "ciclo corto" standalone es un mini-change sembrado desde el ledger, no un bypass.
3. **Severidades (D3)**: el enum de `state.yaml` ya tenía 4 niveles — el mapeo final es `BLOCKER→critical`, `CRITICAL→high`, `WARNING→medium`, `SUGGESTION→low`. Se corrigió además el Result Processing del orquestador para incluir `critical` en `open_risks`.
4. **Veredicto de review**: `qa_summary` está atado a `mode: stage|final`; se agregó un bloque **`review_summary`** propio en `state.schema.yaml` (verdict, mode `4r|judgment-day`, round, counts, ledger_path).
5. **Standalone**: se registró `reviews_root` en `config.schema.yaml` (su `paths` tiene `additionalProperties: false`); el resume standalone es el **digest auto-descriptivo del ledger**, sin `state.yaml`.
6. **`review_gate` no era opcional**: 2 de sus 3 usos no tenían checkpoint type válido (`escalation_review` significa "escalar a sdd-v2", no adjudicar jueces). Se agregó al schema y al user-interaction-contract.
7. **Campo `findings`** de primera clase en la Common result structure del flow-contract (los findings no viajan como texto libre en `evidence`).
8. La tabla de 11 archivos quedó corta: la implementación final tocó también `sddl-qa-review`, `qa-report.md`, `sddl-plan`, `USER-GUIDE.md`, `USER_GUIDE_ES.md` (con purga de referencias fantasma a user-preferences), `sddl-user-interaction-contract.md` y `config.schema.yaml`.

---

## 1. Resumen Ejecutivo

### Qué se va a construir

| Flujo | Skill nuevo | Qué hace | Cuándo corre |
|---|---|---|---|
| **Code Review 4R** | `sddl-code-review` | Review de un diff con lenses Risk / Readability / Reliability / Resilience, triage por riesgo, ledger de findings, refuter para severos | Auto-triageado post-executor en el flujo SDD, o standalone sobre cualquier diff/PR |
| **Judgment Day** | `sddl-judgment-day` | 2 jueces ciegos en paralelo sobre un target inmutable; convergencia = corroboración (confirmed / suspect / escalated) | Solo opt-in explícito del usuario; reemplaza al 4R para ese target; modo `code` (diffs) y modo `artifact` (planning: design/plan/spec) |

### Decisiones clave validadas

1. **Skills-only** — ambos flujos son skills (protocolo + prompts en `references/`), NO agentes en disco. Consistente con sdd-lite, portable a Codex, cero mecánica nueva de instalación.
2. El skill es el **protocolo que ejecuta el orquestador**; los lenses/jueces son workers frescos genéricos read-only lanzados por el orquestador con el prompt inyectado.
3. `sddl-code-review` es **separado** de `sddl-qa-review`: el QA es dueño del ciclo de vida (stage/final, único cierre); el code-review produce un ledger que el QA final consume como evidencia.
4. Ledger con severidades `BLOCKER/CRITICAL/WARNING/SUGGESTION` + **severity floor** (solo BLOCKER/CRITICAL gatillan fixes; el resto es `info`, nunca bloquea).
5. **Refuter simplificado**: 1 solo pass, solo sobre findings severos inferenciales, solo en full-4R.
6. **Triage con umbrales numéricos**: trivial → 0 lenses; standard → 1 lens; hot-path o >400 líneas → 4R completo.
7. **Fix routing dependiente de contexto**: el orquestador interpreta (change abierto vs standalone, scope, magnitud) y sugiere — nunca auto-arregla.
8. **3 modos de ejecución por plataforma**: paralelo (Claude Agent tool), paralelo nativo o inline (Codex), inline secuencial (genérico).

---

## 2. Estado Actual de SDD-Lite (lo relevante)

- **Orquestador delgado** (`orchestrator/SDDL-ORCHESTRATOR.md`): thin event loop, rutea por Stage Routing Table según qué artefacto existe/está stale, delega workers frescos con envelope compacto (paths + digests + standards + worker boundary "no lances sub-agentes").
- **8 skills canónicos** con formato uniforme: frontmatter (`name`, `description` con "Triggered by the sddl orchestrator after X") + Goal / Scope / Reads / Writes / Workflow / Expected Output (`success`/`partial`/`blocked`).
- **Review existente**: solo `sddl-qa-review` (modos `stage`/`final`, read-only sobre código, veredictos `pass`/`pass_with_warnings`/`fail`, severidades `low`/`medium`/`high`). Ya existe la "fresh review rule" (reviews con contexto fresco) — la semilla conceptual de los jueces ciegos.
- **Reglas que condicionan el diseño**: workers no lanzan sub-agentes; solo se paralelizan tareas read-only independientes; nunca workers con escrituras solapadas; `stage_approval` obligatorio antes de tocar código.
- **No existe**: framework 4R, review multi-juez, ni loop de code-review independiente del QA.
- Hallazgos previos vigentes del review interno: falta rúbrica cuantitativa de routing (A1), la delegación asume Agent tool de Claude (C2), falta fast-track para cambios triviales. Los tres se atacan parcialmente con este diseño.

---

## 3. Hallazgos de Gentle-AI (referencia de diseño)

### 3.1 Reviewer 4R

- **No es una skill**: son 4 agentes lens (`review-{risk,readability,reliability,resilience}.md`) + 1 refuter + lógica de triage en el orquestador + contrato compartido `review-ledger-contract.md`.
- Lenses **read-only** (`tools: Read, Grep, Glob`) con reglas concretas Flag/Block/Require/Do-not-flag y un **precision gate**: "report a finding only if it is a real, user-impacting defect... when in doubt, stay silent". Findings de estilo prohibidos.
- **Triage determinístico**: trivial (docs/formato) → 0 lenses; standard → exactamente 1 lens (riesgo dominante); hot path (auth/security/payments) o >400 líneas → 4R completo.
- **Ledger**: filas `id / lens / location(path:line) / severity / status / evidence`. Severidades `BLOCKER|CRITICAL|WARNING|SUGGESTION`; status `open|fixed|verified|refuted|wont-fix|info`.
- **Budgets duros**: 1 sweep por lens (2 en full-4R); máx 2 fix rounds; lo abierto tras round 2 se reporta y el loop termina. "No loop-until-dry".
- **Refuter**: verificación adversarial de findings severos *inferenciales* (los deterministic no se refutan). Fan-out fijo: 1 refuter (standard) o 3 en paralelo con voto 2-de-3 (full-4R). Nunca 1 refuter por finding. Verdict malformado = el finding se mantiene.
- Cada finding lleva `evidence_class` (deterministic/inferential) y `causal_disposition` — **solo lo introducido/empeorado por el cambio puede bloquear**.

### 3.2 Judgment Day

- **Sí es una skill** provider-agnóstica (`skills/judgment-day/SKILL.md` + `references/prompts-and-formats.md`) + 3 agentes (`jd-judge-a`, `jd-judge-b`, `jd-fix-agent`).
- **Opt-in explícito** ("judgment day, dual review, adversarial review, juzgar"). Regla dura: *"Judgment Day replaces ordinary 4R for that target; never run both."*
- Mecánica: target inmutable → 2 jueces ciegos idénticos en paralelo (esperar a AMBOS, nunca juicio parcial) → cada juez devuelve JSON puro de findings → merge en frozen ledger.
- **Decision gates**: ambos coinciden en severo → **confirmed** (preguntar, luego fix); solo uno → **suspect** (se registra, NO se auto-arregla); se contradicen → **escalated** a humano; WARNING/SUGGESTION → `info`.
- Sin refuter: la convergencia de 2 jueces ES la corroboración.
- **Fix actor** único con permisos de escritura: solo IDs confirmados, work units atómicos con test result + rollback boundary; nunca agrega findings ni refactoriza fuera de scope.
- Máx 2 fix rounds; re-judgment scoped (jueces re-ven solo ledger congelado + fix delta). Terminales: `APPROVED ✅` / `ESCALATED ⚠️`.

### 3.3 Integración y plataformas

- El review **no es fase del grafo SDD** — es una operación separada post-implementación, con gate de lifecycle antes de commit/PR que valida el receipt sin lanzar lenses nuevos.
- Claude Code: agentes `.md` en `~/.claude/agents/` invocados con Agent tool. Codex: sin agentes en disco — `spawn_agent`/`wait_agent`/`close_agent` nativos si `multi_agent=true`, si no **modo inline secuencial** (el orquestador corre lenses/jueces secuencialmente en su propio contexto y mantiene el ledger él mismo, con las mismas reglas).

---

## 4. Diseño Propuesto para SDD-Lite

### 4.1 Estructura (skills-only)

```text
skills/
  sddl-code-review/
    SKILL.md                  # protocolo 4R: triage, lanzamiento de lenses, ledger, budgets, refuter
    references/
      lens-prompts.md         # prompts R1-R4 + prompt del refuter (con boundary read-only explícito)
      ledger-format.md        # schema del ledger + severidades + reglas de status
  sddl-judgment-day/
    SKILL.md                  # protocolo: target inmutable, jueces, decision gates, modos code/artifact
    references/
      judge-prompt.md         # prompt del juez (parametrizado A/B) + criterios por modo + verdict format
templates/artifacts/
  review-ledger.md            # template del artefacto ledger
```

**Modelo de ejecución** (ambos flujos): el orquestador ejecuta el protocolo del SKILL.md — lanza cada lens/juez como worker fresco genérico read-only (prompt inyectado desde `references/`), espera todos los resultados, mergea el ledger y lo persiste. Los workers devuelven filas de ledger (o JSON de findings); **solo el orquestador escribe**. Esto respeta el worker boundary, la regla de paralelización read-only y la regla de escrituras sin overlap, sin refactorizar nada existente.

### 4.2 Decisiones con alternativas (D1–D8)

#### D1. `sddl-code-review` separado de `sddl-qa-review` ✅

- **Elegida**: skill separado. Usable standalone sin change activo; no toca el skill más delicado del flujo; espeja a gentle-ai (review de código ≠ QA de fase).
- Descartada: extender `sddl-qa-review` con lenses — mezcla dos ejes distintos (QA valida el *cambio contra spec/plan*; el 4R valida el *diff contra calidad de código*) e infla el skill.
- **Deslinde**: `sddl-qa-review` sigue siendo el único cierre del ciclo de vida. El QA final **consume** el `review-ledger.md` como evidencia (sección "Review Evidence" en `qa-report.md`) en vez de repetir el análisis.

#### D2. Judgment day dual-mode: `code` y `artifact` ✅

- `mode: code`: juzga un diff/PR; reemplaza al 4R para ese target (regla de gentle-ai).
- `mode: artifact`: juzga `proposal.md`/`spec.md`/`design.md`/`plan.md` contra criterios de completitud, consistencia interna, gaps y riesgos. Mismo mecanismo, solo cambian target y bloque de criterios en `judge-prompt.md`.
- En modo artifact **no hay fix actor**: los findings confirmados alimentan un rerun del stage dueño (ej. gap confirmado en `design.md` → re-lanzar `sddl-design` con los findings en el envelope).
- Nota: el modo artifact es diseño propio (gentle-ai no lo tiene); costo marginal bajo, cubre el caso de uso "judgment day como planning reviewer".

#### D3. Severidades y ledger: adoptar escala de gentle-ai ✅

- Ledger: `severity: BLOCKER|CRITICAL|WARNING|SUGGESTION`, `status: open|fixed|verified|refuted|wont-fix|info`, más `evidence_class` (deterministic/inferential) y `causal_disposition` en modo code (solo lo introducido/empeorado bloquea).
- **Severity floor**: solo BLOCKER/CRITICAL entran al loop de fix; WARNING/SUGGESTION se reportan una vez como `info` y nunca bloquean ni se re-revisan. (Esto es lo que evita loops infinitos de nitpicks — requiere los 4 niveles; por eso se descartó reusar `low/medium/high` en el ledger.)
- `state.yaml` mantiene `low/medium/high` con mapeo fijo: BLOCKER/CRITICAL→high, WARNING→medium, SUGGESTION→low.
- Veredictos judgment-day → mapeo a los existentes: `APPROVED`→`pass`/`pass_with_warnings`, `ESCALATED`→`fail` + checkpoint de escalación.

#### D4. Persistencia del ledger ✅

- Con change activo: `./sdd-lite/openspec/changes/{change-name}/review-ledger.md` — artefacto **condicional** en el schema (mismo patrón que `macro-plan.md`).
- Standalone: `./sdd-lite/openspec/reviews/{target-slug}/review-ledger.md` (`target-slug` = `pr-{n}`, branch en kebab-case, o slug del target).

#### D5. Refuter simplificado ✅

- **Elegida**: 1 solo refuter pass, solo sobre findings BLOCKER/CRITICAL con `evidence_class: inferential`, solo en full-4R. Devuelve `corroborated|refuted|inconclusive` por finding; malformado/ausente = el finding se mantiene.
- Descartadas: paridad total con gentle-ai (3 refuters + voto 2-de-3 — demasiado para "lite"; es upgrade directo si aparecen falsos positivos) y sin refuter (deja el 4R full sin corroboración).
- Los findings deterministic no se refutan nunca.

#### D6. Triage con rúbrica numérica ✅

| Tier | Criterio | Lenses |
|---|---|---|
| Trivial | Solo docs/comentarios/formato/typos — cero código ejecutable y cero config | 0 (no corre review) |
| Standard | Resto | Exactamente 1 (riesgo dominante, ver tabla de señales) |
| Hot path / grande | Toca auth/seguridad/pagos/datos sensibles, **o** >400 líneas cambiadas | 4R completo + refuter |

Señales para el lens dominante: naming/estructura/refactor → readability; behavior/state/tests → reliability; integraciones/fallos parciales/recovery → resilience; seguridad/permisos/datos/dependencias → risk.

Budgets duros: 1 sweep por lens (2 en full-4R); **máx 2 fix rounds**; lo abierto tras round 2 se reporta al usuario y el loop termina.

#### D7. Fix routing dependiente de contexto ✅ (refinado con el usuario)

Tras findings confirmados, el orquestador **interpreta el contexto y sugiere** vía checkpoint — nunca auto-arregla, el usuario decide:

| Contexto | Sugerencia del orquestador |
|---|---|
| Change SDD activo, findings dentro del scope aprobado | Fix stage acotado con `sddl-executor` en el mismo change (solo IDs confirmados, work units atómicos, `stage_approval` mediante) |
| Change activo pero findings exceden el scope de spec/design | Reabrir etapas anteriores (re-run `sddl-design`/`sddl-plan` con findings en el envelope) o registrar como follow-up — usa el checkpoint `scope_change` existente |
| Standalone, findings acotados (≤2 archivos, scope evidente) | **Ciclo corto**: mini-change quick-fix directo a executor (habilita de paso el fast-track pedido en el review interno) |
| Standalone, findings sustanciales | Abrir un **nuevo change SDD** con `proposal.md` pre-poblado desde el ledger (los findings confirmados son el problem framing) |

Descartado: skill fix-actor dedicado tipo `jd-fix-agent` — duplicaría a `sddl-executor`, que ya tiene stop rules y approval gate. El re-review scoped (validar fix delta contra ledger congelado) lo hace un worker fresco con el prompt de lens/juez correspondiente.

#### D8. Estrategia por plataforma ✅

| Plataforma | Ejecución de lenses/jueces | Notas |
|---|---|---|
| Claude Code | Workers frescos **en paralelo** vía Agent tool | Camino default |
| Codex | `spawn_agent`/`wait_agent` si `multi_agent=true`; si no, inline secuencial | Al spawnear: los jueces son waited handoffs, nunca fire-and-forget |
| Genérico/otros | **Inline secuencial** siempre | El orquestador corre cada rol secuencialmente en su contexto y mantiene el ledger |

Ceguera de jueces en modo inline: correr juez A, persistir SOLO su JSON (descartar razonamiento), correr juez B sin mostrarle el resultado de A. Es más débil que la ceguera real (mismo modelo, misma sesión) — **limitación documentada honestamente** en el SKILL.md. Cada wrapper (`claude-orchestrator.md` / `codex-orchestrator.md` / `generic-orchestrator.md`) indica qué modo usar; esto resuelve el hallazgo crítico C2 del review interno (delegación Claude-only).

### 4.3 Integración con el orquestador (triggers y routing)

1. **Standalone (independiente del flujo SDD)**:
   - "review este diff/PR" / "code review 4R" → `sddl-code-review`.
   - "judgment day" / "dual review" / "adversarial review" / "juzgar X" → `sddl-judgment-day`.
   - No requieren change activo; persisten en `openspec/reviews/{target-slug}/`.
2. **En el flujo SDD** (filas nuevas en la Stage Routing Table):
   - Tras `sddl-executor` con etapa `success`: el orquestador triagea el diff de la etapa; si es standard/hot-path, **ofrece** (`interactive`) o encadena (`auto`) `sddl-code-review` antes del QA stage.
   - `sddl-judgment-day` **nunca se auto-rutea**: siempre opt-in del usuario. Si corre sobre un target, reemplaza al 4R para ese target (nunca ambos).
   - `sddl-qa-review` final consume el ledger como evidencia si existe.
3. **Planning**: en el checkpoint `macro_plan_review` (o a pedido tras design/plan), el orquestador ofrece `sddl-judgment-day mode=artifact` como validación fuerte de los artefactos de planning.

### 4.4 Plan de archivos a tocar

| # | Archivo | Cambio |
|---|---|---|
| 1 | `skills/sddl-code-review/` (SKILL.md + references/) | **Nuevo** — protocolo 4R |
| 2 | `skills/sddl-judgment-day/` (SKILL.md + references/) | **Nuevo** — protocolo judgment day |
| 3 | `templates/artifacts/review-ledger.md` | **Nuevo** — template del ledger (digest arriba + tabla de findings, patrón de `qa-report.md`) |
| 4 | `orchestrator/SDDL-ORCHESTRATOR.md` | Filas en Stage Routing Table; sección "Review Operations" (triage con rúbrica, modos por plataforma, fix routing D7); trigger opt-in de judgment-day |
| 5 | `skills/_shared/sddl-flow-contract.md` | Stage ids nuevos (`sddl-code-review`, `sddl-judgment-day`); buckets confirmed/suspect/escalated |
| 6 | `schemas/state.schema.yaml` | Enums `current_stage`/`stages`; artefacto opcional `review_ledger` (patrón `macro_plan`); checkpoint `review_gate` si se agrega |
| 7 | `skills/sddl-init/SKILL.md` | Lista de skills instalables: 8 → 10 |
| 8 | `templates/bootstrap/skill-catalog.md` | Registrar ambos skills, triggers y reglas compactas de review |
| 9 | `README.md` | Flujo estándar actualizado; sección de los 2 loops nuevos |
| 10 | `templates/wrappers/*.md` | Modo de ejecución de review por plataforma (paralelo / spawn / inline) |
| 11 | `skills/_shared/sddl-persistence-contract.md` | Ownership de `review-ledger.md` y ruta `openspec/reviews/` |

Orden sugerido de implementación: 3 → 1 → 2 (skills con el ledger definido) → 5/6/11 (contratos y schema) → 4 (orquestador) → 7/8/10 (instalación y wrappers) → 9 (docs).

---

## 5. Puntos Importantes y Riesgos

1. **Garantía read-only blanda**: sin agentes con `tools:` enforced, el "no edites" de lenses/jueces es prompt-level. Es el mismo nivel de garantía que sdd-lite ya acepta para `sddl-qa-review`. Mitigación: boundary explícito en cada prompt + el orquestador valida en el Result Processing que el worker no reporte escrituras fuera de ownership. **Puerta abierta**: si se necesita enforcement duro o modelos distintos por rol, se puede agregar una capa opcional de agentes solo-Claude como wrappers finos sobre los prompts de `references/` — sin cambiar el diseño base.
2. **Ceguera degradada en modo inline** (Codex sin multi_agent / genérico): jueces secuenciales en la misma sesión no son verdaderamente ciegos. Documentado como limitación; la alternativa (no ofrecer judgment-day fuera de Claude) fue descartada por romper la paridad multi-plataforma.
3. **Disciplina de budgets**: el valor del sistema depende de respetar los caps (1-2 sweeps, 2 fix rounds, severity floor). Deben estar en el SKILL.md Y en el bloque compacto del skill-catalog para que sobrevivan a la compresión de contexto.
4. **Precision gate es crítico**: sin él, los lenses generan ruido de estilo y el severity floor no alcanza. Copiar la formulación de gentle-ai ("when in doubt, stay silent"; findings de estilo prohibidos salvo que oculten un defecto).
5. **No mezclar los dos ejes de review**: 4R/judgment-day juzgan calidad del diff/artefacto; `sddl-qa-review` juzga el cambio contra spec/plan y es el único cierre. El ledger fluye hacia el QA, nunca al revés.
6. **Judgment day es caro** (2 jueces + posibles re-judgments): por eso es opt-in y nunca auto-ruteado. El 4R triageado es el default económico (la mayoría de los diffs corren 0 o 1 lens).

---

## 6. Checklist de Próximos Pasos

- [ ] Crear `templates/artifacts/review-ledger.md` (base: tabla de findings de `qa-report.md` + campos de gentle-ai)
- [ ] Escribir `sddl-code-review/SKILL.md` + `references/lens-prompts.md` + `references/ledger-format.md`
- [ ] Escribir `sddl-judgment-day/SKILL.md` + `references/judge-prompt.md` (con bloques de criterios `code` y `artifact`)
- [ ] Extender `sddl-flow-contract.md`, `state.schema.yaml`, `sddl-persistence-contract.md`
- [ ] Agregar sección "Review Operations" + filas de routing en `SDDL-ORCHESTRATOR.md`
- [ ] Actualizar `sddl-init` (10 skills), `skill-catalog.md`, wrappers y `README.md`
- [ ] Probar: (a) 4R standalone sobre un diff trivial/standard/hot-path, (b) judgment-day `mode=artifact` sobre un `design.md`, (c) flujo completo con code-review post-executor y QA final consumiendo el ledger
