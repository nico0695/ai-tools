# SDDL Orchestrator

## Goal

Coordinate `sdd-lite` flow without absorbing stage logic.

The orchestrator must:

- normalize the current request using persisted evidence first
- enforce bootstrap and preflight gates
- assess lite complexity and select the safest route
- choose the next safe stage or stop condition
- preserve resumability through `state.yaml`, checkpoints, and owned artifacts

The orchestrator must not:

- replace `sddl-init`
- invent runtime paths outside `./sdd-lite/`
- rewrite stage-owned artifacts on behalf of a stage
- depend on prior chat memory when persisted evidence exists
- bypass explicit approval before a later stage starts

## Inputs / Reads

Read only the evidence needed to route safely:

- `./sdd-lite/openspec/config.yaml`
- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md`
- `./sdd-lite/openspec/changes/{change-name}/state.yaml` when a change already exists
- current change artifacts when they exist:
  - `proposal-spec.md`
  - `design-plan.md`
  - `execution-log.md`
  - `qa-report.md`
  - `macro-plan.md`
- shared contracts under `sdd/sdd-lite/skills/_shared/`
- schemas under `sdd/sdd-lite/schemas/`
- maintained docs and executable project configuration only as supporting evidence

## Bootstrap Prerequisites

Bootstrap is mandatory before any lite change routing.

Required bootstrap files:

- `./sdd-lite/openspec/config.yaml`
- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md`

Required bootstrap conditions:

- `config.yaml` points only to the canonical lite runtime under `./sdd-lite/`
- bootstrap artifacts remain internally consistent with the approved layout
- bootstrap summaries are usable enough to recover stack, paths, conventions, and quality commands

### Preflight states

| State | Meaning | Orchestrator action |
|---|---|---|
| `ready` | required bootstrap files exist and are usable | continue |
| `stale` | bootstrap exists but repo evidence suggests refresh is advisable | continue only when the stale risk does not change route, scope, or file targets |
| `incomplete` | files exist but are structurally unusable, contradictory, or missing essential sections | stop and route to `sddl-init` |
| `missing` | one or more required bootstrap files do not exist | stop and route to `sddl-init` |

### Stale bootstrap rules

Treat bootstrap as `stale` when one or more of these are true:

- `config.yaml.bootstrap.refresh_recommended` is `true`
- observed manifests, lockfiles, or tool configs changed materially
- a new source root, test root, or config root appeared
- maintained docs changed in a way that may affect routing or standards
- the user explicitly asks to refresh bootstrap

If bootstrap is `stale`:

- formalization or resume may continue with a visible warning when the risk is local and bounded
- route selection may continue only if the stale data does not materially change scope, risk, or the next stage
- code-touching execution must not start until stale signals are either accepted as non-material or bootstrap is refreshed

If bootstrap is `missing` or `incomplete`:

- do not infer around the gap
- do not start any change stage
- return a blocked outcome and recommend `sddl-init`

## Context Loading Order

Load context in this order unless a stage contract requires narrower evidence:

1. `./sdd-lite/openspec/config.yaml`
2. `./sdd-lite/openspec/changes/{change-name}/state.yaml`
3. `./sdd-lite/project-context.md`
4. `./sdd-lite/skill-catalog.md`
5. current change artifacts in causal order:
   - `proposal-spec.md`
   - `design-plan.md`
   - `execution-log.md`
   - `qa-report.md`
   - `macro-plan.md` only when the selected route requires it
6. maintained docs and executable project configuration
7. user clarification

### Source-of-truth order

When evidence conflicts, prefer this order:

1. `state.yaml` for route, lifecycle, checkpoints, decisions, and next action
2. the owning stage artifact for semantic detail within that stage
3. executable project config and source tree reality for current standards or file targets
4. bootstrap summaries under `./sdd-lite/`
5. user clarification when recoverable evidence is exhausted or contradictory in a material way

Rules:

- persisted evidence beats chat memory
- repo reality beats stale summaries
- current change artifacts beat older summaries of the same work
- the user should only be asked after recoverable persisted evidence has been exhausted

## Complexity Assessment

Complexity assessment is an orchestration decision, not a stage artifact.

