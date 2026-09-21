# Verify Report

## Summary

- change_name:
- objective:
- mode:
- lifecycle_status:
- verification_scope: full-change
- code_touched:
- verdict: pass | pass_with_warnings | fail
- archive_gate: ready | closeout_review_required | blocked
- closeout_review_checkpoint_id:
- closeout_review_decision_id:
- verified_at:

## Verification Context

- proposal_reviewed:
- spec_reviewed:
- design_reviewed:
- tasks_reviewed:
- apply_progress_reviewed:
- changed_scope_reviewed:
- verification_notes:

## Final Command Plan And Results

| Category | Commands From Config | Used In Final Verify | Outcome | Notes |
|---|---|---|---|---|
| test |  |  | passed |  |
| typecheck |  |  | not_configured |  |
| build |  |  | not_run |  |
| lint |  |  | not_run |  |

Recommended outcome values:
- `passed`
- `warning`
- `failed`
- `not_run`
- `not_configured`

## Compliance Matrix

| Check Id | Source | Requirement Or Target | Evidence | Status | Notes |
|---|---|---|---|---|---|

Recommended source values:
- `spec`
- `tasks`
- `design`
- `apply-progress`
- `repo-state`

Recommended status values:
- `passed`
- `warning`
- `failed`
- `not_applicable`

Matrix guidance:
- build rows from `spec.md` acceptance criteria, `tasks.md` validation notes, and material design constraints
- use `warning` for non-blocking gaps or residual uncertainty
- use `failed` for unmet material requirements or evidence that is too weak for closeout confidence
- use `not_applicable` only when the requirement truly does not apply to the implemented scope

## Open Issues

| Issue Id | Severity | Summary | Affects | Blocking | Recommended Action |
|---|---|---|---|---|---|

Recommended severity values:
- `low`
- `medium`
- `high`

Recommended blocking values:
- `yes`
- `no`

## Evidence Log

| Kind | Reference | Notes |
|---|---|---|

Recommended kind values:
- `command`
- `artifact`
- `file`
- `observation`
- `test`

## Verdict Rationale

- 

## Next Recommended Action

- 

## Archive Gate Notes

- `ready`: final verification supports moving to archive without an extra closeout checkpoint.
- `closeout_review_required`: final verification passed with warnings or review-worthy observations; run a closeout review before archive.
- `blocked`: final verification did not support closure; return to implementation or upstream correction.

## Verification Rules

- `state.yaml` should keep only the operational summary of verification, not the full matrix.
- `stage-qa` evidence may be reused, but this report must add change-wide final verification evidence.
- `planner` does not use this artifact as a terminal closure report.
