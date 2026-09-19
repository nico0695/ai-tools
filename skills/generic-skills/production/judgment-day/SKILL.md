---
name: judgment-day
description: |
  Run two blind reviews of the same code or document in isolated contexts.
  Use when explicitly invoked, requested as "juicio final", or the user asks for two blind reviewers.
  Suggest when the user wants corroboration of a review before a critical decision.
---

You are the judgment-day protocol: an adversarial dual review that raises confidence on one high-stakes
target by having two blind judges review it in isolated contexts and treating their convergence as the
corroboration mechanism. The passes are blind and independently prompted, not statistically independent
models — agreement confirms, a solitary finding stays suspect, and an incompatible claim escalates to you.

The failure mode this skill exists to prevent is a single reviewer's mistake — a missed defect, an
invented one, a misjudged severity — passing as fact because nothing checked it. Two blind readings of
the same target either agree, in which case the finding earns more confidence, or they don't, in which
case that disagreement is itself the signal, not something to paper over.

Four rules decide most of what follows. Where they apply, they beat a better idea in the moment.

- **Opt-in only.** Nothing in this protocol starts unprompted; it runs only on explicit request.
- **Blindness is the mechanism, not an optimization.** Nothing from one judge reaches the other before
  both results are merged — not their existence, not their reasoning, not their findings.
- **Wait for both.** A partial judgment is not a judgment; a missing or malformed result blocks the
  merge, it is never silently dropped.
- **Never auto-fix.** Fixes are described, never applied; contradictions are the user's to adjudicate,
  never picked by preference.

State is optional, not absent. The chat report is the only guaranteed output; a ledger file exists only
if the user asks for one, and a scoped re-judgment depends on one of the two still being in front of
you. Every completed lineage ends in exactly one of two terminal states, `APPROVED` or `ESCALATED` —
no open-ended loop. An `ESCALATED` report can still be re-judged while the Phase 6 budget remains; once
no re-judgment remains, it is final. A run that cannot obtain both valid judge results is operationally
`INCOMPLETE` and has no target verdict.

## Language Policy

Detect the language the user writes in and report in that same language. Headings and labels in the
report template below are structure, not text to copy — render them in the chat's language. A
persisted ledger stays in English regardless.

---

## Phase 1: Target and Mode

| Mode | Target | After-review path |
|---|---|---|
| `code` | a diff, branch, PR, or commit range, recorded as a review reference | confirmed severe findings get suggested fixes; optional scoped re-judgment after the user fixes |
| `artifact` | one document: a spec, design, plan, RFC, README, or any single file argued as prose | no fix loop; confirmed findings are handed as a revision list to whoever owns the document |

Infer the mode without asking. First match wins:

1. The user named the mode explicitly.
2. The user pointed at exactly one document and named no diff, branch, or commit range → `artifact`.
3. The user named a diff, branch, commit range, or PR → `code`. A PR that touches only one document is
   still `code`: a PR is a change, not a standalone artifact, even when its content happens to be prose.
4. Still unclear → ask one scope question and stop.

Record a review reference: a commit SHA, a range resolved to SHAs, a diff hash, or a content digest of
the artifact. Every judgment in this lineage uses that reference.

---

## Phase 2: Launch Both Judges

Build the judge prompt from `references/judge-prompts.md`, with `assets/judge-contract.md` appended
from its first heading onward, filling `{target_reference}`, the mode, `{paths_or_diff_or_artifact}`,
the matching `{criteria_block}`, and `{project_standards_block}` (from `CLAUDE.md`/`AGENTS.md` if
present; omit otherwise). Launch it twice, unmodified — the two runs are byte-identical.
`{judge_letter}` (A/B) is your own bookkeeping to track which subagent produced which result; it never
appears inside the text either judge reads. That is what keeps the two reviews isolated: neither
prompt mentions that a second pass exists.

Launch them per the Subagent Delegation Rules below. Budget: one exhaustive sweep per judge per round.
Wait for BOTH results before merging — never accept a partial judgment. A missing or malformed result
gets one retry for that judge (two attempts total); if it still fails, stop with `Run status: INCOMPLETE`
and do not print a target verdict.

---

## Phase 3: Merge by Convergence

