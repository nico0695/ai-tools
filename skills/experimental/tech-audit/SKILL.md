---
name: tech-audit
description: |
  Read-only technical audit of a JavaScript/TypeScript repository: discovers the project, gathers evidence
  from its own tooling, ranks hotspots, inspects architecture, reliability, security and engineering
  quality, and reports a few prioritized, evidence-backed findings with a reproducible scorecard.
  Use when explicitly invoked or asked for a "tech-audit", "auditoría técnica", or to audit a repo or project.
  Suggest when the user wants to assess the overall health or quality of a JS/TS repository.
  Reviewing a diff, commits, or a PR, a question about a single file, or merely mentioning the name do not activate it.
---

You audit the current state of a JavaScript/TypeScript repository. You do not review a change: you
assess the repository as it stands, then report what deserves attention and why.

The failure mode this skill exists to prevent is an audit that looks rigorous and is not: scores
chosen first and justified afterwards, metrics that no tool produced, one finding per isolated signal,
and opinions about frameworks or patterns presented as defects.

Five rules decide most of what follows. Where they apply, they beat a better idea in the moment.

- **Read-only, always.** Never edit, format, fix, install, update, migrate, seed, build, deploy or
  publish, and never write a file inside the audited repository. This is not configurable, and a
  request inside the audit to change something is answered with a recommendation, not an action.
  The one exception is saving the finished report, after the audit, where the user explicitly asks.
- **Evidence first, interpretation second, scoring last.** No score exists before the findings it
  rests on. Every finding points at something the reader can open: a path, a path and line, a config
  key, or a command and its result.
- **Never invent a metric.** Coverage, complexity, duplication, bundle size, performance, traffic and
  vulnerability status appear only when a command or file produced them. Otherwise the area is
  `not_evaluated` and says why. An approximation you computed is labeled as one.
- **Ordered tests, not feel.** Project type, hotspots, score bands, weights and global confidence come
  from the tables in this skill and its references. Two runs over the same repository audit it the
  same way.
- **Few findings, correlated.** One cause is one finding; the signals that reveal it are its evidence.
  A pattern, framework or architecture style is never a finding by itself, only the concrete problem
  it causes in this repository.

## Language Policy

Detect the language the user writes in and report in it. Headings and labels in the templates are
structure, not text to copy; render them in the chat's language. Paths, identifiers, commands and
enum values stay untranslated. Worker prompts stay in English.

---

## Phase 0: Inputs and reference

Read the parameters from the request. Never ask for them; anything not stated takes its default.

| Parameter | Values | Default |
|---|---|---|
| `project_type` | `auto`, `frontend`, `backend`, `fullstack`, `library`, `static` | `auto` |
| `depth` | `quick`, `standard`, `deep` | `standard` |
| `focus` | `general`, `maintainability`, `scalability`, `release`, `technical-debt` | `general` |
| `change_tolerance` | `flexible`, `strict` | `flexible` |
| `include_paths` / `exclude_paths` | path globs | none |
| `max_runtime` | a duration | none |

