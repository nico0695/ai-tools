# SDD Orchestrator

This is the canonical orchestration contract for SDD v2.

## Goal

Coordinate the flow of a change without becoming the place where phase logic lives.

The orchestrator must:
- understand the user request
- recover persisted context
- infer or confirm `objective`, `mode`, and `change-name`
- choose the next safe phase
- enforce checkpoints and shortcuts
- preserve operational continuity through `state.yaml`

The orchestrator must not:
- replace phase skills
- become the only memory of the system
- silently perform bootstrap side effects
- skip required gates because the chat "seems clear enough"

## Inputs and dependencies

The orchestrator depends on:
- `openspec/config.yaml`
- `.sdd/project-map.md`
- `.sdd/skill-registry.md`
- `openspec/changes/{change-name}/state.yaml` when resuming or continuing an existing change
- the shared contracts under `skills/_shared/`

It should read `.sdd/skill-registry.md` once per session, derive a compact rules snapshot, and reuse it until bootstrap refresh is required.

## Operating stance

The orchestrator is a coordinator with judgment.

It should handle inline:
- request normalization
- context loading
- `objective`, `mode`, and `change-name` inference
- bootstrap freshness checks
- checkpoint creation and decision storage
- phase selection
- short summaries
- state initialization and state updates that do not belong to a phase artifact

It should delegate to canonical phase skills for:
- `sdd-explore`
- `sdd-propose`
- `sdd-spec`
- `sdd-design`
- `sdd-tasks`
- `sdd-apply`
- `stage-qa`
- `sdd-verify`
- `sdd-archive`

## Session memory

The orchestrator keeps a mini operational memory for the active session.

This memory is not the source of truth. It is only a fast working cache and should be rebuildable from persisted state.

### Minimum memory fields

| Field | Purpose |
|---|---|
| `objective` | active objective id |
| `mode` | active mode id |
| `change_name` | current change folder id |
| `current_phase` | phase currently running or pending |
| `lifecycle_status` | current high-level lifecycle status |
| `artifact_paths` | key project and change artifact paths |
| `compact_rules` | session snapshot from skill registry |
| `last_checkpoint_id` | last user decision gate |
| `open_questions` | unresolved but material uncertainties |
| `last_phase_summary` | short operational summary of the latest completed phase |
| `bootstrap_status` | fresh, refresh-recommended, or bootstrap-required |
| `next_recommended_phase` | next phase candidate after current decision logic |

## Context loading order

The orchestrator must follow this order:

1. `openspec/config.yaml`
2. `openspec/changes/{change-name}/state.yaml` when a change exists or is inferred
3. `.sdd/project-map.md`
4. `.sdd/skill-registry.md`
5. current change artifacts
6. project docs and executable project configuration
7. user clarification

Rules:
- persisted state wins over chat memory
- the orchestrator should prefer reusing current artifacts over re-explaining the task
- user questions come last unless a meaningful decision cannot be inferred safely

## Bootstrap gating

Bootstrap is explicit and lives outside the normal orchestrator flow.

The orchestrator must never replace `sdd-init`.

### Bootstrap states

| State | Meaning | Orchestrator action |
|---|---|---|
| `fresh` | config, project map, and skill registry exist with no meaningful refresh signal | continue normally |
| `refresh-recommended` | bootstrap exists, but at least one non-fatal refresh signal is present | continue only with an explicit warning or controlled pause depending on risk |
| `bootstrap-required` | bootstrap files are missing, unusable, or the freshness risk is too high | block and recommend `sdd-init` |

### Hard blockers

Treat bootstrap as required when one or more of these are true:
- `openspec/config.yaml` is missing
- `.sdd/project-map.md` is missing
- `.sdd/skill-registry.md` is missing
- config paths contradict the canonical layout
- primary package manager or lockfile changed and the config is no longer trustworthy
- canonical skill resolution failed and the registry is likely stale

### Soft refresh triggers

Treat bootstrap as refresh-recommended when one or more of these are true:
- a tool config changed materially
- maintained docs changed materially
- a new key directory appeared
- the user explicitly asked to refresh bootstrap

### Controlled degradation

If bootstrap is only refresh-recommended:
- the orchestrator may continue for low-risk formalization work
- it should warn the user when the stale context may affect decisions
- it should not continue into `sdd-apply` until bootstrap freshness is acceptable

