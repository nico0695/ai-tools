---
name: sddl-eval-report
description: >-
  Rebuild sdd-lite evaluation reports and local history, or compare a candidate run
  against an explicitly named baseline. Use when reviewing trends, regressions,
  token usage, provider differences, or prior sdd-lite evaluation findings.
---

# sddl-eval-report

Aggregate existing evidence without launching another model-backed test.

## Campaign report

```text
python3 <harness>/scripts/sddl_eval.py report
  --workspace <id> --campaign <campaign>
```

## Explicit baseline

Require both run ids:

```text
python3 <harness>/scripts/sddl_eval.py report
  --workspace <id> --campaign <campaign>
  --candidate-run <candidate> --baseline-run <baseline>
```

Never auto-select the latest run. If provider, case, project hash, or model differs,
label the comparison `confounded` and explain the specific differences.

Summarize verdict deltas, new/persisting/resolved findings, token/cost changes when
observable, and evidence paths. Keep raw transcripts out of the human summary.