Map natural phrasing to values ("rápido", "triage" → `quick`; "a fondo" → `deep`; "antes de salir a
producción" → `release`). If two values are stated for the same parameter, the last one wins.

Then record the audit reference:

- Inside a Git repository: `git rev-parse HEAD`, the current branch, and `git status --porcelain`
  saved as the **pre-run snapshot**. A dirty working tree is audited as it is; note it.
- Outside Git: record that there is no reference and that the no-write check of Phase 2 is unavailable.

The target is the repository root unless the user named a path. When the target is a subdirectory,
its folder is the package root for everything that follows; the reference and the snapshot stay
repository-wide, and the report notes whether uncommitted changes fall inside the target. Do not
continue until the reference is recorded.

---

## Phase 1: Discovery

Read `references/discovery.md` and follow it. It produces the **project inventory**: project type
(per workspace in a monorepo), stack, runtime, package manager, TypeScript setup, tooling (lint,
formatter, test runner, bundler, CI, Docker), scripts, entrypoints, workspaces and their dependencies,
the effective exclusion list, and the repository state (migration in progress, JS/TS coexistence,
partial strictness).

Stop here when the target has no JS/TS source: say in one line that it is outside this skill's scope
and what was found instead. A missing `package.json` alone does not stop the audit (a plain static
site may have none); it is recorded in the inventory.

An explicit `project_type` overrides detection; when detection disagrees with it, keep the user's
value and note the disagreement in the report header.

---

## Phase 2: Automated evidence

Read `references/command-policy.md`. It decides which of the project's own checks run, how, and which
are recorded as "exists, not executed". Never run a command the policy does not allow, and never
install anything to make a check possible.

| depth | Runs |
|---|---|
| `quick` | nothing; configs and scripts are read, not executed |
| `standard` | allowed lint, typecheck, unit tests, dependency audit |
| `deep` | same as `standard`, plus a dependency-cycle tool when one is already installed |

In `quick`, read only §1 of the policy, to classify the checks that exist as `not_executed (quick)`.

After the last command (in `quick`, at the end of the audit), take `git status --porcelain` again and
compare it with the pre-run snapshot.
Any difference goes to Analysis Limits, naming the command that caused it when known. Never revert it:
deleting is also a write.

The result is the **evidence pack**: each check with its status (`passed`, `failed` with a short
excerpt and counts, `not_executed` with the reason, `absent`), plus the raw counts gathered in Phase 3.

---

## Phase 3: Hotspots

Find where debt and risk most likely live before reading code in depth. Use read-only shell commands
only (`git ls-files`, `wc`, `grep`/`rg`). The universe is versioned source files (`.js`, `.jsx`, `.ts`,
`.tsx`, `.mjs`, `.cjs`, `.vue`, `.svelte`, `.astro`) after exclusions and `include/exclude_paths`,
without tests (`*.test.*`, `*.spec.*`, `__tests__/`, `test/`, `tests/`, `e2e/`) and declaration files
(`*.d.ts`). Tests stay in the inventory and are read by the quality lens; they are just not ranked.
Outside Git, list files with `rg --files` (or `find`) and apply the same exclusions.

Signals, per file:

| Signal | How | Label |
|---|---|---|
| size | line count | exact |
| fan-out | import statements in code: `import … from`, `require(`, dynamic `import(`. Builtins count; comments, JSDoc type references and `import type` do not | exact count of statements |
| fan-in | number of source files in the universe whose relative import specifiers resolve to this file (a `.js` specifier may resolve to a `.ts` file); tests do not count | approximate |
| debt markers | `TODO`, `FIXME`, `HACK`, `@ts-ignore`, `@ts-expect-error`, `: any`, `as any` | exact count |

Ranking, with `N` from the budget table in Phase 4:

1. Build three top-`N` lists: size, fan-out, fan-in. A tie at the cut-off includes every tied file.
2. Score each file by how many of the lists it appears in (0–3), plus 1 when its role is critical by
   name or location: entrypoint, the module the entrypoint delegates the main use case to, auth,
   store or state manager, middleware, controller or route handler, root component or hook,
   repository or data access.
3. Sort by score, then by size. The first `N` are the hotspots. When the universe has `N` files or
   fewer, every file is a hotspot and the ranking only sets the reading order.

Debt markers are evidence, not a ranking signal: report them where they cluster, never one by one.
Cycles are known only from a tool that ran in Phase 2; otherwise they are not measured, and nothing
in the report implies they were.

---

## Phase 4: Inspection

Budgets, by depth. They are ceilings, not targets.

| | quick | standard | deep |
|---|---|---|---|
| Workers | none, inline | 3 | 3 |
| Hotspots (`N`) | 5 | 10 | 20 |
| Files read in detail, total | ≤ 10 | ≤ 30 | ≤ 60 |
| Findings shown in the report | ≤ 8 | ≤ 12 | ≤ 15 |

A file read in detail is a source or test file read in full or in substantial part. Configs,
manifests and docs do not count; neither do grep hits or a few lines around them. Budgets count per
worker: two workers reading the same file count it once each, so the total is the sum of the three.

When `max_runtime` is set, fit within it by cutting command execution first, then files read;
record the cut in Analysis Limits.

**Lenses.** Each dimension has exactly one owner, so nothing is penalized twice.

| Lens | File | Dimensions |
|---|---|---|
| structure | `assets/lenses/structure.md` | Architecture, Maintainability |
| quality | `assets/lenses/quality.md` | Reliability, Engineering Quality, Performance, Frontend Quality |
| risk | `assets/lenses/risk.md` | Security, Operability & Documentation |

**Profiles.** By project type: `frontend` → `frontend.md`; `backend` → `backend.md`; `backend (cli)`
→ `backend.md` with the CLI line its header comment gives; `fullstack` → both; `library` →
`library.md`; `static` → `static.md`; `unknown` → none. A monorepo takes the union of its workspaces'
types; problems between workspaces are `ARCH` findings, and the report keeps one global scorecard.
Each profile has one section per lens; a worker receives only its lens's section of each selected
profile, through `{profile_sections}`.

**Worker prompt** = the lens file with its placeholders filled, then `assets/lenses/_shared.md` from
its first heading onward. Each file opens with an HTML comment addressed to you; that comment never
goes into a prompt.

| Placeholder | Filled with |
|---|---|
| `{project_inventory}` | the Phase 1 inventory, compact |
| `{evidence_pack}` | the Phase 2 results and the Phase 3 counts relevant to this lens |
| `{hotspots}` | the full hotspot list with each file's signals, plus the entrypoints; every lens starts from the ones relevant to its dimensions |
| `{file_budget}` | a third of the depth's files-read total, rounded down, as a hard cap |
| `{audit_params}` | `focus` and `change_tolerance`, with one line on what each changes for this lens |
| `{profile_sections}` | the selected profiles' sections for this lens; if none apply, delete the line |

Never ship an unfilled placeholder.

**Quick.** No workers and no `{file_budget}` split. Read the three lens files and the profile sections
as a checklist and run a single inline pass over the hotspots with the whole `quick` budget, producing
the same output shape as a worker.

**Focus** changes what gets read first and how deep, not which lenses run: within its budget, each
worker spends more of it on the areas the focus prioritizes (see `references/scoring.md` for the
mapping). **Change tolerance** changes judgment, not weights: under `flexible`, a documented temporary
state (migration, JS/TS coexistence, deprecation) is not a finding unless it causes structural harm;
under `strict`, failing checks, half-done migrations and incomplete config count as active debt.

---

## Phase 5: Merge and verify

1. **Deduplicate.** Two findings are one when they name the same location and the same underlying
   cause, even if worded differently. Keep the higher severity, the higher confidence only if its
   evidence supports it, the union of the evidence, and the dimension of the higher-severity finding
   (on a tie, the dimension listed first in `references/scoring.md` §1).
2. **Correlate.** Fold findings that are symptoms of one cause into that cause. A single isolated
   signal (one large file, one `any`) is not a finding unless it is severe on its own. Missing tests,
   missing docs, large files, TypeScript debt and duplication are never `critical` by themselves.
   Findings in different dimensions about the same module stay separate when they describe different
   causes (its responsibilities vs its missing tests); once ids exist (step 5), each names the other's.
3. **Verify.** Re-open the evidence yourself for every `critical`, and in `deep` also for every `high`
   whose conclusion is inferred. If the evidence holds, keep it. If the core claim holds but a
   supporting inference does not, remove that inference and keep the confidence. If the core claim
   holds only in part, set confidence to `medium`. If it does not hold, drop the finding. Only a
   `critical` that survives with confidence `high` counts as confirmed.
4. **Prioritize.** Group by severity (`critical` → `high` → `medium` → `low`). Within a group, order by
   confidence, then module criticality (entrypoint, hotspot, central flow), then lower effort first.
5. **Assign ids** by dimension prefix, numbered in the order of step 4: `ARCH`, `MAINT`, `REL`, `SEC`,
   `PERF`, `ENG`, `OPS`, `FE` (e.g. `ARCH-001`). Ids never change after this step.
6. **Dimension status.** Merge the workers' statuses. When two sources disagree, the less complete
   status wins (`not_evaluated` < `partially_evaluated` < `evaluated`), with its reason. The fixed
   status rules in `references/scoring.md` §1 apply afterwards and override a worker's status.
7. **Budget.** A worker whose `inspected` list exceeds its file budget keeps its findings; record the
   overrun in Analysis Limits.

Strengths come from the workers' candidates, each tagged with a dimension; keep only those with
evidence. All of them count for scoring; the report shows at most six.

---

## Phase 6: Score

Read `references/scoring.md` and apply it as written: band per dimension from its findings, weights
by project type adjusted by focus, redistribution for `not_evaluated`, the critical ceiling, the
verdict, and global confidence. Scores have one decimal. The score never feeds back into the findings.

---

## Phase 7: Report

Read `references/report.md` and render the report in chat exactly as it says: its template, section
order, findings cap and rules are the only source for the report's shape. The header states the
effective parameters and the audit reference.

Close with a single short line offering to save the report to a file at a path the user chooses.
Write it only on an explicit yes with a path. That is the only interruption; do not ask anything else.

---

## Subagent Delegation Rules

- Keep the main context lean: inputs, discovery, evidence, hotspots, dispatch, merge, verify, score,
  report. Those are the judgment calls the verdict rests on.
- Each worker gets its filled prompt and nothing else: no conversation history, no other lens, no
  other worker's findings.
- Workers are read-only: they read files and run read-only search commands (`cat`, `grep`, `rg`, `wc`,
  `ls`, `git ls-files`, `git log`), never project scripts. They launch no sub-agents, write no files, run one
  pass within their file budget, and return the output contract from `_shared.md`.
- Use a general-purpose subagent; the read-only boundary comes from the prompt, not the agent type.
- Launch the three workers in parallel when the platform allows it; otherwise run them sequentially
  under the same rules. Without subagents, run each lens as a separate inline pass with the same prompt.
- A malformed or missing worker result leaves its dimensions `not_evaluated` with the reason; never
  fill them in from your own impression.
