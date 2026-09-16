# Review ledger

Read this only when the user has accepted saving the review to a file. Everything needed to run a
review lives in `SKILL.md` and `assets/lenses/`; nothing here is required to produce the chat report.

The ledger is the chat report made durable. It carries no field the report does not already show —
its only job is to survive the conversation.

## Template

Write it in English even when the chat is in another language, so the file stays readable to whoever
picks up the repository later.

```markdown
# Review Ledger — {target-slug}

- review_mode: 4r
- immutable_reference: {SHA, range resolved to SHAs, or diff hash}
- tier: trivial | standard | full-4r
- lenses: {which ran}
- verdict: pass | pass_with_warnings | fail
- open_severe_findings: {count}
- updated_at: {ISO date}

## Findings

| Id | Lens | Location | Severity | Status | Claim | Proof Refs |
|---|---|---|---|---|---|---|

## Verdict Rationale

-
```

`{target-slug}` is the branch name or a short target descriptor, plus the short SHA:
`feat-checkout-a1b2c3d`.

## Field rules

- **`immutable_reference`** is the one field that must be exact. It is what makes the ledger mean
  something later: a ledger whose reference no longer resolves describes a target nobody can
  reconstruct.
- **`verdict`** — `pass` when no findings at all, `pass_with_warnings` when only `info` rows remain,
  `fail` when a blocking severe finding is open. Exactly one applies; the three are disjoint by
  construction.
- **`open_severe_findings`** counts rows with `status: open`. It is the number a person scans for.
- **Every row that was reported is a row here**, including `info` rows and refuted ones. A ledger
  that only records what survived cannot be audited.
- Rewrite the whole file on a re-review. Ids never change, so the previous rows stay recognizable.

## What this deliberately does not carry

No round counter, no fix-round table, no next-action digest. Those existed to let a fix round resume
in a different conversation, and nothing reads them: the orchestrator that would have routed on them
does not exist here.

The consequence, stated plainly: a fix round is only possible while the report or this file is in
front of you. Reopening a months-old ledger in a fresh conversation gives you a record of what was
found, not a review in progress. That is the correct reading of an artifact that old.
