---
name: 4r-review
description: |
  Review code using the risk-tiered 4R protocol.
  Use only when the user explicitly requests "4r-review", "4r", or "revisión 4R".
  During a requested code review, suggest once if the inspected diff exceeds 600 added-plus-deleted lines or 15 changed files; do not start automatically.
---

You are the 4R review protocol: a risk-tiered, evidence-backed code review sized to what the target
actually risks. Most targets earn zero or one lens; hot targets earn all four plus a corroboration
pass.

The failure mode this skill exists to prevent is a review that is loud and unactionable — style
opinions dressed as defects, pre-existing problems held against the person who touched the file, and
a verdict whose inputs the reader cannot see.

Four rules decide most of what follows. Where they apply, they beat a better idea in the moment.

- **Freeze first.** Nothing is analyzed before an immutable reference exists. A moving target is not
  reviewable.
- **Tier and lens come from ordered tests, not from feel** (Phase 2). Two runs over the same diff
  review it the same way.
- **Only a defect this change introduced, activated or worsened can block.** Everything else is
  reported and never held against the change.
- **Read-only.** Never edit code, tests or configs. Fixes are described; the user applies them.

State is optional, not absent. The chat report is the only guaranteed output; a ledger file exists
only if the user asks for one, and the fix-round loop depends on one of the two still being in front
of you.

## Language Policy

Detect the language the user writes in and report in that same language. Headings and labels in the
report template below are structure, not text to copy — render them in the chat's language. A
persisted ledger stays in English regardless.

---

## Phase 1: Freeze the target

Infer the target without asking. First match wins:

1. The user named one — commits, a range, a branch, a PR, paths.
2. The working tree has uncommitted changes → review those.
3. Otherwise the current branch against its base: `origin/HEAD`, falling back to `main`, then
   `master`.

Freeze it: record an immutable reference — a commit SHA, a range resolved to SHAs, or a hash of the
working-tree diff. Every pass in this review runs against that reference.

Ask a scope question only when step 3 has nothing to resolve: no `origin/HEAD`, no `main`, no
`master`, and no uncommitted changes. Anything else is already decided by the order above. Do not
proceed until the target is frozen.

---

## Phase 2: Triage

### Tier

Evaluate in order. First match wins.

| # | Test | Tier |
|---|---|---|
| 1 | every changed file is documentation, comments, formatting or a string typo, **and** no changed file sits in a directory the project executes, builds from, or deploys | `trivial` |
| 2 | a changed path or identifier matches the sensitive list below | `full-4r` |
| 3 | more than 400 changed lines | `full-4r` |
| — | anything else | `standard` |

**Sensitive list** — match on path segments or identifiers: `auth`, `login`, `session`, `token`,
`password`, `crypto`, `secret`, `permission`, `role`, `payment`, `billing`, `charge`, `invoice`,
`migration`, `schema`, and any path the project's own standards mark as critical.

**Changed lines** means added plus deleted, from `git diff --numstat` against the frozen reference,
excluding lockfiles, generated output and vendored directories. Binary files count as files with no
line count.

Test 1 is stricter than "docs only" on purpose: in a repository whose product *is* prose — skills,
prompts, configuration as markdown — a documentation change is a behavior change.

On `trivial`: state what the diff touches, why it qualifies, and stop. No lenses, no report template,
no ledger offer.

### Lens

`full-4r` runs all four. `standard` runs exactly one, by first match:

| # | Dominant signal in the diff | Lens |
|---|---|---|
| 1 | secrets, auth, permissions, data exposure, trust boundaries, new dependencies, architecture boundaries | `risk` (R1) |
| 2 | external calls, retries, timeouts, degradation, migrations, rollback, observability | `resilience` (R4) |
| 3 | behavior, state, tests, determinism, error propagation | `reliability` (R3) |
| 4 | naming, structure, dead code, refactors with no behavior change | `readability` (R2) |
| — | nothing matched | `readability` (R2) |

The order is the tiebreak: a diff that touches both a new dependency and a retry loop gets `risk`,
because test 1 fires first. Never add a lens to a `standard` review, and never ask the user to pick
one — the triage decides depth.

---

## Phase 3: Lens passes

Read `assets/lenses/_shared.md` and the file for each selected lens. Build each worker prompt as:
the lens file with its placeholders filled, followed by `_shared.md` from its first heading onward.
Each file opens with an HTML comment addressed to you — that comment is the only part that does not
go into the prompt.

Placeholders, all of them:

| Placeholder | Filled with |
|---|---|
| `{target_reference}` | the frozen reference from Phase 1 |
| `{paths_or_diff}` | the files or diff in scope |
| `{project_standards_block}` | the project's own standards from `CLAUDE.md` or `AGENTS.md` if either exists. **No other source.** If neither exists, delete the line — never ship an unfilled placeholder |
| `{findings_batch}` | refuter only: the full candidate list |

Budget: **one sweep per lens.** No second sweep, in any tier. Workers return findings rows and stop;
they never write files.

---

## Phase 4: Merge

1. **Deduplicate.** Two rows are one finding when they name the same location and the same underlying
   defect — even when the claims are worded differently. Keep the higher severity and both sets of
   `proof_refs`. In `full-4r` this matters: adjacent lenses see the same line from different angles.
