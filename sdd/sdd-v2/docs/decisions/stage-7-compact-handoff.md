# Stage 7 Compact Handoff

## Purpose

This file is a compact continuity snapshot for the completed Stage 7 work.
It exists so continuation does not depend on chat history alone.

## Date

- recorded_at: 2026-04-02

## User-confirmed decisions preserved

- Do not touch files outside `/Users/nicolasschmidt/Documents/develop/ai-tools/sdd/sdd-v2` without asking first.
- Do not auto-create git commits.
- Do not auto-stash.
- If a checkpoint or git action is needed, stop and ask first.
- Dirty working tree blocks `sdd-apply` by default.
- `sdd-apply` uses `Suggested Batches` in `tasks.md` as canonical when available.
- `stage-qa` runs only for code-touching `end-of-feature` or `critical-point` batches, or on explicit user request.
- `stage-qa` always requires explicit user confirmation before running.
- `tasks.md` is the visible task and batch board.
- `apply-progress.md` is the batch execution and incremental QA ledger.
- `state.yaml` is operational state only, not the batch ledger.

## Stage 7 progress

### Completed

- `Stage 7A.1`
  - Replaced the placeholder `sdd-verify` skill.
  - Replaced the placeholder `verify-report.md` template.
  - Defined the final verify contract, verdict model, evidence expectations, command usage from `config.yaml`, and compliance matrix shape.

- `Stage 7A.2`
  - Aligned orchestrator and minimum shared contracts with verify verdict routing.
  - Added explicit `closeout_review` and `verified_pending_archive` behavior.
  - Preserved the distinction between incremental `stage-qa` and final `sdd-verify`.

- `Stage 7B.1`
  - Replaced the placeholder `sdd-archive` skill.
  - Replaced the placeholder `archive-report.md` template.
  - Defined strict archive guardrails, archive move semantics, planner exclusion, and the optional `judgment-day` hook.

- `Stage 7B.2`
  - Aligned orchestrator and minimum shared contracts with archive guardrails.
  - Clarified that archive moves the full active change folder into the canonical archive tree.
  - Recorded that `judgment-day` is optional unless some future explicit policy says otherwise.

## Files changed in Stage 7

- `orchestrator/SDD-ORCHESTRATOR.md`
- `skills/_shared/artifact-contract.md`
- `skills/_shared/persistence-contract.md`
- `skills/_shared/user-interaction-contract.md`
- `skills/_shared/sdd-phase-common.md`
- `skills/_shared/openspec-convention.md`
- `skills/sdd-verify/SKILL.md`
- `skills/sdd-archive/SKILL.md`
- `templates/artifacts/verify-report.md`
- `templates/artifacts/archive-report.md`
- `README.md`
- `docs/decisions/README.md`
- `docs/decisions/stage-7-new-chat-prompt.md`

## Current contract highlights

### `sdd-verify`

- Final verification is change-wide and evidence-heavy.
- Command usage is derived from `openspec/config.yaml`.
- `verify-report.md` carries:
  - final command plan and results
  - compliance matrix
  - evidence log
  - open issues
  - verdict
  - archive gate
- Stable verify verdicts:
  - `pass`
  - `pass_with_warnings`
  - `fail`

### `closeout_review`

- `closeout_review` is used when verify returned `pass_with_warnings` or review-worthy observations still matter before archive.
- `verified_pending_archive` is the stable lifecycle state for that hold point.
- Archive remains gated until the review decision is resolved in favor of closure.

### `sdd-archive`

- Archive is not part of `planner`.
- Archive requires successful final verify first.
- Archive moves the full active change folder to `openspec/changes/archive/YYYY-MM-DD-{change-name}/`.
- `archive-report.md` is created only inside the archived destination.
- `judgment-day` may be suggested before archive for unusually sensitive changes, but it is optional in the current contract set.

## Remaining risks and follow-up

- Stage 7 was completed as a contracts/templates/orchestration pass; runtime execution of these flows was not exercised here.
- `judgment-day` itself remains a placeholder skill; Stage 7 only defined the optional hook and recommendation semantics around it.
- Some implementation-planning documents still contain historical references to Stage 7 as pending by design; those are historical source materials, not the current contract state.

## Recommended next step

Move out of Stage 7 and into whichever downstream integration or validation stage is next.
If continuity is needed in a later chat, start from this file plus `README.md` rather than the historical Stage 7 prompt.
