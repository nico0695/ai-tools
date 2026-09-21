---
name: sddl-eval-level-3
description: >-
  Run the installed sdd-lite main flow end to end in a disposable fixture using the
  active CLI: proposal, spec, design, plan, human approvals, executor, and QA. Use
  for release confidence after changes to the main orchestration flow.
---

# sddl-eval-level-3

Exercise the real main flow while preserving every mandatory gate.

## Start

Require a passing/non-blocking Level 1 and a reviewed case. Preview first:

```text
python3 <harness>/scripts/sddl_eval.py level3
  --workspace <id> --case <case> --provider <provider>
```

Explain that the first child runs only through planning, uses the CLI default model,
and has no automatic cost cap. After confirmation, repeat with `--execute`.

## Approval loop

When the run returns `awaiting_approval`:

1. Read the persisted plan, state summary, assertions, and source delta.
2. Show the user the exact run id, stage, scope summary, risks, and report path.
3. Ask for approval of that named stage. Never infer approval from the original task.
4. Preview the continuation command without `--execute`.
5. After confirmation, run:

```text
python3 <harness>/scripts/sddl_eval.py level3
  --workspace <id> --resume-run <run-id> --approve-stage <stage> --execute
```

Each continuation is a new CLI process and must recover from files, not conversation
history. Repeat until `completed` or a failed assertion blocks continuation.

The default case excludes 4R, Judgment Day, delivery, and archive. Do not reinterpret
mandatory QA as optional. Return final verdict, quality command results, usage, diff,
and report paths. Once complete, fill `analysis-template.yaml` from observable
evidence and attach it through `sddl_eval.py analyze` so semantic conclusions enter
the report and local history.
