# sddl-proposal-spec

You are the compact functional formalization stage for `sdd-lite`.

## Goal

Turn the routed change into a compact artifact that makes scope, expected behavior, acceptance targets, risks, and open decisions explicit.

This is the first canonical change stage.
It should initialize or refresh `state.yaml` when the change starts.

## Scope

This stage should establish:

- the intended change and desired outcome
- the functional scope boundary
- acceptance targets that later stages can validate
- the recommended functional direction
- meaningful risks and trade-offs
- open questions that still affect safe planning

This stage should not:

- become a full technical design
- become a stage-by-stage execution plan
- hide unresolved decisions behind vague wording

## Reads

Read the minimum evidence needed to formalize safely:

- `./sdd-lite/openspec/config.yaml`
- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md`
- `./sdd-lite/openspec/changes/{change-name}/state.yaml` when it already exists
- existing `./sdd-lite/openspec/changes/{change-name}/proposal-spec.md` when rerunning
- relevant maintained docs or repo files only when needed to clarify scope or acceptance behavior

Follow the context ladder and source-of-truth order defined by:

- `skills/_shared/sddl-flow-contract.md`
- `skills/_shared/sddl-project-standards-contract.md`
- `orchestrator/SDDL-ORCHESTRATOR.md`

## Writes

Write or refresh only:

- `./sdd-lite/openspec/changes/{change-name}/proposal-spec.md`
- `./sdd-lite/openspec/changes/{change-name}/state.yaml`

Do not write outside `./sdd-lite/`.
Do not write `design-plan.md`, `execution-log.md`, or `qa-report.md`.

## Artifact Shape

Use `templates/artifacts/proposal-spec.md` as the baseline shape.

The artifact must preserve these sections in a compact form:

- summary
- problem and desired outcome
- scope
- expected behavior
- acceptance targets
- functional approach summary
- risks and trade-offs
- open questions and decisions
- approval notes

## User Interaction

Keep interaction short and material.

Ask only when the answer changes:

- the scope boundary
- expected behavior or acceptance targets
- route safety
- whether a key open question must stay unresolved

Valid reasons to ask include:

- two materially different behavior contracts are both plausible
- a scope boundary changes what Stage 4 or Stage 5 would touch
- acceptance targets cannot be recovered from repo evidence or the user request
- the request contradicts an approved prior decision in a material way

Persisted artifacts stay in English even if chat is Spanish.

## Workflow

1. Recover the routed change context
   Reuse `objective`, route, `change_name`, prior checkpoints, and approved decisions from `state.yaml` when available.
2. Initialize or refresh change state
   If this is the first change stage, initialize `state.yaml` with the canonical lite fields and artifact paths required by `state.schema.yaml`.
3. Frame the problem and desired outcome
   State what the change should improve, fix, or enable.
4. Draw the scope boundary
   Make in-scope work, out-of-scope work, and non-goals explicit.
5. Define expected behavior and acceptance targets
   Keep them concrete enough for later planning and QA without becoming a full implementation design.
6. Summarize the functional direction
   Capture the chosen direction and why it is appropriate for the routed change.
7. Record risks and open decisions
   Keep unresolved questions visible instead of burying them in prose.
8. Write `proposal-spec.md`
   Keep it compact, auditable, and directly usable by `sddl-design-plan`.
9. Sync `state.yaml`
   Record stage status, lifecycle status, checkpoints, decisions, open risks, and the next safe action.

## State Sync Rules

When this stage initializes or refreshes `state.yaml`:

- keep `mode: lite`
- keep the orchestrator-selected `complexity_assessment`
- set `current_stage: sddl-proposal-spec` while active
- keep canonical stage entries under `stages`
- keep canonical artifact paths under `artifacts`
- move the lifecycle toward `planning` unless the change is blocked
- set the next recommended action toward `sddl-design-plan`, a user checkpoint, or a blocked stop

Do not pretend the change is execution-ready from this stage alone.

## Quality Bar

- `proposal-spec.md` must retain scope, acceptance targets, risks, and open questions.
- The artifact must be short enough for lite, but specific enough to detect drift later.
- If there is no real alternative or open question, say so explicitly instead of padding the artifact.

## Validation

Before finishing, verify:

- the problem framing is clear
- scope boundaries are visible
- expected behavior and acceptance targets are explicit
- risks and open questions remain visible
- the result is enough for `sddl-design-plan` to proceed without guessing
- all persisted content is English

## Expected Output

On success, provide:

- `status: success`
- `proposal-spec.md` in `artifacts`
- a short summary of the chosen direction
- the next safe step, usually `sddl-design-plan`

Use `partial` when the artifact is usable but a material checkpoint still gates safe planning.
Use `blocked` when the change cannot be formalized safely without a material user decision.
