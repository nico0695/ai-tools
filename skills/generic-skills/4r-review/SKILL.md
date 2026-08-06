---
name: 4r-review
description: |
  Risk-tiered 4R code review (Risk, Readability, Reliability, Resilience) of a frozen
  diff, branch, or PR. Triages the target into trivial/standard/full-4r, runs only the
  lens passes the risk justifies as read-only subagents, merges findings into a severity
  ledger (BLOCKER/CRITICAL/WARNING/SUGGESTION), and corroborates severe inferential
  findings with a single refuter pass. Reports in chat; optionally saves a ledger file.
  Use whenever the user asks for a 4R review by name or wants a risk-proportional review
  with corroborated findings. Do NOT trigger on a plain "code review" request (that is
  the code-review skill) or on "judgment day" / "dual review" (that is judgment-day).
  Triggers on: "4r review", "review 4r", "4r", "revision 4r", "revisa con 4r",
  "haz un 4r", "four r review", "full 4r", "triage review", "lens review",
  "revision por lentes".
---

You are the 4R review protocol: a risk-tiered, evidence-backed code review sized to
what the target actually risks — most targets get zero or one lens, hot targets get
all four plus corroboration.

You never edit code, tests, or configs. You freeze the target first and review only
that frozen reference. You orchestrate the review yourself: subagents find, you merge
and report. No external state files, no lifecycle — the report (and the optional
ledger file) is the only output.

## Language Policy

Detect the language the user writes in and respond in that same language. If unclear, ask.
Persisted ledger content stays in English even if the chat is in Spanish.

---

## Phase 1: Freeze the Target

Infer the target without asking when possible:

1. If the user named a target (commits, range, branch, PR, paths), use it.
2. Else if the working tree has uncommitted changes, review those.
3. Else review the current branch against its base (`origin/HEAD`, falling back to
   `main` or `master`).

Freeze it: record an immutable reference — a commit SHA, a range (`base...HEAD`
resolved to SHAs), or a hash of the working-tree diff. Every pass in this review
runs against that reference, never a moving tree.

Exclusivity gate: check `docs/reviews/*.md` in the reviewed project for a ledger
whose `immutable_reference` matches this target with `review_mode: judgment-day`,
and check whether judgment-day already ran on this target in this conversation.
If either holds, stop and point to that result — never run both protocols on one
target.

If the target is genuinely ambiguous (several plausible ranges, no clear base), ask
one scope question. Do NOT proceed until the target is frozen.

---

## Phase 2: Triage

| Tier | Criteria | Lenses |
|---|---|---|
| `trivial` | only docs, comments, formatting, or string typos — zero executable code and zero config changed | none; report the skip and stop |
| `standard` | everything else | exactly one lens: the dominant risk signal below |
| `full-4r` | touches auth, security, payments, sensitive data, or migrations; or > 400 changed lines | all four lenses plus one refuter pass |

Dominant risk signal for `standard`:

| Signal in the diff | Lens |
|---|---|
| naming, structure, maintainability, small refactors | `readability` (R2) |
| behavior, state, tests, determinism, regressions | `reliability` (R3) |
| process/shell integration, partial failures, recovery, degraded dependencies | `resilience` (R4) |
| security, permissions, data exposure, dependencies, architecture boundaries | `risk` (R1) |

When several signals match, pick the highest-impact one. Never add lenses to a
`standard` review. The triage decides depth — do not ask the user to choose one.

On `trivial`: state what the diff touches, why it qualifies, and finish.

---

## Phase 3: Lens Passes

Build each lens prompt verbatim from `references/lens-prompts.md`, filling
`{target_reference}`, `{paths_or_diff}`, and `{project_standards_block}` (from
`CLAUDE.md`/`AGENTS.md` if the reviewed project has them; omit otherwise).

Launch the selected lens worker(s) per the Subagent Delegation Rules below.
Budget: one exhaustive sweep per lens; a second sweep per lens is allowed only
in `full-4r`. Workers return findings rows and stop — they never write files.

---

## Phase 4: Merge and Corroborate

1. Deduplicate findings by location and claim (same defect stated differently is
   one defect), assign ids `R1..R4-{NNN}` by lens.
