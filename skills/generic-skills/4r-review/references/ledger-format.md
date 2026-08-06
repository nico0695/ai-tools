# Review Ledger Format — 4R

Canonical rules for findings rows and for the optional persisted ledger file.
Adapted from this repo's sdd review contract; the judgment-day skill carries its
own aligned copy — keep the severity model in sync if you edit one.

## Worker Findings Contract

Lens workers return findings as:

```yaml
findings:
  - location: "path/to/file.ext:42"        # or path:start-end
    severity: BLOCKER | CRITICAL | WARNING | SUGGESTION
    claim: "observable incorrect behavior, one sentence"
    evidence_class: deterministic | inferential
    causal_disposition: introduced | behavior-activated | worsened | pre-existing | unknown
    proof_refs: ["concrete proof: file:line, command output, spec section"]
evidence: ["what was inspected"]
```

Workers never assign ids or statuses; the main skill does when merging.

## Severity Model

| Severity | Meaning | May hold `open`? | Blocks? |
|---|---|---|---|
| `BLOCKER` | must not ship; incident or data loss likely | yes | yes |
| `CRITICAL` | severe defect with a concrete failure path | yes | yes |
| `WARNING` | real weakness, tolerable short-term | no — recorded once as `info` | never |
| `SUGGESTION` | improvement opportunity | no — recorded once as `info` | never |

Severity floor: only `BLOCKER`/`CRITICAL` enter refutation, fix rounds, and re-review.

Blocking additionally requires `causal_disposition` in `introduced`, `behavior-activated`, or `worsened`.
`pre-existing` and `unknown` findings are reported but never block this change.

## Id And Status Rules

- Ids: `R1|R2|R3|R4-{NNN}` per lens (`R1-001`). Ids never change once assigned.
- Status values: `open` | `fixed` | `verified` | `refuted` | `wont-fix` | `info`.
- Status transitions (only these):
  - `open -> fixed` when the user applies a fix for the finding
  - `fixed -> verified` when the scoped re-review confirms the fix delta resolves it
  - `open -> refuted` via refuter outcome `refuted`
  - `open -> wont-fix` only by explicit user decision recorded in the ledger
  - `WARNING`/`SUGGESTION` rows are created directly as `info` and stay `info`
- A row is never deleted within a review lineage; findings history stays in the
  ledger until the lineage terminates.
- One ledger per `target-slug`; the working sections always describe the current
  review lineage.

## Digest Rules

The Review Digest at the top of the ledger is the routing and resume anchor:

- always current: rewrite it on every merge, fix round, and re-review
- counts line uses fixed keys: `confirmed`, `suspect`, `escalated`, `info` —
  for 4R, `confirmed` = severe findings standing after corroboration
  (deterministic, `corroborated`, or `inconclusive`), `suspect` = 0,
  `escalated` = 0, `info` = `WARNING`/`SUGGESTION` rows
- `open_severe_findings` counts only rows with `status: open`
- verdict: `pass` (no open severe findings), `pass_with_warnings` (only `info`
  rows remain), `fail` (open severe findings after budget exhaustion),
  `not_reached` (review in progress)
- there is no external state; the digest alone must explain where the review stands

## Budgets (hard caps)

- one exhaustive sweep per lens; two per lens only in `full-4r`
- exactly one refuter pass, and only in `full-4r` reviews; zero in
  `trivial`/`standard` tiers
- maximum two fix rounds per review lineage; no third round, no lineage reset
- scoped re-reviews see only the frozen ledger plus the immutable fix delta

## Persisted Ledger Template

When the user asks to persist, write `docs/reviews/{target-slug}.md` in the
reviewed project with this shape (always in English):

```markdown
# Review Ledger

## Review Digest

- target_identity:
- review_mode: 4r
- tier: trivial | standard | full-4r
- scope: standalone:{target-slug}
- round: 0 | 1 | 2
- counts: confirmed=0 suspect=0 escalated=0 info=0
- open_severe_findings: 0
- verdict: pass | pass_with_warnings | fail | not_reached
- next_action_digest:
- updated_at:

## Target

- description:
- target_kind: diff | pr | paths
- paths_or_diff_reference:
- changed_lines:
- immutable_reference:
- created_at:

## Findings Ledger

| Id | Lens | Location | Severity | Status | Evidence Class | Causal Disposition | Blocking | Claim | Proof Refs |
|---|---|---|---|---|---|---|---|---|---|

## Corroboration Log

| Finding Id | Mechanism | Outcome | Notes |
|---|---|---|---|

Mechanism is always `refuter`; outcomes: `corroborated` | `refuted` | `inconclusive`.
A malformed or missing verdict means the finding stands.

## Fix Rounds

| Round | Ledger Ids | Fix Vehicle | Applied At | Scoped Re-review Outcome |
|---|---|---|---|---|

Fix Vehicle: `user` (fixed in this conversation) | `external` (fixed outside it).

## Verdict Rationale

-

## Next Recommended Action

-
```

`immutable_reference` freezes the review target: a commit SHA, commit range, or
diff hash. All sweeps, refutations, and re-reviews run against this reference,
never a moving tree. Target roughly 200 to 400 words plus tables.
