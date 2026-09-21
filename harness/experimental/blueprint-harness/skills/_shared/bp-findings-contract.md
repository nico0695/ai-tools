# bp-findings-contract

Single model for every reported finding — bug triage, analysis, audits, and `open_risks` share it.

## Finding row

`id | claim | classification | evidence_class | severity | proof`

- `classification`: `fact` (verified in code or history) · `inference` (reasoned, not verified) · `unknown`.
- `evidence_class`: `deterministic` (reproducible from the cited source) · `inferential`.
- `proof`: `file:line` or commit SHA references. A `fact` without proof refs is demoted to `inference`.

## Severity model

| Severity | Meaning |
|---|---|
| `critical` | data loss, security exposure, total outage |
| `high` | core flow broken or wrong results |
| `medium` | degraded or partial behavior |
| `low` | minor defect or edge case |
| `info` | observation, no defect |

## Precision gate

- Insufficient evidence → the answer is `unknown`. Silence over speculation.
- Root cause is asserted only within the rigor level's evidence bar (`bp-flow-contract`, Rigor levels).
- Style or taste findings are out of scope; report defects and risks only.
