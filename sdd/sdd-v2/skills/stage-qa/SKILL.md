# stage-qa

You are the incremental validation phase for SDD v2.

## Goal

Run a fast, batch-scoped quality check after a relevant code-touching apply batch so issues surface early without pretending that final verification already happened.

This phase is intentionally smaller than `sdd-verify`.

## Scope

This phase should:
- validate the latest relevant code-touching batch
- use the batch validation note from `tasks.md`
- prefer the smallest useful set of checks
- record incremental QA evidence in `apply-progress.md`
- summarize whether the change looks safe to continue, risky, or blocked

This phase should not:
- modify application code
- create `verify-report.md`
- run automatically without explicit user confirmation
- replace final `sdd-verify`

## When to use

Use this phase when one of these is true:
- the latest completed batch is code-touching and has `QA Checkpoint: end-of-feature`
- the latest completed batch is code-touching and has `QA Checkpoint: critical-point`
- the user explicitly asks to run incremental QA after a code-touching batch

Do not use this phase:
- for purely documentary or planning batches
- as a mandatory gate after every small code batch
- as a substitute for final verification

## Reads

Read:
- `openspec/changes/{change-name}/tasks.md`
- `openspec/changes/{change-name}/apply-progress.md`
- `openspec/changes/{change-name}/state.yaml`
- `openspec/config.yaml`
- the files changed in the latest relevant batch
- `spec.md` when the batch validation note refers to a behavioral expectation

## Writes

Write or refresh:
- `openspec/changes/{change-name}/apply-progress.md`
- change `state.yaml`

This phase should not write code files.

## Approval and triggering rules

`stage-qa` is confirm-before-run.

The orchestrator should open a short incremental QA checkpoint before invoking this phase when:
- a relevant batch reached `end-of-feature` or `critical-point`
- or the user explicitly asked for incremental QA

That checkpoint should summarize:
- the batch id
- the changed scope
- the planned incremental checks
- why the check is useful now

Recommended options:
- run incremental QA now
- defer and continue
- stop and revise before more execution

## Validation selection rules

Start from the latest batch entry in `apply-progress.md` and the matching batch row in `tasks.md`.

Build the incremental validation set in this order:
1. targeted smoke checks implied by the batch goal
2. focused regression checks tied to the batch validation note
3. narrow test, lint, or type-check commands when they are clearly relevant

Rules:
- prefer focused checks over full-project validation
- do not default to full test, build, lint, and type-check matrix
- if the repo only exposes broad commands, surface that cost clearly in the checkpoint summary
- keep this phase fast enough to support iterative execution

## Result model

Record one of these incremental outcomes in the current batch log:
- `passed`
- `warning`
- `failed`

Interpretation:
- `passed`: no blocking signal found in the incremental checks that ran
- `warning`: non-blocking issues, gaps, or notable uncertainty remain
- `failed`: incremental validation found a blocker or a high-confidence regression signal

This outcome is not the final verify verdict.

## Output and persistence rules

### `apply-progress.md`

For the current batch, update or append:
- `stage_qa_status`
- `stage_qa_checkpoint_id` when a checkpoint gated execution
- `stage_qa_decision_id` when a user decision approved, deferred, or declined the run
- `Incremental QA.triggered_by`
- `Incremental QA.checks_planned`
- `Incremental QA.checks_run`
- `Incremental QA.findings_summary`
- `Incremental QA.continue_recommendation`
- `Incremental QA.qa_notes`
- commands or checks that ran
- evidence references
- findings summary
- recommended next action

Keep the QA write scoped to the current batch entry.
Do not create a second QA artifact for the MVP.

### `state.yaml`

Keep updates operational only:
- `current_phase`
- `phases.stage-qa`
- `open_risks` when a warning or failure exposes real risk
- `evidence` as a short summary when useful
- `next_recommended_phase`

Do not write a batch-by-batch QA ledger into `state.yaml`.

## Distinction from `sdd-verify`

`stage-qa` is:
- incremental
- batch-scoped
- intentionally selective
- useful for early alerts

`sdd-verify` is:
- final
- change-wide
- evidence-heavy
- mandatory when code changed

Passing `stage-qa` does not satisfy archive requirements.
Skipping `stage-qa` does not remove the need for `sdd-verify`.

## Validation

Before finishing, verify:
- the phase was actually triggered by a relevant code batch or explicit user request
- the checks run were proportional to the batch scope
- the result was recorded in `apply-progress.md`
- the next recommended action is explicit
- the summary does not imply final compliance closure

## Expected envelope

On success:
- `status: success`
- include `apply-progress.md` in `artifacts`
- include evidence for the checks that ran

Use `partial` when:
- incremental QA ran but returned `warning`
- only part of the intended checks could run safely
- the user deferred follow-up even though a warning exists

Use `blocked` when:
- the latest batch is not a valid trigger for `stage-qa`
- required approval to run incremental QA is missing
- incremental QA found a blocking failure
