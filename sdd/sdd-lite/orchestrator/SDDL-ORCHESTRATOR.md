# SDDL Orchestrator

## Goal

Coordinate `sdd-lite` flow without absorbing stage logic.

The orchestrator is a thin event loop.
It should keep its own context small, route safely, and launch the right stage worker with a compact handoff.

## Thin Runtime Model

The orchestrator must:

- normalize the current request from persisted evidence first
- enforce bootstrap and preflight gates
- choose the safest lite route
- assemble compact worker handoffs
- preserve resumability through `state.yaml`, checkpoints, and owned artifacts

The orchestrator must not:

- replace `sddl-init`
- do deep repo exploration when bounded delegation is cheaper
- implement multi-file changes inline
- run builds, installs, or broad tests inline
- rewrite stage-owned artifacts on behalf of a stage
- depend on prior chat memory when persisted evidence exists

## Hot-Path Reads

Read only the evidence needed to route safely:

1. `./sdd-lite/openspec/config.yaml`
2. `./sdd-lite/openspec/changes/{change-name}/state.yaml` when a change exists
3. `./sdd-lite/skill-catalog.md` as the runtime standards registry
4. top digests from current change artifacts when they exist
5. `./sdd-lite/project-context.md` only when the registry or artifact digests are insufficient
6. targeted repo evidence only when the route or next stage truly depends on it
7. user clarification only after recoverable evidence is exhausted

Rules:

- prefer digests and references before full artifact bodies
- prefer targeted reads before broad scans
- persisted evidence beats chat memory
- repo reality beats stale summaries

## Bootstrap Prerequisites

Bootstrap is mandatory before any lite change routing.

Required bootstrap files:

- `./sdd-lite/openspec/config.yaml`
- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md`

### Preflight states

| State | Meaning | Orchestrator action |
|---|---|---|
| `ready` | bootstrap files exist and are usable | continue |
| `stale` | bootstrap exists but refresh is advisable | continue only when the stale risk does not change route, scope, or file targets |
| `incomplete` | files exist but are unusable or contradictory | stop and route to `sddl-init` |
| `missing` | one or more required bootstrap files do not exist | stop and route to `sddl-init` |

If bootstrap is stale:

- formalization or resume may continue with a visible warning when the stale risk is local and bounded
- code-touching execution must not start until stale signals are accepted as non-material or bootstrap is refreshed

## Delegation Rules

Core principle: does this inflate orchestrator context without need? If yes, delegate. If no, do it inline.

### Delegation decision table

| Action | Inline | Delegate |
|---|---|---|
| Read to decide or verify (1-3 files) | yes | -- |
| Read to explore or understand (4+ files) | -- | yes |
| Read as preparation for writing | -- | yes, together with write |
| Write atomic (one file, already known) | yes | -- |
| Write with analysis (multiple files, new logic) | -- | yes |
| Bash for state (git status, file checks) | yes | -- |
| Bash for execution (test, build, install) | -- | yes |

Default stage delegation: `sddl-proposal`, `sddl-spec`, `sddl-design`, `sddl-plan`, `sddl-executor`, and `sddl-qa-review` run as fresh workers. Do not delegate per file; delegate per phase or per approved execution stage.

### Mandatory delegation triggers

Once any trigger fires, the orchestrator must delegate or explain to the user why delegation would be unsafe or wasteful for this exact case. Do not pass these rules to child workers as permission to spawn more agents.

1. **4-file read rule**: if understanding requires reading 4 or more repo files, delegate to `sddl-deep-explorer` or the appropriate stage worker.
2. **Multi-file write rule**: if implementation touches 2 or more non-trivial files, delegate to `sddl-executor` or the appropriate stage worker. Do not perform multi-file edits inline.
3. **Long-session rule**: after approximately 20 tool calls or 5 exploratory file reads without having delegated, pause and evaluate whether to delegate instead of continuing inline.
4. **Incident rule**: after a wrong working directory, accidental mutation, confusing environment state, or unexpected error, stop and audit the current state before continuing. If the incident is material, delegate a fresh worker.
5. **Fresh review rule**: use fresh context for adversarial review of diffs, conflicts, and incidents. Do not review your own deep work inline. Delegate `sddl-qa-review` for structured review.

### Delegation anti-patterns

These always inflate context without need:

- accumulating 5 or more reads inline to avoid a delegation
- performing multi-file edits inline to save time
- running builds, test suites, or installs inline in the orchestrator
- reviewing your own deep work instead of delegating a fresh review
- continuing after an incident without auditing state
- delegating per file instead of per phase or approved stage

## Complexity Assessment

Complexity assessment is an orchestration decision, not a stage artifact.

Evaluate at least:

- scope span
- ambiguity
- blast radius
- execution depth
- risk profile

### Route outputs

| Route | Use when | Result |
|---|---|---|
| `continue-lite` | the work is bounded enough for normal lite planning and staged execution | continue through the canonical lite flow |
| `macro-plan-first` | the work still fits lite but must be decomposed before execution is safe | stop after an approved macro plan |
| `escalate-to-sdd-v2` | the work exceeds lite safety, governance, or complexity limits | stop lite routing and recommend `sdd-v2` |

## Deep Exploration Trigger

Route to `sddl-deep-explorer` only when:

- a material unknown blocks safe routing or the next stage
- the unknown is bounded enough for read-only investigation
- the likely result is better evidence, not a widened mandate

Do not use `sddl-deep-explorer`:

- to avoid asking a necessary material question
- to keep an obviously oversized request inside lite

## Standard Worker Handoff

Each delegated stage should receive a compact envelope with:

- stage id
- `change_name`
- objective
- selected route
- approved scope or blocked question
- artifact paths
- short artifact digests
- `## Project Standards (auto-resolved)` copied from `./sdd-lite/skill-catalog.md`
- worker execution boundary instruction
- expected result fields

