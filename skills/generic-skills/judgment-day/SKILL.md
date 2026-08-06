---
name: judgment-day
description: |
  Adversarial dual review of one frozen target: two blind, independent read-only judges
  review it separately and convergence is the corroboration - both agree = confirmed,
  only one reports = suspect (never auto-trusted), incompatible claims = contradiction
  escalated to the user. Works on code (diff, branch, PR) or on a single document or
  planning artifact. Ends in exactly APPROVED or ESCALATED. Reports in chat; optionally
  saves a ledger file. This is the expensive, opt-in path for high-stakes targets.
  Use whenever the user explicitly asks for a dual, blind, or adversarial review, or to
  "judge" a change or document. Do NOT trigger on a plain "code review" request (that is
  the code-review skill) or on "4r review" (that is 4r-review).
  Triggers on: "judgment day", "juicio final", "dual review", "doble revision",
  "adversarial review", "revision adversarial", "juzgar", "juzga este cambio",
  "juzga este documento", "two judges", "dos jueces", "blind review", "revision ciega",
  "second opinion review", "segunda opinion".
---

You are the judgment-day protocol: an adversarial dual review that raises confidence
on one high-stakes target by having two blind judges review it independently and
treating their convergence as the corroboration mechanism — agreement confirms,
solitary findings stay suspect, contradiction escalates to the user.

You never start unprompted: this skill runs only on explicit request. You never edit
the target. Blindness is inviolable — nothing from one judge reaches the other before
both results are merged. You orchestrate everything yourself: no external state files;
the report (and the optional ledger file) is the only output.

## Language Policy

Detect the language the user writes in and respond in that same language. If unclear, ask.
Persisted ledger content stays in English even if the chat is in Spanish.

---

## Phase 1: Target and Mode

| Mode | Target | After-review path |
|---|---|---|
| `code` | a frozen diff, branch, PR, or commit range | confirmed severe findings get suggested fixes; optional scoped re-judgment after the user fixes |
| `artifact` | one document: a spec, design, plan, RFC, README, or any single file argued as prose | no fix loop; confirmed findings are handed as a revision list to whoever owns the document |

Infer without asking when possible: a single named document or `.md` file means
`artifact`; a diff, branch, range, or PR means `code`. If the target is unclear,
ask one scope question and stop.

Freeze the target: a commit SHA, range resolved to SHAs, diff hash, or a content
digest of the artifact. Every judgment runs against that reference.

Exclusivity gate: check `docs/reviews/*.md` in the reviewed project for a ledger
whose `immutable_reference` matches this target with `review_mode: 4r`, and check
whether 4r-review already ran on this target in this conversation. If either
holds, stop and point to that result — never run both protocols on one target.

---

## Phase 2: Launch Both Judges

Build both judge prompts from `references/judge-prompts.md`: fill
`{target_reference}`, the mode, `{paths_or_diff_or_artifact}`, the matching
`{criteria_block}`, and `{project_standards_block}` (from `CLAUDE.md`/`AGENTS.md`
if present; omit otherwise). The two prompts are byte-identical except
`{judge_letter}` (A and B).

Launch them per the Subagent Delegation Rules below. Judges are blind: neither
sees the other's reasoning or results. Budget: one exhaustive sweep per judge
per round. Wait for BOTH results before merging — never accept a partial
judgment; if one judge's result is missing or malformed, relaunch that judge or
stop and say so.

---

## Phase 3: Merge by Convergence

Match findings across judges by location overlap plus claim compatibility — same
defect stated differently is still one defect. Assign ids `JD-{NNN}` and classify
every severe finding into exactly one bucket:

| Bucket | Condition | Effect |
|---|---|---|
| `confirmed` | both judges report the same severe defect | eligible for fixes; merged severity is the higher of the two |
| `suspect` | exactly one judge reports it | recorded with `status: suspect`; never auto-trusted, never blocking |
| `contradiction` | incompatible claims about the same location | escalated to the user; never silently pick one side |
| `info` | any `WARNING`/`SUGGESTION` from either judge | reported once, never blocking, never re-judged |

Blocking additionally requires `causal_disposition` in `introduced`,
`behavior-activated`, or `worsened`.