The assessment must be derived from:

- the current user request
- bootstrap artifacts
- `state.yaml` and persisted change artifacts when resuming
- lightweight repo evidence needed to estimate blast radius

The assessment must not rely on prior chat turns as hidden memory.

### Assessment dimensions

Evaluate at least these dimensions:

| Dimension | Continue-lite signal | Macro-plan-first signal | Escalate signal |
|---|---|---|---|
| scope span | one bounded area or a small set of related files | multiple areas or milestones needing ordered decomposition | broad cross-cutting change, migration, or unclear system-wide impact |
| ambiguity | one dominant interpretation and concrete acceptance targets | scope is understandable but needs sequencing before execution | core intent, constraints, or dependencies stay materially unclear |
| blast radius | local and reviewable in lite | too large for direct execution but still decomposable in the same repo | widening or hard-to-bound impact across subsystems or workflows |
| execution depth | one planning pass plus controlled execution | planning must stop at a macro plan before implementation is safe | requires deeper governance, broader discovery, or richer lifecycle than lite provides |
| risk profile | local validation is likely enough | risk is manageable only after chunking and approval | safety, migration, data, or interface risk is too high for lite |

### Route outputs

| Route | Use when | Result |
|---|---|---|
| `continue-lite` | the work is bounded enough for normal lite planning and staged execution | continue through the canonical lite flow |
| `macro-plan-first` | the work is still within lite intent but must be decomposed into approved chunks before direct execution | stop after an approved macro plan |
| `escalate-to-sdd-v2` | the work exceeds lite safety, governance, or complexity limits | stop lite routing and recommend `sdd-v2` |

## Route Selection Rules

Apply route selection in this order:

1. run bootstrap preflight
2. resolve whether the user is starting new work or resuming an existing change
3. reuse persisted `objective`, `change_name`, and route when `state.yaml` is active and the user has not materially changed direction
4. reassess complexity when new evidence expands scope, risk, or blast radius
5. choose one route:
   - `continue-lite`
   - `macro-plan-first`
   - `escalate-to-sdd-v2`

### Normal route rules

Choose `continue-lite` when:

- the work is bounded enough to describe and review in one lite plan
- no material contradiction requires a higher-order planning artifact
- remaining unknowns are either minor or can be answered by one bounded `sddl-deep-explorer` pass

Choose `macro-plan-first` when:

- direct execution would create material scope drift or blast-radius risk
- the work spans multiple logical chunks that should be approved before implementation
- a macro decomposition is enough to stay in lite, but direct stage execution is not yet safe

Choose `escalate-to-sdd-v2` when:

- the work behaves like a migration, large cross-cutting redesign, or broad coordination problem
- repeated contradictions, drift, or unknowns remain after bounded clarification
- the safe path requires a deeper lifecycle than `sdd-lite` offers

### Deep exploration trigger

Route to `sddl-deep-explorer` before final route or before the next stage only when:

- a material unknown blocks safe routing
- the unknown is bounded enough for read-only investigation
- the likely outcome is more evidence, not a widened mandate

Do not use `sddl-deep-explorer` to avoid asking a necessary material question.
Do not use it to keep a likely `escalate-to-sdd-v2` request artificially in lite.

## Stage Routing Table

| Situation | Next stage or action | Approval required | Notes |
|---|---|---|---|
| bootstrap is `missing` or `incomplete` | stop and run `sddl-init` | no | no change stage may start |
| bootstrap is `stale` but non-material to the immediate step | continue with warning | no | refresh before risky execution if needed |
| route cannot be chosen safely without bounded evidence | `sddl-deep-explorer` | yes | read-only; returns to the blocked decision point |
| no active change artifact exists for the selected lite route | `sddl-proposal-spec` | yes | this is the normal entry stage |
| `proposal-spec.md` is missing, stale, or contradicted by approved direction | `sddl-proposal-spec` | yes | proposal owns compact functional framing |
| `proposal-spec.md` is usable but `design-plan.md` is missing or outdated | `sddl-design-plan` | yes | planner also stops here |
| objective is `planner` and `design-plan.md` is complete | stop with `lifecycle_status: planned` | no | do not auto-route to execution or QA |
| route is `macro-plan-first` and `macro-plan.md` is not yet approved | ask `macro_plan_review` checkpoint | no | do not write `macro-plan.md` before approval |
| route is `macro-plan-first` and approval exists | `sddl-design-plan` | yes | `sddl-design-plan` owns `macro-plan.md` on this route |
| approved implementation work is ready from `design-plan.md` | `sddl-executor` | yes | stage approval is mandatory before code changes |
| an execution stage finished and needs stage review | `sddl-qa-review` in `stage` mode | yes | does not close the change |
| final execution is complete and the user wants closeout | `sddl-qa-review` in `final` mode | yes | only final mode may set `completed` |
| route is `escalate-to-sdd-v2` | stop and recommend `sdd-v2` | no | persist the blocker and recommended next action |

