---
name: sddl-eval-level-1
description: >-
  Run zero-token deterministic integrity checks against an installed sdd-lite.
  Use for every sdd-lite change and whenever wrappers, schemas, routes, skill files,
  bootstrap paths, or legacy runtime references may be inconsistent.
---

# sddl-eval-level-1

Run the structural gate before any model-backed evaluation.

## Procedure

1. Resolve the harness as described by `sddl-eval-init`.
2. Identify the workspace id; recover it from `workspaces/*/project.yaml` before asking.
3. Run:

```text
python3 <harness>/scripts/sddl_eval.py level1 --workspace <id>
```

4. Read the generated `report.md`, not every raw input.
5. Present verdict, failures, warnings, and direct evidence paths.

`BLOCKED` and `FAIL` prevent Levels 2 and 3. `WARN` permits them only when the
warning cannot invalidate the intended case. Do not reinterpret a deterministic
failure as stylistic disagreement.