A finding is **severe** when its severity is `BLOCKER` or `CRITICAL`; `WARNING` and `SUGGESTION` are
never severe and always become `info`, regardless of how many judges reported them.

Two rows describe the same defect when they name overlapping location — the same file with
intersecting or adjacent line ranges (code), or the same section anchor (artifact) — **and** a
compatible claim: the same observable failure, worded differently, is still one defect.

Compare explicit assessments before merging findings. A `correct` assessment from one judge contradicts
a `broken` assessment or a severe finding from the other only when both name the same criterion and an
overlapping location, using the same overlap test as above. A `correct` without a specific location, or
whose location does not overlap, contradicts nothing: the other judge's finding stays `suspect`.
`not_assessed` is an absence of evidence, not an approval, and never creates a contradiction.

Assign ids `JD-{NNN}` and classify every finding into exactly one bucket:

| Bucket | Condition | Effect |
|---|---|---|
| `confirmed` | both judges report the same defect, both severe | `status: open`; eligible for fixes; merged severity is the higher of the two |
| `suspect` | exactly one judge reports it severe, whether or not the other judge noted the same location at `WARNING`/`SUGGESTION` | `status: suspect`; never auto-trusted, never blocking; a milder note from the other judge stays a note on the row, not a separate `info` row |
| `contradiction` | incompatible claims about an overlapping location — one says correct, one says broken; or mutually exclusive root causes | escalated to the user; never silently pick one side |
| `info` | any `WARNING`/`SUGGESTION` from either judge, not already folded into a `suspect` row above | reported once, never blocking, never re-judged |

Blocking additionally requires `causal_disposition` in `introduced`, `behavior-activated`, or
`worsened`; `pre-existing` and `unknown` never block.

---

## Phase 4: Report

The report is read by someone deciding whether to trust this target. Confirmed and suspect findings are
compact — one row each, detail on request. Contradictions are not: adjudicating them is the one thing
only the user can do, so their full evidence is inline, in this same message, never behind a request.

```
## Judgment Day — [target description]
**Mode:** [code / artifact] · **Reference:** [review reference]
**Run status:** [COMPLETE / INCOMPLETE] — operational status, separate from the target verdict
**Action:** [NONE / CHANGES REQUIRED] — remediation requested, separate from the target verdict

### Confirmed (both judges)
| Id | Location | Severity | Claim |
|---|---|---|---|

### Suspects (one judge)
| Id | Judge | Location | Severity | Claim |
|---|---|---|---|---|

### Contradictions
[per contradiction, in full: both judges' claims and evidence side by side — this section is never
compacted]

### Info
- [WARNING/SUGGESTION rows, one line each]

---
**TL;DR** — [one or two sentences: what this target risks, in plain words]
**Verdict:** [PENDING ADJUDICATION if a contradiction is unresolved, otherwise APPROVED / ESCALATED]
**Confirmed:** [id `location`, id `location`] — or "none"
**Needs your decision:** [contradiction ids] — or "none"
**Next step:** [the next safe action]
```

Rules for it:

- **Confirmed and Suspects are tables, one row per finding, one sentence per claim.** Evidence,
  `causal_disposition`, and a suggested fix live in an expansion the user requests — described, never
  applied.
- **Contradictions are never compacted.** Both judges' claims and evidence go in full, because the
  verdict cannot be final until the user resolves them.
- **Drop a section when it is empty** rather than printing an empty heading or table.
- **The TL;DR goes last and repeats the anchors.** By the time someone scrolls past a long report they
  have lost the ids; the closing block is where they find them again.
- **When nothing was found**, drop every section and say so in one line: what was inspected, and that
  it came back clean.
- `Verdict: APPROVED` when no confirmed severe finding remains `open` and no contradiction is
  unresolved; remaining suspects cap the ledger's `verdict` at `pass_with_warnings`.
- `Verdict: ESCALATED` when a confirmed severe finding remains `open`, or a contradiction stays
  unresolved past the closing question in Phase 5. It is final once no re-judgment remains: the Phase 6
  budget is spent, the mode is `artifact`, or the user does not request one.
- Until every contradiction is resolved, the printed verdict is `PENDING ADJUDICATION` — never a final
  `APPROVED`/`ESCALATED` the report has not yet earned.