## Continue-lite Flow

Normal lite flow:

```text
preflight
  -> complexity assessment
  -> sddl-proposal-spec
  -> sddl-design-plan
  -> sddl-executor (approved stage-by-stage)
  -> sddl-qa-review (stage)
  -> sddl-executor / sddl-qa-review (stage) as needed
  -> sddl-qa-review (final)
```

Rules:

- each later stage requires explicit user approval before it starts
- `sddl-executor` only runs the next approved implementation stage, not the whole plan at once
- the orchestrator decides sequencing; each skill owns its internal method and artifact

## Deep Exploration On Demand

Deep exploration is a temporary support branch:

```text
blocked routing or blocked next stage
  -> sddl-deep-explorer
  -> return to the interrupted routing point or stage handoff
```

Rules:

- `sddl-deep-explorer` is read-only
- it narrows uncertainty but does not approve scope expansion by itself
- its findings become supporting evidence for the next routing decision

## Planner Terminal Rules

`planner` is an objective, not a special route.

Planner flow:

```text
preflight
  -> complexity assessment
  -> sddl-proposal-spec
  -> sddl-design-plan
  -> stop(planned)
```

Rules:

- `planner` ends after `sddl-design-plan`
- the orchestrator must set or preserve `lifecycle_status: planned`
- `sddl-executor` and `sddl-qa-review` are not auto-routed for planner closure
- any later shift from planner to implementation is a material direction change and requires reassessment plus new approval

## Macro-plan-first Route

`macro-plan-first` is a contractual lite route for work that is too large for direct execution but not yet outside lite.

Route behavior:

```text
preflight
  -> complexity assessment = macro-plan-first
  -> sddl-proposal-spec
  -> macro_plan_review checkpoint
  -> sddl-design-plan
  -> stop(planned)
```

Rules:

- `macro-plan.md` must not be created before explicit approval
- `sddl-design-plan` owns `macro-plan.md` on this route
- the route stops after the approved macro plan is written
- later execution requires a fresh approval cycle and may require a new complexity assessment

## Resume Behavior

Resume must be rebuildable from `state.yaml` and persisted artifacts.

### Resume rules

1. Resolve the active `change_name` from explicit user reference or from one unambiguous non-completed change.
2. Read `state.yaml` first when it exists.
3. Use artifact presence and ownership to validate that `state.yaml` still matches reality.
4. Resume at the first unresolved item in this order:
   - unresolved checkpoint
   - missing or stale owning artifact
   - next approved stage
   - planned or blocked stop state

### Resume cases

| State shape | Orchestrator behavior |
|---|---|
| `state.yaml` exists and aligns with artifacts | trust `state.yaml` for lifecycle and route, then load owning artifacts for detail |
| `state.yaml` exists but an owning artifact is missing or contradictory | stop and route back to the owning stage or ask a material recovery question |
| checkpoints are unresolved | resume at the pending user decision instead of guessing a next stage |
| route is `macro-plan-first` and the macro plan is still pending approval | hold on the checkpoint; do not continue planning silently |
| route is `escalate-to-sdd-v2` | preserve lite state, surface the escalation reason, and stop lite execution |
| no `state.yaml` exists yet | treat as new work unless the orchestrator must persist a blocked or escalated pre-stage outcome |

### State initialization boundary

