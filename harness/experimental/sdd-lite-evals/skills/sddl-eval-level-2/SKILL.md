---
name: sddl-eval-level-2
description: >-
  Evaluate sdd-lite triggers, wrappers, routing, worker bypass, resume, approvals,
  and main stage prompts in fresh child sessions of the active CLI. Use after prompt,
  orchestrator, wrapper, handoff, routing, or canonical skill changes.
---

# sddl-eval-level-2

Run provider-native behavioral probes without contaminating their context.

## Preconditions

- Level 1 is neither `BLOCKED` nor `FAIL`.
- The selected case exists under the workspace.
- The active provider matches the requested provider.

Read only `references/providers/<active-provider>.md` when provider details are
needed. Do not load the other provider references.

## Cost preview

First run without `--execute`:

```text
python3 <harness>/scripts/sddl_eval.py level2
  --workspace <id> --case <case> --provider <provider> --profile <smoke|full>
```

Show the probe names and child-session count. Explain that the CLI default model is
used and there is no automatic cost cap. Wait for confirmation unless the user has
explicitly approved this exact preview.

Then repeat with `--execute`.

## Analysis

Read the normalized run report and only the event files needed to explain failures.
Copy `analysis-template.yaml`, complete it with concise evidence-backed findings,
and attach it with:

```text
python3 <harness>/scripts/sddl_eval.py analyze
  --workspace <id> --run-id <run-id> --analysis-file <completed-yaml>
```

The normalized analysis must cover:

- provider-specific prompt incompatibilities
- trigger or route deviations
- evidence that worker bypass or clean-session isolation failed
- `not_observable` limitations
- recommendations separated from deterministic failures

Do not expose hidden reasoning or claim unobserved file reads. The attach command
regenerates reports and history. Return verdict,
token/cost data when available, and paths to the report and analysis.