- `Run status: INCOMPLETE` is used only when both valid judge results were not obtained after the retry;
  it is not a target verdict and is not mapped to approval or escalation.
- On an initial report with a confirmed severe finding, the verdict is `ESCALATED`. Set `Action:
  CHANGES REQUIRED` when remediation is expected, or `Action: NONE` when no remediation is being
  requested. Explain the context and rationale; `Action` is not a verdict.
- The chat verdict and the ledger `verdict` field describe the same outcome for two different readers:
  see the field rule in `references/ledger.md`.

In `artifact` mode there is no fix loop: hand the confirmed findings as a revision list to whoever owns
the document; suspects attach as notes. A revised document is a new Judgment Day run, not a
re-judgment — Phase 6 below is `code`-mode only.

---

## Phase 5: Close

One consolidated question, once, after the report — never a second interruption:

> For each contradiction above, which side matches what actually happened, or should it stay open? Want
> me to expand a finding's evidence and suggested fix, or save this as a review ledger?

- Resolve every contradiction per the user's answer (`open` or `refuted`) before the verdict is final.
  Skip this line entirely when there are no contradictions.
- A suspect becomes `open` only by this explicit decision, or when a later round has both judges
  confirm the same defect. A suspect the user does not act on stays `suspect` — never silently dropped,
  never silently promoted.
- Offer the expansion only when at least one confirmed or suspect finding exists. On yes: the evidence,
  the causal disposition, why it does or does not block, and — `code` mode only — the smallest change
  that fixes it, as a before/after snippet. Described, never applied.
- Propose a ledger path the project can actually hold: `docs/reviews/jd-{target-slug}.md` when `docs/`
  exists, otherwise ask where it goes. Never assume the convention. Default is chat-only; on yes, write
  the file using the template in `references/ledger.md` (`review_mode: judgment-day`), in English.
- That is the only interruption after the report, in either direction. Do not ask again.

---

## Phase 6: Scoped Re-Judgment (Code Mode Only, On Request)

You never apply fixes. When the user has applied them and asks for re-judgment:

**Precondition.** A scoped re-judgment needs the previous findings — either the persisted ledger, or
this conversation still holding the report. Without one of the two, this is a fresh Judgment Day run,
not round 2. Say which of the two is happening instead of guessing.

1. Record the fix delta reference: a new SHA or diff hash.
2. Send BOTH judges the Scoped Re-Judgment prompt from `references/judge-prompts.md`, with
   `assets/judge-contract.md` appended the same way as round one: only the frozen findings rows (never
   which judge originally reported each one) plus the fix delta reference — never the original target
   again.
3. Update statuses per their converged outcome: `open → fixed` when both judges agree the delta
   addresses it, `fixed → verified` when both confirm the delta actually resolves it, or still `open`
   with the evidence that it does not. Any new severe defect either judge reports inside the delta's
   own lines re-enters Phase 3's convergence buckets exactly like a round-one finding, with a fresh id.
4. Re-report using the Phase 4 shape, with `Status` as a column this time.

**Maximum two fix rounds and two scoped re-judgments per lineage.** Any confirmed severe finding still
open after round two means a final `Verdict: ESCALATED` — stop. If a fix cannot be verified from the delta
alone — its correctness depends on context the delta does not carry — say so and leave it `fixed`, not
`verified`. An unverifiable claim of verification is worse than an honest `fixed`.

---

## Subagent Delegation Rules

- Keep the main context lean: record, launch, merge, adjudicate, report. Only you merge and write.
- Each judge gets one filled-in prompt — the round-one or re-judgment template plus
  `assets/judge-contract.md` — nothing else. Judges are read-only, launch no sub-agents, return the
  output required by the active prompt and contract plus `evidence`, and never write files.
- Parallel launch is preferred: two subagents in one turn give real isolation, and neither prompt
  mentions that the other exists.
- Sequential fallback: run Judge A, keep its output out of Judge B's prompt entirely, then run Judge B.
  Two separate subagent contexts are fully blind regardless of launch order — there is nothing weaker
  about running them one after the other.
- No subagents at all: as a last resort, run two self-contained inline passes, writing pass B without
  rereading pass A's output. This is best-effort isolation within a single context, not the real
  blindness two subagents give you — declare that limitation in the report.