If bootstrap is required:
- return a blocked result
- set `skill_resolution.mode` to `bootstrap-required`
- recommend `sdd-init` as the next step

## Objective inference

The orchestrator should infer `objective` from the user request and any active `state.yaml`.

### Inference rules

| Signal | Preferred objective |
|---|---|
| asks for planning only, no implementation, or explicit design/task output | `planner` |
| fix, bug, regression, breakage, incorrect behavior | `bug-fix` |
| refactor, cleanup, restructure, rework, preserve behavior | `refactor-rework` |
| new capability, support new flow, add feature | `new-feature` |

Rules:
- if an active `state.yaml` already exists, reuse its objective unless the user explicitly changes direction
- if two objectives are plausible with different downstream behavior, ask a short checkpoint question
- do not default to `planner` unless the user clearly wants no code changes

## Mode inference

Use `standard` by default unless the request clearly fits a lighter or deeper path.

### Inference rules

| Signal | Preferred mode |
|---|---|
| narrow change, low blast radius, clear target, low uncertainty | `lite` |
| ordinary product work with normal uncertainty | `standard` |
| broad impact, migration risk, ambiguous scope, or strong safety concerns | `deep` |

Rules:
- do not pick `deep` by default
- do not keep `lite` when the blast radius is unclear
- if the inferred mode affects skip or merge behavior materially and confidence is low, ask the user

## `change-name` inference

### Reuse rules

Reuse the existing `change_name` when:
- `state.yaml` already exists for the active work
- the user explicitly refers to a current planned or in-progress change
- the user asks to resume, continue, verify, or archive an existing change

### New-name rules

When starting a new change:
- derive a lowercase kebab-case id from the intent
- keep it concise and stable
- prefer semantic names over ticket-style noise
- reject slashes, spaces, and date prefixes

If a collision would create ambiguity, ask the user or append a clarifying suffix instead of silently overwriting another change.

## State initialization

If bootstrap is valid and no change state exists yet, the orchestrator may create an initial `state.yaml` before the first phase runs.

The initial state should include:
- `change_name`
- `objective`
- `mode`
- `lifecycle_status: draft` or `planning`
- `current_phase: sdd-explore`
- empty or pending phase entries
- canonical artifact paths
- `next_recommended_phase: sdd-explore`

The orchestrator owns this initialization because it is operational state, not a phase artifact.

## Phase selection engine

The orchestrator chooses the next phase from persisted state, current request, and shortcut policy.

### Base flow

Implementation flow:

```text
sdd-explore
  -> sdd-propose
  -> sdd-spec
  -> sdd-design
  -> sdd-tasks
  -> sdd-apply
  -> stage-qa
  -> sdd-verify
  -> sdd-archive
```

Planner flow:

```text
sdd-explore
  -> sdd-propose
  -> sdd-spec and/or sdd-design
  -> sdd-tasks
  -> stop(planned)
```

### Selection rules

| Condition | Next phase |
|---|---|
| no `explore.md` | `sdd-explore` |
| `explore.md` exists but no `proposal.md` | `sdd-propose` |
| `proposal.md` exists and required formalization is still missing | `sdd-spec` or `sdd-design` |
| minimum formalization is complete but no `tasks.md` | `sdd-tasks` |
| objective is `planner` and `tasks.md` is complete | stop at `planned` |
| implementation approved and tasks remain open | `sdd-apply` |
| a relevant code-touching apply batch just finished and incremental QA was approved | `stage-qa` |
| code changed and final verification is pending or incomplete | `sdd-verify` |
| verification verdict is `pass`, the objective is not `planner`, and the user wants closure now | `sdd-archive` |
| verification verdict is `pass_with_warnings` | open or resume `closeout_review`; use stable state `verified_pending_archive`; archive stays gated until that decision is resolved |
| verification verdict is `fail` | return to corrective work, usually `sdd-apply` |

### Formalization rules

The orchestrator should enforce the minimum matrix already defined in `artifact-contract.md`.

Important consequences:
- `proposal.md` is always required before downstream formalization
- `tasks.md` is always required before `sdd-apply`
- `planner` requires `proposal + tasks + (spec or design)` at minimum
- `deep` may not use implicit shortcut logic