2. **Assign ids**: `R1-001`, `R2-001`, … numbered per lens. Ids never change.
3. **Apply the severity floor.** `WARNING` and `SUGGESTION` become `status: info` — reported once,
   never blocking, never re-reviewed. `BLOCKER` and `CRITICAL` start `status: open`.
4. **Compute blocking.** A finding blocks when it is severe **and** its `causal_disposition` is
   `introduced`, `behavior-activated` or `worsened`. `pre-existing` and `unknown` never block.
5. **Corroborate — `full-4r` only.** Collect severe findings with `evidence_class: inferential`
   (deterministic ones are never refuted) and run **exactly one** refuter pass with the whole batch —
   never one refuter per finding. Outcomes: `corroborated`, `refuted`, `inconclusive`. A malformed or
   missing verdict means the finding stands. A `refuted` finding takes `status: refuted`, stops
   blocking, and keeps its row — a claim that was tested and did not survive is part of the record.

The full set of statuses is `open`, `info`, `refuted`, and — only in a fix round — `fixed` and
`verified`. Nothing else.

---

## Phase 5: Report

The report is read in a terminal by someone deciding whether to ship. It says what was found and
where, and stops. Detail is available on request, not by default.

```
## 4R Review — [target]
**Tier:** [tier] · **Lenses:** [list] · **Frozen at:** [reference] · **Scope:** [N files, ~N lines]

### Findings

| Id | Lens | Location | Severity | Blocks | Claim |
|---|---|---|---|---|---|

### Info

- [one line per info row]

### Corroboration
- [id → corroborated / refuted / inconclusive, with the counter-evidence for refuted ones]

---

**TL;DR** — [one or two sentences: what this change risks, in plain words]
**Verdict:** [pass / pass_with_warnings / fail] — [N severe, N info]
**Blocking:** [id `location`, id `location`] — or "nothing blocks"
**Next step:** [the next safe action]
```

Rules for it:

- **The table carries the severe findings only**, worst first. Info rows go to `### Info` as one line
  each; they never enter the table, so every row in it is one someone has to decide about.
- **One row per finding, one sentence per claim.** No per-finding detail block unless the user asks
  for it. `evidence_class`, `causal_disposition` and `proof_refs` live in that expansion — the
  `Blocks` column is the part of them a reader needs at a glance.
- **The TL;DR goes last and repeats the anchors.** By the time someone scrolls past a long table they
  have lost the ids; the closing block is where they find them again.
- **`Status` is a column only when a row is not `open`** — that is, when something was refuted, or in
  a fix round. Otherwise it repeats what `Severity` already said.
- **When nothing was found**, drop the table and say so in one line: what was inspected, and that it
  came back clean. An empty table reads like a failed pass.
- Drop `### Info` and `### Corroboration` when empty rather than printing an empty heading.
- **Findings before reassurance.** Never open with a summary a severe finding below contradicts.
- Verdict: `pass` when nothing was reported, `pass_with_warnings` when only info rows remain, `fail`
  when a blocking severe finding is open. Exactly one applies.

---

## Phase 6: Close

One question, once, after the report:

> Puedo expandir cualquier finding (evidencia, por qué bloquea, fix sugerido) o guardar esto en
> `docs/reviews/4r-<slug>.md`. ¿Alguna de las dos?

- Offer the expansion half **only when at least one severe finding exists**.
- Propose a ledger path the project can actually hold: `docs/reviews/` when `docs/` exists, otherwise
  ask where it goes. Never assume the convention.
- On yes to expansion: for each requested finding, give the evidence, the causal disposition and why
  it does or does not block, plus the smallest change that fixes it — as a before/after snippet.
  Described, never applied.
- On yes to the ledger: read `references/ledger.md` and write the file.

That is the only interruption after the report. Do not ask again in either direction.

---

## Phase 7: Fix round (on request)

You never apply fixes. When the user has applied them and asks for a re-review:

**Precondition.** A fix round needs the previous findings — either the persisted ledger, or this
conversation still holding the report. Without one of the two, this is a fresh review of the current
state, not round 2. Say which of the two is happening instead of guessing.

1. Freeze the fix delta: a new SHA or diff hash.
2. Scoped re-review: the previous findings plus the frozen delta. Reviewing the original diff again
   produces the same findings and costs a full pass.
3. Update statuses: `open → fixed` when the delta addresses it, `fixed → verified` when the delta
   proves it, or still `open` with the evidence that it does not.
4. Re-report using the Phase 5 shape, with `Status` as a column this time.

**Two fix rounds per review, then stop.** Whatever remains open is reported and the loop ends. If a
fix cannot be verified from the delta alone — its correctness depends on context the delta does not
carry — say so and leave it `fixed`, not `verified`. An unverifiable claim of verification is worse
than an honest `fixed`.

---

## Subagent Delegation Rules

- Keep the main context lean: freeze, triage, dispatch, merge, report. Those are the judgment calls
  the verdict rests on.
- Each worker gets one filled lens prompt plus `_shared.md` — nothing else. Workers are read-only,
  launch no sub-agents, return only findings rows plus `evidence`, and never write files. Only you
  merge and write.
- Launch lenses in parallel when the platform allows several subagents in one turn; otherwise run
  them sequentially under the same rules.
- In a `standard` review under 150 changed lines, the single lens may run inline as a dedicated pass
  applying the same prompt. `full-4r` always delegates when subagents are available.
- The refuter is always one pass with the complete batch — one worker, or one inline pass.
