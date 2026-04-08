# Stage 6 Compact Handoff

## Purpose

This file is a compact continuity snapshot for the current Stage 6 work.
It exists so continuation does not depend on chat history alone.

## Date

- recorded_at: 2026-04-02

## User-confirmed decisions

- Do not create git commits automatically during pre-apply handling.
- Do not auto-stash.
- If a checkpoint or git action is needed, stop and ask the user first.
- Dirty working tree blocks `sdd-apply` by default.
- `sdd-apply` should use `Suggested Batches` in `tasks.md` as the canonical batch plan when available.
- If `Suggested Batches` is missing or weak, derive a small batch from tightly coupled adjacent tasks.
- `stage-qa` should run only for code-touching batches at `end-of-feature` or `critical-point`, or when the user explicitly requests it.
- `stage-qa` always requires explicit user confirmation before it runs.
- `tasks.md` keeps visible task and batch state.
- `apply-progress.md` keeps the batch execution and QA ledger.
- `state.yaml` keeps lifecycle, checkpoints, decisions, risks, and next-step routing.

## Stage 6 progress

### Completed

- `Stage 6A.1`
  - Implemented the operational contract for `sdd-apply`.
  - Replaced the placeholder `apply-progress.md` template.
  - Expanded `tasks.md` so execution can track task status, batch status, and QA checkpoint intent.

- `Stage 6A.2`
  - Aligned orchestrator and shared contracts with batch-scoped `pre_apply`.
  - Clarified that `state.yaml` is not the batch ledger.
  - Kept batch-level traceability in `tasks.md` and `apply-progress.md`.

- `Stage 6B.1`
  - Implemented the operational contract for `stage-qa`.
  - Added the `incremental_qa` checkpoint type.
  - Aligned `sdd-apply` handoff and `apply-progress.md` policy summary with the new incremental QA trigger rules.
- `Stage 6B.2`
  - Tightened the evidence integration between `stage-qa` and `apply-progress.md`.
  - Added explicit batch-level fields for QA checkpoint references, QA decision references, planned checks, executed checks, findings summary, and continuation recommendation.
  - Aligned `sdd-apply`, `stage-qa`, and `sdd-phase-common` with the new QA evidence expectations.

## Files changed so far

- `orchestrator/SDD-ORCHESTRATOR.md`
- `skills/_shared/artifact-contract.md`
- `skills/_shared/persistence-contract.md`
- `skills/_shared/user-interaction-contract.md`
- `schemas/state.schema.yaml`
- `skills/sdd-apply/SKILL.md`
- `skills/stage-qa/SKILL.md`
- `templates/artifacts/tasks.md`
- `templates/artifacts/apply-progress.md`

## Current contract highlights

### `sdd-apply`

- Batch-scoped execution only.
- One approved batch per invocation.
- Mandatory `pre_apply` checkpoint for each code-touching batch.
- Dirty tree blocks execution.
- Clean tree records metadata-only baseline reference.
- `stage-qa` is recommended, not automatic.

### `tasks.md`

- `Ordered Tasks` now include `Scope Hints` and `Status`.
- `Suggested Batches` now include `Touches Code`, `QA Checkpoint`, and `Status`.
- Recommended batch/task status values:
  - `pending`
  - `in_progress`
  - `completed`
  - `blocked`

### `apply-progress.md`

- Keeps the append-oriented batch ledger.
- Records:
  - approval checkpoint and decision references
  - baseline metadata
  - planned scope and actual files changed
  - sync and blast-radius notes
  - evidence
  - blockers and user-facing summary
  - `stage_qa_status`
  - QA checkpoint and decision references
  - explicit incremental QA block with planned checks, checks run, findings, and continuation recommendation

### `stage-qa`

- Triggered only for:
  - code-touching `end-of-feature` batches
  - code-touching `critical-point` batches
  - explicit user request after a code-touching batch
- Runs focused checks, not full-project final validation.
- Writes results back into `apply-progress.md` and operational summaries into `state.yaml`.
- Does not create `verify-report.md`.
- Does not replace `sdd-verify`.

## Open risks and follow-up

- `state.schema.yaml` was intentionally kept minimal; batch-level detail remains artifact-driven for now.
- `stage-qa` must remain incremental and should not drift into a second `sdd-verify`.
- Stage 7 is still fully pending: `sdd-verify`, `sdd-archive`, `verify-report.md`, and `archive-report.md` remain placeholders.

## Recommended next step

Start `Stage 7` in controlled slices:
- `Stage 7A`: `sdd-verify` + `verify-report.md` + verdicts + compliance matrix + command usage from `config.yaml`
- `Stage 7B`: `sdd-archive` + `archive-report.md` + archive guardrails + planner exception
