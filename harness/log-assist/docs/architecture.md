# Architecture

How `log-assist` works inside, and why it is built this way. For **using** it, read
[`USER_GUIDE.md`](USER_GUIDE.md) instead — this document is for someone who will change it.

## The idea everything follows from

**The agent queries the logs. It never receives them.**

No log file is loaded into a context window. A question about a log becomes a command, the
command returns a bounded answer, and the answer carries citations you can check. This is not a
token-saving trick: an agent reasoning over a log it holds in context performs measurably worse
at root-cause analysis than one that queries it, and it cannot show its work.

Every other decision below is a consequence of that one.

## Four layers

```
wrapper          CLAUDE.md / AGENTS.md      what role am I in
  └── orchestrator   orchestrator/LOGA-RUNTIME.md   what happens next, and what gets persisted
        ├── inline         small queries under a guard
        └── worker         .claude|.codex/agents/loga-worker   one step, fresh context
              └── skill    skills/<name>/SKILL.md              how that step is done
                    └── scripts/loga_*.py                      what the logs actually say
```

| Layer | Decides | Must never |
|---|---|---|
| wrapper | whether this session orchestrates or executes one skill | — |
| orchestrator | the next step, what the user confirms, every write to `state.toml` and `SUMMARY.md` | open a log, write inside `record/` |
| worker | nothing about the flow | route a step, launch a descendant, read the runtime |
| skill | how one step is performed and what it writes | write a file it does not own |
| script | what the logs say | interpret, decide, or depend on a shell pipe |

The orchestrator's context holds state and digests only. A worker's context holds one step and
then dies with it. That is what keeps a 335,000-line corpus analyzable in a normal session.

## Who writes what

Ownership is the spine of persistence, because **resume reads from disk, never from the
conversation**.

| File | Owner |
|---|---|
| `state.toml`, `SUMMARY.md` | orchestrator only |
| `record/intake.md` | `loga-intake` |
| `analyses/<id>/logs/` | the orchestrator, applying a plan from `loga-import` |
| `record/inventory.md` | `loga-inventory` |
| `record/findings.md`, `hypotheses.md`, `comparison.md` | `loga-analyze` |
| `record/exploration.md` | `loga-explorer` |
| `record/challenge.md` | `loga-challenger` |
| `reports/*.md` | `loga-report` |
| `record/runs/` | any script, via `--save` |

A step writes its file even when it ends `partial` or `blocked`, with the blocker in its digest.
A worker writing outside its ownership is an incident: the result is discarded, not merged.

`loga-import` is the shape this rule forces: it triages `inbox/` and returns a move plan, because
`logs/` is outside any worker's write scope. The orchestrator applies the plan. Whenever a step
seems to need a wider write scope, returning a plan instead is usually the answer.

Every `record/` file opens with a `## Digest` of 3-6 bullets. The orchestrator reads only those
digests. That is how the conversation stays small while the record stays complete.

## Two gates

1. No log is queried before a minimal intake exists.
2. No report is emitted while `loga_verify_citations` fails on it.

They are enforced in the runtime and repeated in the skills that own them. Gates are satisfied,
never waived.

## Why it is built this way

| Decision | Reason |
|---|---|
| Orchestrator and worker are separate roles | Analysis fills a context. Keeping the deciding context small is what makes the session survive a real corpus |
| One worker role, with no model or effort set | It is a role — allowed skills and write scope — not a performance profile. It inherits the session's model, so upgrading the session upgrades the harness |
| Scripts are Python 3.11, standard library only | Nothing to install, no lock file, and the same command runs on macOS and on Windows |
| Baselines are measured, never hardcoded | webOS emits a heartbeat every 300 s and Tizen every 60 s. Any fixed threshold is wrong on one of them |
| Every claim carries a verified citation | The dangerous error is not a missing citation — it is a real line number with rewritten text. The check compares the excerpt too |
| The catalog is extended by hand | A signature without a counterexample is a guess, and a guess in the catalog produces confident wrong answers indefinitely |
| No shell pipes anywhere | Every filter is a flag, so one command works in bash and in PowerShell |
| Logs enter through `inbox/`, never by hand | People drop whole nested folders with names that mean something only to them. Sorting that out once, explicitly, beats every later script guessing |
| Templates are copied, never generated | The standard library reads TOML but cannot write it. Copying a template keeps its comments — and its allowed values — visible while the file is being filled in |

## Where to change what

| To do this | Edit | Then verify with |
|---|---|---|
| Teach it a new known bug | `scripts/catalog.toml` | `loga_check --all` — examples and counterexamples self-verify on load |
| Add or change a query script | `scripts/loga_*.py`, sharing logic in `scripts/loga_core/` | `scripts/verify.py --corpus <folder>` |
| Change a parser rule | `scripts/loga_core/parser.py` **and** [`log-format.md`](log-format.md) | both corpora — a rule with no evidence does not go in |
| Change what a step does | `skills/<name>/SKILL.md` | `loga_doctor` (drift), then rerun `loga-init` |
| Change routing, gates or delegation | `orchestrator/LOGA-RUNTIME.md` | it has a 150-line budget; if it does not fit, it belongs in a contract |
| Change an artifact's shape | `templates/` | `loga_progress` validates `state.toml` against it |
| Change a rule every skill obeys | `skills/_shared/` | the skills reference these; they do not restate them |

Adding a script means giving it a `SPEC`, so `loga_index` lists it without importing it, and
emitting the standard envelope through `loga_core.cli` — those two things are what make it part
of the harness rather than a loose tool beside it.

## Invariants worth knowing before you change something

- **Section headings are always English**, whatever the configured language. `## Digest` and
  `## Discarded` are parsed; translating them would make parsing depend on a setting.
- **Nothing is written outside `analyses/<id>/`**, except `loga.config.toml`, `inbox/` and the
  skill copies `loga-init` makes. `analyses/` and `inbox/` are gitignored: logs carry customer
  names, and `inbox/` is where they land before anyone has thought about it.
- **Entry ids are never reused**, even after a discard, so an old ticket reference still resolves.
- **Screen identity comes from log content, never from a file name.** A file ending in ` (1)` is
  a different screen, not a duplicate.
- **Level is read positionally, and a nested status overrides the line level.** Counts will not
  match a naive `grep`, and every script that reports by level says so.

## What is deliberately absent

No evals or automated regression suite; no shared knowledge base across analyses; no auto mode;
no Jira integration; no compressed log support. These are v1 scope decisions, not oversights —
`docs/plan/log-assist-plan.md` §2 lists them with their reasoning.

The memory of the harness is two things instead: `scripts/catalog.toml`, which travels with the
repo, and `loga_search` over previous analyses, which stays local.

## Where to read what

[`docs/README.md`](README.md) maps the documentation and says what is authoritative, what is
reference, and what is history.
