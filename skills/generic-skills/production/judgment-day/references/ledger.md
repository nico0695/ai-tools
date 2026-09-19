# Review ledger

Read this only when the user has accepted saving the review to a file. Everything needed to run a
judgment lives in `SKILL.md`, `references/judge-prompts.md`, and `assets/judge-contract.md`; nothing
here is required to produce the chat report.

The ledger is the chat report made durable. It carries no field the report does not already show — its
only job is to survive the conversation.

## Template

Write it in English even when the chat is in another language, so the file stays readable to whoever
picks up the repository later.

```markdown
# Review Ledger — {target-slug}

- review_mode: judgment-day
- target_kind: code | artifact
- review_reference: {SHA, range resolved to SHAs, or artifact digest}
- run_status: complete | incomplete
- action: none | changes_required
- verdict: pass | pass_with_warnings | fail | unavailable
- counts: confirmed={n} suspect={n} escalated={n} info={n}
- open_severe_findings: {count}
- updated_at: {ISO date}

## Findings

| Id | Lens/Judge | Location | Severity | Status | Claim | Proof Refs |
|---|---|---|---|---|---|---|

`Lens/Judge`: `judge-a` | `judge-b` | `both-judges`. Confirmed rows use `both-judges`; suspects keep
the reporting judge.

## Verdict Rationale

-
```

`{target-slug}` is a short target descriptor plus the short SHA, or the document's filename plus its
digest for `artifact` mode: `feat-checkout-a1b2c3d`, `design-doc-9f1a2b3`.

## Field rules

- **`review_reference`** is the one field that must be exact. It is what makes the ledger mean
  something later: a ledger whose reference no longer resolves describes a target nobody can
  reconstruct.
- **`verdict`** maps from the chat verdict for a reader who only sees this file: `APPROVED` with no
  remaining suspects is `pass`; `APPROVED` with suspects still open is `pass_with_warnings`;
  `ESCALATED` — a confirmed severe finding still open, or an unresolved contradiction — is always
  `fail`; a run with `run_status: incomplete` is `unavailable`. Exactly one applies.
- **`run_status`** is operational: `incomplete` means both valid judge results were not obtained after
  the one retry per judge. It maps the ledger `verdict` to `unavailable`; it never maps to `pass` or
  `fail`.
- **`action`** records whether the report requests remediation. It is separate from `verdict`: a
  confirmed severe finding uses `verdict: fail` and may use `action: changes_required`.
- **`open_severe_findings`** counts only rows with `status: open` — `suspect` rows never count as open,
  even though they are severe.
- **`counts`** uses the fixed keys `confirmed`, `suspect`, `escalated`, `info`. The convergence buckets
  map directly onto them, with one rename: the `contradiction` bucket is counted under `escalated`,
  because by the time this file is written every contradiction has already been through Phase 5's
  adjudication — what is left to record is whether it escalated the verdict, not that it once was a
  bucket named `contradiction`.
- **Every row that was reported is a row here**, including `info` rows, suspects, and refuted ones. A
  ledger that only records what survived cannot be audited.
- Rewrite the whole file on a re-judgment. Ids never change, so the previous rows stay recognizable.

## What this deliberately does not carry

No round counter, no separate corroboration log, no next-action digest. `Lens/Judge` already states how
a row was corroborated — `both-judges` means both judges converged on it separately, which is the
only corroboration mechanism this protocol has; a separate log restating that fact in different words is
not new information. Nothing reads a round counter or a next-action digest: the orchestrator that would
have routed on them does not exist here.

The consequence, stated plainly: a scoped re-judgment is only possible while the report or this file is
in front of you. Reopening a months-old ledger in a fresh conversation gives you a record of what was
found, not a judgment in progress.
