# Archive Report

## Summary

- change_name:
- objective:
- mode:
- archived_at:
- lifecycle_status: archived
- source_active_path:
- archive_path:
- verify_verdict: pass | pass_with_warnings
- verify_archive_gate: ready | closeout_review_required
- closeout_review_checkpoint_id:
- closeout_review_decision_id:

## Archive Eligibility Context

- verify_report_reviewed:
- state_reviewed:
- planner_exception_confirmed:
- archive_ready:
- archive_collision_check:
- archive_notes:

## Archived Artifact Inventory

| Artifact | Archived Copy Present | Notes |
|---|---|---|
| state.yaml | yes |  |
| explore.md | yes |  |
| proposal.md | yes |  |
| spec.md | yes |  |
| design.md | yes |  |
| tasks.md | yes |  |
| apply-progress.md | yes |  |
| verify-report.md | yes |  |
| archive-report.md | yes | created during archive |

Recommended values for `Archived Copy Present`:
- `yes`
- `no`
- `not_applicable`

## Archive Actions

| Step | Result | Notes |
|---|---|---|
| verify gate confirmed | completed |  |
| archive target resolved | completed |  |
| collision check | completed |  |
| active folder moved | completed |  |
| archived state finalized | completed |  |
| archive report written | completed |  |

Recommended result values:
- `completed`
- `skipped`
- `blocked`

## Optional Deep Review Hook

- judgment_day_status: not_requested | considered_not_run | requested | completed | not_applicable
- judgment_day_reference:
- judgment_day_notes:

## Closure Notes

- 

## Reopen Guidance

- 

## Archive Rules

- This artifact is created only inside the archived folder.
- `planner` does not use this artifact because `planner` stops at `planned`.
- Archive requires successful final verify first.
- If verify required `closeout_review`, record the checkpoint and decision references here before closure.
- MVP archive means moving the full active change folder and preserving the final change record as an archived unit.