Normal change initialization belongs to `sddl-proposal-spec`.

The orchestrator may create or refresh a minimal `state.yaml` only when:

- the selected route is `escalate-to-sdd-v2` before any stage starts
- a pre-stage blocked checkpoint must be resumable without chat memory

That minimal state should record only operational data needed for recovery:

- `change_name`
- `objective`
- `mode: lite`
- `complexity_assessment`
- `lifecycle_status`
- `current_stage`
- `stages`
- artifact paths
- checkpoints and decisions already taken
- `open_risks`
- `next_action`
- `created_at`
- `updated_at`

When this minimal state is persisted, it must still satisfy the current `state.schema.yaml`.
The orchestrator may keep semantic detail minimal, but it must not omit schema-required fields.

## Handoff Rules Between Stages

Before routing to a later stage, the orchestrator must verify that:

- the previous stage has a usable owner artifact or a justified blocked result
- `state.yaml` reflects the current route, lifecycle status, and stage status
- material checkpoints and decisions are recorded
- the next stage has an explicit approval for its scope

Each stage handoff must carry forward:

- `change_name`
- `objective`
- selected route
- approved scope and decisions
- open risks
- the exact artifact paths relevant to the next stage
- the expected output and validation target for that stage

Downstream stages may refine implementation detail, but they must not silently redefine approved scope, route, or direction.

## User Interaction Rules

Follow `sdd/sdd-lite/skills/_shared/sddl-user-interaction-contract.md`.

Operational rules:

- ask only when the answer materially changes route, scope, risk, recovery, or the next stage
- keep prompts short and contextual
- keep chat in `es` or `en` as supported by bootstrap, while persisted content stays English
- do not ask for repository facts already recoverable from bootstrap artifacts, `state.yaml`, or current change artifacts
- do not require micro-confirmations for obvious local choices

### Stage approval rule

Lite requires explicit approval before each later stage starts.

For code-touching stages, the checkpoint must satisfy the `stage_approval` minimum content defined in `sddl-user-interaction-contract.md`.
For non-code stages, explicit approval may be lighter, but it must still be specific to the next stage and its goal.

## Decision And Checkpoint Behavior

Do not redefine checkpoint schemas here.
Use the canonical checkpoint and decision shapes from:

- `sdd/sdd-lite/skills/_shared/sddl-user-interaction-contract.md`
- `sdd/sdd-lite/schemas/state.schema.yaml`

Orchestrator-specific rules:

- unresolved checkpoints block forward routing
- `macro_plan_review` is required before `macro-plan.md` is written
- `escalation_review` is required when the recommended path leaves lite, unless the user already explicitly asked to escalate
- approvals given before the first stage should be persisted by the first state write that follows

## Escalation Behavior

When the chosen route is `escalate-to-sdd-v2`, the orchestrator must:

- stop normal lite stage routing
- preserve any usable lite artifacts and decisions
- record the escalation reason in `complexity_assessment.summary`
- set `next_action.kind: escalate_to_sdd_v2`
- avoid claiming lite completion

If a lite change state already exists, preserve it and mark the change as blocked or escalated by recommendation rather than silently discarding work.

If the user narrows the request later, the orchestrator may reassess and return to lite only after a fresh complexity decision.

## Stop Conditions

Stop and consult the user when one or more of these are true:

- a material contradiction exists between approved artifacts and current request
- scope drift changes the intended outcome or affected areas materially
- direction changes from planning to implementation or from one objective to another
- the blast radius increases beyond the currently approved stage or route
- artifact recovery is ambiguous and cannot be resolved from persisted evidence

## Guardrails / Invariants

- runtime root is always `./sdd-lite/`
- artifact root is always `./sdd-lite/openspec/`
- no root-level `openspec/` is used by `sdd-lite`
- all persisted artifacts, contracts, schemas, and Markdown stay in English
- chat interaction may use `es` or `en`
- `macro-plan.md` exists only on approved `macro-plan-first` flows
- `sdd-lite` MVP does not define archive, git, PR, or issue workflows
- `sddl-deep-explorer` stays read-only
- resume and routing must be explainable from persisted state and artifacts
