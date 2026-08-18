# Authoring evaluation cases

Keep project configuration, test intent, and run history separate.

## Assertions

Supported deterministic assertions:

- `exit_code`
- `output_contains_any` / `output_not_contains_any`
- `event_contains_any` / `event_not_contains_any`
- `path_exists` / `path_absent`
- `source_unchanged`

Output assertions inspect extracted assistant text, not reflected user prompts.
Event assertions inspect raw structured events and are appropriate for observable
file reads or tool calls.

## Fixture setup

A probe may remove paths or apply an overlay stored inside its workspace:

```yaml
fixture_setup:
  overlay_dir: cases/fixtures/spec-ready
  remove_paths:
    - sdd-lite/project-context.md
```

Paths are fixture-relative and cannot contain `..`. Overlays must stay inside the
workspace. Use an overlay for stage-specific routing or resume checkpoints; keep
the task prompt independent from the project profile where practical.

## Useful main-flow checkpoints

- no active change → proposal
- proposal ready → spec
- spec ready → design
- design ready → plan
- plan ready without approval → stop
- persisted approved stage → executor
- executed stage → stage QA
- all stages accepted → final QA and completed

Default Level 3 requires no pre-existing active changes. Create a dedicated resume
case with `requires_no_active_changes: false` when testing a seeded checkpoint.