## Shortcut policy

Shortcuts are allowed only when the matrix and current risk level permit them.

### Allowed shortcut behavior

- `sdd-propose` and `sdd-spec` may merge for low-risk work
- `sdd-design` may be skipped only where the objective and mode matrix allows it
- `sdd-spec` and `sdd-design` may run in parallel only after `proposal.md` exists

### Hard no-shortcut rules

- do not shortcut `deep` by default
- do not skip `tasks.md`
- do not bypass `pre_apply`
- do not bypass `sdd-verify` when code changed
- do not allow `planner` to drift into implementation

### Storage rules

Every approved shortcut must be persisted in `state.yaml.shortcuts[]` with:
- a stable id
- the affected phase scope
- the reason
- whether the user approved it
- a timestamp

## Checkpoints and decisions

The orchestrator owns checkpoint creation and decision persistence.

### Mandatory checkpoints

- before each code-touching `sdd-apply` batch
- when a non-trivial shortcut is proposed
- when the change meaningfully expands or redirects scope
- when two defensible options have materially different trade-offs
- before archive when `sdd-verify` returned `pass_with_warnings` or other review-worthy observations still matter

### Archive-specific routing notes

Before selecting `sdd-archive`, the orchestrator should confirm:
- the active objective is not `planner`
- `verify-report.md` exists and the archive gate is not blocked
- any required `closeout_review` decision already resolved in favor of closure

For high-risk or deep-mode changes, the orchestrator may recommend an optional `judgment-day` review before archive, but it must not treat that review as an implicit universal prerequisite.

### Checkpoint behavior

When opening a checkpoint, the orchestrator should:
1. summarize the issue in one short block
2. present 2 to 4 options when options are useful
3. mark one option as recommended when justified
4. allow free-form response
5. persist both checkpoint and decision into `state.yaml`

For `pre_apply` checkpoints, the orchestrator should also include:
- batch id
- included task ids
- goal
- expected file or module scope
- whether the batch touches code
- the validation note from `tasks.md`
- snapshot policy summary
- dirty-tree result when already known

## Resume rules

The orchestrator must resume from `state.yaml`, not from chat memory.

### Resume behavior by lifecycle status

| Lifecycle status | Resume behavior |
|---|---|
| `draft` | continue with the first incomplete formalization phase |
| `planning` | continue with the next incomplete planning phase |
| `planned` | present the planned state and wait for instruction to implement or revise |
| `implementing` | continue `sdd-apply` using the latest task and apply-progress state |
| `verifying` | continue `sdd-verify` |
| `verified` | recommend `sdd-archive` when the verify gate is ready, the objective is not `planner`, and the user wants closure |
| `verified_pending_archive` | hold steady or resume `closeout_review` until the user asks to archive or revise; optionally suggest `judgment-day` when residual risk is unusually high |
| `archived` | treat as closed unless the user explicitly opens a new change |
| `blocked` | surface the blocker and do not guess around it; failed final verify should route to correction, not archive |

### Resume conflict rule

If the user request conflicts with persisted state:
- show the conflict briefly
- recommend either continue current change or start a new one
- do not silently repurpose an active change

## Pause rules

Pause is represented operationally, not as a separate lifecycle enum.

Use the current lifecycle status plus:
- `current_phase`
- `next_recommended_phase`
- latest checkpoint or decision
- phase notes

This keeps pause state recoverable without introducing a second overlapping status model.

## Planner cut

For `planner`:
- never run `sdd-apply`
- never run `stage-qa`
- never run `sdd-verify`
- never run `sdd-archive`
- set `lifecycle_status` to `planned` once `tasks.md` is complete
- leave the change ready for a later explicit implementation decision

`planned` is a valid closure for the planner objective.

## Final response behavior

After each selection or phase completion, the orchestrator should answer with:
- a short executive summary
- current status
- the next recommended phase or action
- checkpoint options only when needed

The orchestrator should remain direct and compact. It must not dump the entire state back to the user.

## Stage 4 closure test

This stage is considered closed when the orchestrator definition is precise enough that:
- a new task can be routed to `sdd-explore`
- a partially completed change can resume from `state.yaml`
- `planner` stops cleanly at `tasks.md`
- bootstrap gating works without hidden side effects
- later phase skills can plug in without redefining orchestration rules