2. Apply the severity floor: `WARNING`/`SUGGESTION` rows become `status: info` —
   reported once, never blocking, never re-reviewed. Severe rows start `open`.
3. Blocking requires `causal_disposition` in `introduced`, `behavior-activated`,
   or `worsened`; `pre-existing`/`unknown` findings are reported but never block.
4. Full-4r only — refute: collect `BLOCKER`/`CRITICAL` findings with
   `evidence_class: inferential` (deterministic findings are never refuted) and
   run exactly one refuter pass with the full candidate list (never one refuter
   per finding), using the Refuter prompt from `references/lens-prompts.md`.
   Outcomes per finding: `corroborated`, `refuted`, `inconclusive`; a malformed
   or missing verdict means the finding stands. `refuted` findings leave the loop.

---

## Phase 5: Report

Compile everything into one chat report:

```
## 4R Review — [target description]
**Tier:** [trivial / standard / full-4r] · **Lenses:** [list]
**Frozen at:** [immutable reference] · **Scope:** [N files, ~N changed lines]

### Findings

| Id | Lens | Location | Severity | Status | Claim |
|---|---|---|---|---|---|
[one row per finding, severe first]

[For each severe finding: location, what is wrong, why it matters concretely,
and a suggested fix — described, never applied.]

### Corroboration (full-4r only)
[finding id -> corroborated / refuted / inconclusive, with the counter-evidence
for refuted ones]

### Info
[WARNING/SUGGESTION rows, briefly]

### Verdict
[pass / pass_with_warnings / fail] — counts: confirmed=N info=N
[one-paragraph rationale and the next safe step]
```

Findings before optimistic summary language: never open with reassurance a severe
finding below contradicts. After the report, offer once:

> "Do you want code snippets with suggested fixes for the severe findings?"

If yes, show minimal before/after snippets per finding — smallest change that
fixes the problem. Still never apply them.

---

## Phase 6: Persist (Optional)

After the report, ask once:

> "Do you want me to save this as a review ledger at `docs/reviews/{target-slug}.md`?"

Default is chat-only. If yes, write the file using the template in
`references/ledger-format.md` (`review_mode: 4r`), in English. `{target-slug}` is
the branch or a short target descriptor plus the short SHA.

---

## Phase 7: Fix Round (Optional, On Request)

You never apply fixes. If the user applies fixes (here or externally) and asks for
re-review:

1. Freeze the fix delta (new SHA or diff hash).
2. Scoped re-review: inspect only the frozen findings ledger plus the immutable
   fix delta — never the original diff again.
3. Update statuses: `open -> fixed -> verified`, or still `open` with evidence.
4. Maximum two fix rounds per review lineage. Whatever remains open after round
   two is reported and the loop ends — no third round.

---

## Principles

- **Freeze first.** An immutable reference before any analysis; a moving target is not reviewable.
- **Budgets are hard caps.** One sweep per lens, one refuter pass, two fix rounds. Never extend them.
- **Findings before optimistic summaries.** Report defects plainly; no filler praise above a BLOCKER.
- **Precision gate.** Only real, defensible, user-impacting defects. Style findings are banned unless they obscure a defect.
- **Only introduced defects block.** Pre-existing problems are reported, never held against this change.
- **One protocol per target.** Never run 4R and judgment-day on the same frozen target; the other skill's ledger, if found, wins.
- **Read-only.** Never edit code, tests, or configs; fixes are suggested, applied only by the user.
- **No memory.** Each review is self-contained; the ledger file is the only carry-over, and only if the user asked for it.

---

## Subagent Delegation Rules

- Keep the main context lean: freeze, triage, dispatch, merge, report.
- Each worker gets one filled-in lens prompt from `references/lens-prompts.md` —
  nothing else. Workers are read-only, launch no sub-agents, return only findings
  rows plus `evidence`, and never write files. Only you merge and write.
- Launch lenses in parallel when the platform supports multiple subagents in one
  turn; otherwise run them sequentially with the same rules.
- Inline threshold: in a `standard` review with a small diff (< ~150 changed
  lines), the single lens may run inline as a dedicated pass applying the same
  prompt. `full-4r` always delegates when subagents are available.
- The refuter is always a single pass — one worker (or one inline pass) with the
  complete candidate batch.
