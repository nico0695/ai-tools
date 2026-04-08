# Tasks

## Summary

- change_name:
- objective:
- mode:
- planner_terminal: false
- apply_ready: false

## Preconditions

- 

## Ordered Tasks

| Task Id | Description | Depends On | Validation | Scope Hints | Status |
|---|---|---|---|---|---|

## Suggested Batches

| Batch | Included Tasks | Goal | Validation | Touches Code | QA Checkpoint | Status |
|---|---|---|---|---|---|---|

## Dependency Notes

- 

## Apply Sync Rules

- `sdd-apply` should use `Suggested Batches` as the canonical batch plan when present.
- If no usable batch plan exists, `sdd-apply` may derive a small batch from tightly coupled adjacent tasks.
- Update only the `Status` cells for the tasks and batch currently being executed.
- Recommended status values: `pending`, `in_progress`, `completed`, `blocked`.
- Use `QA Checkpoint` to signal when a code-touching batch should recommend `stage-qa`.
- Recommended `QA Checkpoint` values: `none`, `end-of-feature`, `critical-point`.

## Planner Stop Note

- If `objective` is `planner`, stop after this artifact and mark the change as `planned`.