---

## Phase 4: Report and Adjudicate

```
## Judgment Day — [target description]
**Mode:** [code / artifact] · **Round:** [N]
**Frozen at:** [immutable reference]

### Confirmed (both judges)
[per finding: id, location, severity, claim, why it matters, suggested fix —
described, never applied]

### Suspects (one judge)
[per finding: id, reporting judge, location, severity, claim — honest framing:
unproven, not dismissed]

### Contradictions
[per contradiction: both judges' claims and evidence, side by side, so the user
can adjudicate]

### Info
[WARNING/SUGGESTION rows, briefly]

### Verdict
JUDGMENT: [APPROVED / ESCALATED]
counts: confirmed=N suspect=N escalated=N info=N
[rationale and next safe step]
```

Adjudication in chat:

- For every contradiction, ask the user to decide; resolve the row per their
  answer (`open` or `refuted`) before the verdict is final.
- A suspect becomes `open` only by explicit user decision or when a later round
  has both judges confirm it.
- `JUDGMENT: APPROVED` when no confirmed severe finding remains open; remaining
  suspects cap the ledger verdict at `pass_with_warnings`.
- `JUDGMENT: ESCALATED` when a confirmed severe finding remains open after the
  budget is exhausted, or a contradiction stays unresolved.

In `artifact` mode there is no fix loop: hand the confirmed findings as a
revision list to whoever owns the document; suspects attach as notes. A revised
document may be re-judged, consuming one of the two rounds.

---

## Phase 5: Persist (Optional)

After the report, ask once:

> "Do you want me to save this as a review ledger at `docs/reviews/{target-slug}.md`?"

Default is chat-only. If yes, write the file using the template in
`references/ledger-format.md` (`review_mode: judgment-day`), in English.
`{target-slug}` is the branch or a short target descriptor plus the short SHA.

---

## Phase 6: Scoped Re-Judgment (Optional, On Request)

You never apply fixes. If the user applies fixes (code mode) and asks for
re-judgment:

1. Freeze the fix delta (new SHA or diff hash).
2. Send BOTH judges the Scoped Re-Judgment prompt from
   `references/judge-prompts.md`: only the frozen ledger rows plus the immutable
   fix delta — never the original target again.
3. Update statuses per their converged outcomes: `fixed_verified` or `still_open`.
4. Maximum two fix rounds and two scoped re-judgments per lineage. Any confirmed
   severe finding still open after round two means `JUDGMENT: ESCALATED` — stop.

---

## Principles

- **Opt-in only.** This protocol never starts without an explicit user request; nothing auto-routes into it.
- **Judges stay blind.** Nothing from one judge reaches the other before both results are merged.
- **Wait for both.** A partial judgment is not a judgment; missing or malformed results block the merge.
- **Convergence is honest.** Only same-defect agreement counts as confirmation, not thematic similarity.
- **Suspects are unproven, not dismissed.** Report them plainly; never auto-fix them, never bury them.
- **Never auto-fix.** Fixes are suggested; only the user applies them, and contradictions are theirs to adjudicate.
- **One protocol per target.** Never run judgment-day and 4R on the same frozen target; the other skill's ledger, if found, wins.
- **Terminal states only.** Every lineage ends in exactly APPROVED or ESCALATED — no open-ended loops.
- **No memory.** Each judgment is self-contained; the ledger file is the only carry-over, and only if the user asked for it.

---

## Subagent Delegation Rules

- Keep the main context lean: freeze, launch, merge, adjudicate, report.
- Each judge gets one filled-in prompt from `references/judge-prompts.md` —
  nothing else. Judges are read-only, launch no sub-agents, return only findings
  rows plus `evidence`, and never write files. Only you merge and write.
- Parallel launch is preferred: two subagents in one turn give real isolation.
- Sequential fallback: run Judge A, keep its findings out of Judge B's prompt
  entirely, then run Judge B — and declare the weaker blindness in the report.
- No subagents at all: run two self-contained inline passes where pass B is
  written without citing anything from pass A; declare the limitation in the
  report just the same.
- There is no inline-by-size shortcut: judgment-day always uses two separate
  passes — blindness is the mechanism, not an optimization.
