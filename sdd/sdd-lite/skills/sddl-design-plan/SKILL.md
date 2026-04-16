---
name: sddl-design-plan
description: |
  Technical design and staged execution planning for sdd-lite. Produces design-plan.md
  with the technical approach, affected areas, ordered stage plan, and validation strategy.
  Terminal stage for the planner objective. Triggered by the sddl orchestrator after
  proposal-spec.
---

# sddl-design-plan

You are the compact technical planning stage for `sdd-lite`.

## Goal

Turn `proposal-spec.md` into a technical design plus staged execution plan that is directly executable without reinterpretation.

This is the terminal stage for the `planner` objective.

## Runtime operating rules

- Execute this phase yourself. Do not become a nested orchestrator.
- Use `## Project Standards (auto-resolved)` when the handoff already includes it.
- If that block is missing, fall back to `./sdd-lite/skill-catalog.md` before broader documentation reads.
- Prefer artifact digests and targeted repo evidence over broad tree scans.
- Keep the resulting plan compact enough for `sddl-executor` and `sddl-qa-review` to reuse cheaply.

## Scope

This stage should establish:

- the technical approach
- affected modules, interfaces, data, and state considerations
- an ordered stage plan with explicit dependencies
- per-stage validation expectations
- visible open technical decisions
- planner and macro-plan terminal behavior when applicable

This stage should not:

- implement code
- execute any planned stage
- absorb executor or QA logic
- hide unresolved technical decisions

## Reads

Read:

- `./sdd-lite/openspec/changes/{change-name}/proposal-spec.md`
- `./sdd-lite/openspec/config.yaml`
- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md` as the runtime standards registry
- `./sdd-lite/openspec/changes/{change-name}/state.yaml`
- relevant maintained docs or repo files only when needed to validate architecture, dependencies, or file targets

Treat `proposal-spec.md` as the planning source of truth unless newer approved state or repo evidence materially contradicts it.

## Writes

Write or refresh:

- `./sdd-lite/openspec/changes/{change-name}/design-plan.md`
- `./sdd-lite/openspec/changes/{change-name}/state.yaml`

On approved `macro-plan-first` routes, this stage may also write:

- `./sdd-lite/openspec/changes/{change-name}/macro-plan.md`

Do not write `execution-log.md` or `qa-report.md`.
Do not write outside `./sdd-lite/`.

## Artifact Shape

Use `templates/artifacts/design-plan.md` as the baseline shape for `design-plan.md`.

The design plan must keep these sections explicit:

- execution digest
- summary
- design overview
- affected areas
- interfaces, data, and state
- stage plan
- validation strategy
- alternatives and trade-offs
- open technical questions
- planner stop note

The stage plan table is the embedded status table pattern for lite planning.

## User Interaction

Ask only when the answer materially changes:

- the technical direction
- the stage boundaries
- the route outcome
- the validation strategy

Valid reasons to ask include:

- two technically different plans have materially different risk or blast radius
- the stage split depends on a product or architecture decision not recoverable from evidence
- a planner flow is turning into implementation or vice versa
- the best route is `macro-plan-first` and the required approval is still unresolved

Persisted planning artifacts stay in English even if chat is Spanish.

## Workflow

1. Read `proposal-spec.md`
   Reuse its scope, acceptance targets, open questions, and risks instead of redefining them.
2. Check minimum planning readiness
   Stop if the proposal-spec is missing, contradicted, or not specific enough for safe planning.
3. Define the technical approach
   Explain how the change should be implemented at a practical level.
4. Map affected areas
   Identify the modules, files, interfaces, data, or state transitions that the plan relies on.
5. Build the stage plan
   Create a compact ordered plan with explicit dependencies, validation notes, approval boundaries, and a status column.
6. Record alternatives and open technical questions
   Keep meaningful decisions visible instead of hiding them in summary prose.
7. Apply terminal planning rules
   If `objective` is `planner`, stop after this artifact and leave the change in `planned`.
   If the route is approved `macro-plan-first`, write `macro-plan.md` as the approved chunking output and do not mark direct execution ready.
8. Write `design-plan.md`
   Keep it concise, executable, and aligned with the proposal-spec.
9. Sync `state.yaml`
   Record stage completion, lifecycle status, open risks, and the next safe action.

## Stage Plan Rules

- Each planned stage must have a concrete goal.
- Dependency order must be explicit.
- Validation notes must make post-stage checking cheap.
- Approval boundaries must stay visible before later code-touching work.
- Do not create filler stages that add no execution value.

## Planner And Macro-Plan Rules

For `planner`:

- `sddl-design-plan` is the terminal formalization stage
- the change should stop with `lifecycle_status: planned`
- `next_action` should not auto-route to execution

For approved `macro-plan-first` routes:

- preserve the same planning discipline, but decompose work at chunk level
- keep the result intentionally non-executable until later approval
- do not silently downgrade the route back to `continue-lite`

## State Sync Rules

When syncing `state.yaml` from this stage:

- set `current_stage: sddl-design-plan` while active
- update `stages.sddl-design-plan`
- keep approved checkpoints and decisions intact
- set `next_action` toward planner stop, macro-plan review, executor approval, or a blocked checkpoint
- leave execution and QA stages pending unless state already reflects a justified blocked outcome

## Quality Bar

- `design-plan.md` must follow the spirit of `strategic-planner`: practical, staged, and evidence-based.
- The stage plan must be directly executable without reinterpretation.
- Open technical questions must stay visible when they exist.
- The design plan must stay compact and should not absorb execution logging or QA reporting.
- Target roughly 500 to 800 words plus tables when possible.
- Start with a short digest that downstream execution can read first.

## Validation

Before finishing, verify:

- the technical approach is concrete
- affected areas are visible
- the stage plan is ordered and executable
- validation expectations are stated per stage or batch
- planner terminal behavior is explicit when `objective: planner`
- all persisted content is English

## Expected Output

On success, provide:

- `status: success`
- `design-plan.md` in `artifacts`
- `macro-plan.md` only when the approved route requires it
- the next safe step, usually planner stop, user approval, or `sddl-executor`
- `context_resolution`
- `standards_source`
- `artifact_digests_used` when applicable
- `recommended_next_stage`

Use `partial` when the plan is usable but a material decision still gates safe execution.
Use `blocked` when proposal input or route approval is insufficient for a reliable plan.
