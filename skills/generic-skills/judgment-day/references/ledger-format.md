# Review Ledger Format — Judgment Day

Canonical rules for findings rows and for the optional persisted ledger file.
Adapted from this repo's sdd review contract; the 4r-review skill carries its
own aligned copy — keep the severity model in sync if you edit one.

## Worker Findings Contract

Judges return findings as:

```yaml
findings:
  - location: "path/to/file.ext:42"        # or path:start-end; section anchor for artifact targets
    severity: BLOCKER | CRITICAL | WARNING | SUGGESTION
    claim: "observable incorrect behavior, one sentence"
    evidence_class: deterministic | inferential
    causal_disposition: introduced | behavior-activated | worsened | pre-existing | unknown
    proof_refs: ["concrete proof: file:line, command output, spec section"]
evidence: ["what was inspected"]
```

Judges never assign ids or statuses; the main skill does when merging.

## Severity Model

| Severity | Meaning | May hold `open`? | Blocks? |
|---|---|---|---|
| `BLOCKER` | must not ship; incident or data loss likely | yes | yes |
| `CRITICAL` | severe defect with a concrete failure path | yes | yes |
| `WARNING` | real weakness, tolerable short-term | no — recorded once as `info` | never |
| `SUGGESTION` | improvement opportunity | no — recorded once as `info` | never |

Severity floor: only `BLOCKER`/`CRITICAL` findings may hold `status: open` or
`status: suspect`, and only `open` rows enter the fix loop.

Blocking additionally requires `causal_disposition` in `introduced`, `behavior-activated`, or `worsened`.
`pre-existing` and `unknown` findings are reported but never block this change.

## Convergence Buckets

| Bucket | Condition | Effect |
|---|---|---|
| `confirmed` | both judges report the same severe defect (same location and compatible claim) | eligible for the fix loop |
| `suspect` | exactly one judge reports it | recorded with `status: suspect`, never auto-fixed |
| `contradiction` | judges make incompatible claims about the same location | escalated to explicit user decision in chat |
| `info` | any `WARNING`/`SUGGESTION` from either judge | informational only |

## Id And Status Rules

- Ids: `JD-{NNN}`. Ids never change once assigned.
- Status values: `open` | `suspect` | `fixed` | `verified` | `refuted` | `wont-fix` | `info`.
- Status transitions (only these):
  - severe findings reported by exactly one judge are created directly as
    `suspect`: recorded, outside the fix loop, never blocking
  - `suspect -> open` only by explicit user decision in chat, or when a later
    round has both judges confirm the same defect
  - `suspect -> wont-fix` only by explicit user decision recorded in the ledger
  - `open -> fixed` when the user applies a fix for the finding
  - `fixed -> verified` when the scoped re-judgment confirms the fix delta resolves it
  - `open -> refuted` when a judge contradiction is resolved against it
  - `open -> wont-fix` only by explicit user decision recorded in the ledger
  - `WARNING`/`SUGGESTION` rows are created directly as `info` and stay `info`
- A row is never deleted within a review lineage; findings history stays in the
  ledger until the lineage terminates.
- One ledger per `target-slug`; the working sections always describe the current
  review lineage.

## Digest Rules

The Review Digest at the top of the ledger is the routing and resume anchor:

- always current: rewrite it on every merge, fix round, and re-judgment
- counts line uses fixed keys: `confirmed`, `suspect`, `escalated`, `info` —
  the convergence buckets map directly (`escalated` = unresolved contradictions)
- `open_severe_findings` counts only rows with `status: open`; `suspect` rows
  never count as open
- verdict: `pass` (no open severe findings and no suspects),
  `pass_with_warnings` (only `info` and/or `suspect` rows remain),
  `fail` (open severe findings after budget exhaustion or an unresolved
  contradiction), `not_reached` (review in progress)
- there is no external state; the digest alone must explain where the review stands

## Budgets (hard caps)

- one exhaustive sweep per judge per round
- zero refuter passes — two-judge convergence is the corroboration mechanism
- maximum two fix rounds and two scoped re-judgments per review lineage
- scoped re-judgments see only the frozen ledger plus the immutable fix delta
- terminal states are exactly `approved` or `escalated`

## Persisted Ledger Template

When the user asks to persist, write `docs/reviews/{target-slug}.md` in the
reviewed project with this shape (always in English):

```markdown
# Review Ledger

## Review Digest

- target_identity:
- review_mode: judgment-day
- judgment_target_kind: code | artifact
- scope: standalone:{target-slug}
- round: 0 | 1 | 2
- counts: confirmed=0 suspect=0 escalated=0 info=0
- open_severe_findings: 0
- verdict: pass | pass_with_warnings | fail | not_reached
- next_action_digest:
- updated_at:

## Target

- description:
- target_kind: diff | pr | paths | artifact
- paths_or_diff_reference:
- changed_lines:
- immutable_reference:
- created_at:

## Findings Ledger

| Id | Lens/Judge | Location | Severity | Status | Evidence Class | Causal Disposition | Blocking | Claim | Proof Refs |
|---|---|---|---|---|---|---|---|---|---|

`Lens/Judge`: `judge-a` | `judge-b` | `both-judges`. Confirmed rows use
`both-judges`; suspects keep the reporting judge.

## Corroboration Log

| Finding Id | Mechanism | Outcome | Notes |
|---|---|---|---|

Mechanism is always `judge-convergence`; outcomes: `confirmed` (both judges) |
`suspect` (one judge) | `contradiction` (judges disagree).

## Fix Rounds

| Round | Ledger Ids | Fix Vehicle | Applied At | Scoped Re-judgment Outcome |
|---|---|---|---|---|

Fix Vehicle: `user` (fixed in this conversation) | `external` (fixed outside it).

## Verdict Rationale

-

## Next Recommended Action

-
```

`immutable_reference` freezes the target: a commit SHA, commit range, diff hash,
or artifact digest. All judgments and re-judgments run against this reference,
never a moving tree. Target roughly 200 to 400 words plus tables.