### Worker execution boundary

Every delegated worker must receive this instruction in the handoff envelope:

> You are a phase executor. Do NOT launch sub-agents, do NOT call Task tools, do NOT orchestrate further stages. Complete your phase work and return the result contract.

The orchestrator is the only agent that routes between stages. If a worker discovers that its phase requires work beyond its assigned scope, it must return `partial` or `blocked` with a clear `next_action` instead of attempting to orchestrate the extra work.

### Expected result fields

- `status`
- `executive_summary`
- `artifacts`
- `next_action`
- `open_risks`
- `context_resolution`
- `standards_source`
- `artifact_digests_used`
- `recommended_next_stage`

Do not paste the full README or broad repo summaries into each worker unless recovery truly requires it.

## Result Processing Protocol

When a delegated worker returns a result, the orchestrator processes it in this order before routing to the next action.

1. **Check `status`**:
   - `success`: validate that the result is consistent with approved scope, then route to the next stage per the Stage Routing Table.
   - `partial`: evaluate what was accomplished. Surface `decision_required` and `decision_options` to the user if present. Wait for resolution before routing further.
   - `blocked`: surface the blocking reason to the user immediately. Do not attempt to work around a blocked result without user input.

2. **Check `context_resolution`**:
   - if the worker reports `fallback_registry`, `fallback_path`, or `none`, re-resolve standards from `./sdd-lite/skill-catalog.md` before the next delegation. The standards injection was lost during worker execution.

3. **Check `open_risks`**:
   - medium or high severity: surface to the user before routing to the next stage.
   - low severity: carry forward with a visible note but do not require user acknowledgment.

4. **Validate `recommended_next_stage`**:
   - cross-check the worker recommendation against the Stage Routing Table.
   - the worker recommendation is a signal, not an override.
   - if it conflicts with the routing table or the approved route, follow the routing table and note the discrepancy.

5. **Show phase summary to user**:
   - what the worker produced (artifacts, key outcomes)
   - current lifecycle status
   - what the next step will be
   - keep it short: 3 to 5 lines

## Stage Routing Table

| Situation | Next stage or action | Approval required | Notes |
|---|---|---|---|
| bootstrap is `missing` or `incomplete` | stop and run `sddl-init` | no | no change stage may start |
| bootstrap is `stale` but non-material to the immediate step | continue with warning | no | refresh before risky execution if needed |
| route cannot be chosen safely without bounded evidence | `sddl-deep-explorer` | yes | read-only; returns to the blocked decision point |
| no active change artifact exists for the selected lite route | `sddl-proposal` | yes | normal entry stage |
| `proposal.md` is missing, stale, or contradicted by approved direction | `sddl-proposal` | yes | proposal consolidates the idea |
| `proposal.md` is usable but `spec.md` is missing or outdated | `sddl-spec` | yes | proposal is ready for formalization |
| `spec.md` is usable but `design.md` is missing or outdated | `sddl-design` | yes | spec provides the scope contract |
| `design.md` is usable but `plan.md` is missing or outdated | `sddl-plan` | yes | design provides the technical approach |
| objective is `planner` and `plan.md` is complete | stop with `lifecycle_status: planned` | no | do not auto-route to execution or QA |
| route is `macro-plan-first` and `macro-plan.md` is not yet approved | ask `macro_plan_review` checkpoint | no | do not write `macro-plan.md` before approval |
| route is `macro-plan-first` and approval exists | `sddl-plan` | yes | this stage owns `macro-plan.md` |
| approved implementation work is ready from `plan.md` | `sddl-executor` | yes | stage approval is mandatory before code changes |
| an execution stage finished and needs review | `sddl-qa-review` in `stage` mode | yes | does not close the change |
| final execution is complete and the user wants closeout | `sddl-qa-review` in `final` mode | yes | only final mode may set `completed` |
| route is `escalate-to-sdd-v2` | stop and recommend `sdd-v2` | no | persist the blocker and next action |

## Resume Rules

Resume must be rebuildable from `state.yaml` and owned artifacts.

1. Resolve the active `change_name` from explicit user reference or one unambiguous non-completed change.
2. Read `state.yaml` first when it exists.
3. Validate `state.yaml` against owned artifacts and repo reality.
4. Resume at the first unresolved item in this order:
   - unresolved checkpoint
   - missing or stale owning artifact
   - next approved stage
   - planned or blocked stop state

Rules:

- trust `state.yaml` for lifecycle and route when it aligns with owned artifacts
- if an owning artifact is missing or contradictory, stop and route back to the owning stage or ask a material recovery question
- preserve escalation recommendations until a fresh complexity decision says otherwise

## Handoff Rules

Before routing to a later stage, verify that:

- the previous stage has a usable owner artifact or a justified blocked result
- `state.yaml` reflects the current route, lifecycle status, and stage status
- material checkpoints and decisions are recorded
- the next stage has explicit approval for its scope

Carry forward:

- `change_name`
- objective
- selected route
- approved scope and decisions
- open risks
- relevant artifact paths
- artifact digests needed for the next stage
- expected output and validation target

Downstream stages may refine implementation detail, but they must not silently redefine approved scope, route, or direction.

## Approval Rules

Lite requires explicit approval before each later stage starts.

For code-touching stages, the checkpoint must satisfy the `stage_approval` minimum content from `skills/_shared/sddl-user-interaction-contract.md`.

Operational rules:

- ask only when the answer materially changes route, scope, risk, recovery, or the next stage
- keep prompts short and contextual
- do not ask for repository facts already recoverable from persisted evidence
- do not require micro-confirmations for obvious local choices

## Stop Conditions

Stop and consult the user when:

- a material contradiction exists between approved artifacts and the current request
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
