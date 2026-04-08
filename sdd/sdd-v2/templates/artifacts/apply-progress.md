# Apply Progress

## Summary

- change_name:
- objective:
- mode:
- lifecycle_status:
- current_batch:
- batching_source: suggested-batches | derived-from-tasks
- snapshot_policy: metadata-only pre-apply checkpoint; no automatic git checkpoint
- dirty_working_tree_policy: block and ask user
- stage_qa_policy: ask user before running on code-touching `end-of-feature` or `critical-point` batches; explicit user request may trigger it after other code-touching batches

## Batch Overview

| Batch Id | Included Tasks | Touches Code | QA Checkpoint | Stage QA | Status | Last Updated |
|---|---|---|---|---|---|---|

## Execution Rules

- Append a new log entry for each attempted batch.
- Keep prior batch history visible; do not overwrite completed batch entries.
- `tasks.md` tracks visible task and batch state.
- `state.yaml` tracks lifecycle, checkpoints, decisions, and next recommended action.
- Use this artifact for the execution ledger and batch evidence.

## Batch Log

### Batch `<batch-id>`

- approval_checkpoint_id:
- approval_decision_id:
- snapshot_checkpoint_id:
- baseline_head:
- baseline_worktree: clean | dirty-blocked | not-available
- planned_scope:
- actual_files_changed:
- touches_code:
- qa_checkpoint: none | end-of-feature | critical-point
- stage_qa_status: not_applicable | recommended | pending_user_confirmation | user_deferred | user_declined | passed | warning | failed
- stage_qa_checkpoint_id:
- stage_qa_decision_id:
- batch_status: pending | in_progress | completed | blocked
- next_action:

#### Planned Work

- 

#### Preconditions And Sync Checks

- 

#### Changes Applied

- 

#### Blast Radius And Scope Notes

- 

#### Incremental QA

- triggered_by: qa_checkpoint | explicit_user_request | not_applicable
- checks_planned:
- checks_run:
- findings_summary:
- continue_recommendation: continue | fix_before_next_batch | replan | stop
- qa_notes:

#### Evidence

| Kind | Reference | Notes |
|---|---|---|

#### Decisions And Blockers

- 

#### User-Facing Summary

- 

---

### Batch `<next-batch-id>`

- approval_checkpoint_id:
- approval_decision_id:
- snapshot_checkpoint_id:
- baseline_head:
- baseline_worktree:
- planned_scope:
- actual_files_changed:
- touches_code:
- qa_checkpoint:
- stage_qa_status:
- stage_qa_checkpoint_id:
- stage_qa_decision_id:
- batch_status:
- next_action:

#### Planned Work

- 

#### Preconditions And Sync Checks

- 

#### Changes Applied

- 

#### Blast Radius And Scope Notes

- 

#### Incremental QA

- triggered_by:
- checks_planned:
- checks_run:
- findings_summary:
- continue_recommendation:
- qa_notes:

#### Evidence

| Kind | Reference | Notes |
|---|---|---|

#### Decisions And Blockers

- 

#### User-Facing Summary

- 
