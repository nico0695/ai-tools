# loga-flow-contract

Canonical vocabulary for `log-assist`: what the steps are called, what a status means, how work reaches a worker, and what comes back. Skills and the runtime resolve these names here instead of restating them.

## Steps

| # | Step | Runs in | Owns |
|---|---|---|---|
| 0 | `loga-init` | main session | clone setup, once per clone |
| 1 | `new` | main session, via `loga_new` | `analyses/<id>/` and its `state.toml` |
| 2 | `loga-intake` | main session | `record/intake.md` |
| 2b | `loga-import` | worker, when `inbox/` has files | the move plan; the orchestrator applies it |
| 3 | `loga-inventory` | worker | `record/inventory.md` and suggested metadata |
| 4 | `loga-analyze` | worker | `record/findings.md`, `record/hypotheses.md`, `record/comparison.md` |
| 4b | `loga-explorer` | worker, opt-in | `record/exploration.md` |
| 5a | `loga-challenger` | worker, opt-in | `record/challenge.md` |
| 5b | `loga-report` | worker | `reports/<YYYYMMDD>-<type>.md` |
| 6 | `close` | main session | `status = closed` |

`loga-scripts` is reference material, not a step: workers load it to learn how to call scripts and read their output.

## Status and outcome

`status` is declared in `state.toml` and is always exactly one of:

| Value | Means | Who may set it |
|---|---|---|
| `new` | the folder exists, intake has not run | `loga_new` |
| `analyzing` | intake and inventory are done, rounds are running | orchestrator, once the user confirms the inventory metadata |
| `needs-info` | blocked on the user or on missing logs | orchestrator |
| `concluded` | a report was emitted and its citations verified | orchestrator, after `loga-report` |
| `closed` | the user closed the analysis | orchestrator, only on explicit user instruction |

`outcome` stays empty until `concluded`, then becomes exactly one of `confirmed` | `probable` | `inconclusive` | `not-an-issue`.

Status is **declared**; progress is **derived**. `loga_progress` validates `state.toml`, computes what is actually done from the files on disk, and suggests the next step. It never writes.

## Hard gates

1. **No log query before a minimal intake.** The intake must state the symptom, what was expected instead, and that `logs/` is not empty. `loga-inventory` is the first step allowed to touch `logs/`.
2. **No report while citations fail.** `loga_verify_citations` must exit `0` on the report before it is shown to the user and before `status` becomes `concluded`. Exit `5` means the report is not emitted.

A gate is satisfied, never waived. User impatience is not a reason to pass one.

## Delegation and the inline guard

The orchestrator runs inline: reads of `state.toml` and of `## Digest` sections, `loga_progress`, `loga_search`, `loga_new`, `loga_doctor`, and its own writes to `state.toml` and `SUMMARY.md`.

A log query may run inline only when all three hold:

1. one query script in the turn, with `--max-chars` at most `4000`;
2. at most 2 files in scope;
3. at most 2 consecutive inline queries without delegating.

Everything else is delegated to `loga-analyze`. The orchestrator never opens a log with a file-reading tool and never writes inside `record/`. An inline result worth keeping is handed to `loga-analyze` together with the question that produced it, so that the worker — not the orchestrator — persists it.

## Handoff

The orchestrator passes paths and digests, never pasted artifact bodies:

```yaml
loga_role: worker
skill: <loga-inventory | loga-analyze | loga-explorer | loga-challenger | loga-report>
orchestration_allowed: false
analysis_id: <ref>-<slug>
analysis_path: analyses/<ref>-<slug>/
round: <n>
question: <the single question this round answers>
inputs:
  - <path> — <digest of 3 to 6 bullets>
python_cmd: <from loga.config.toml>
language: <from loga.config.toml>
```

A worker that receives these controls does not read the runtime, does not route, and does not launch descendants.

## Result contract

Every skill returns these five fields and nothing longer:

| Field | Content |
|---|---|
| `status` | `ok` \| `partial` \| `blocked` |
| `summary` | at most 5 lines, in the configured language |
| `artifacts` | the paths written, relative to the repo root |
| `next_action` | one concrete action, or `none` |
| `open_risks` | risks the orchestrator must weigh before routing; empty list if none |

Optional: `round_result` (`progress` \| `no-progress`, required from repeatable skills) and `decision_required` with `decision_options` when the user must choose.

- `partial`: useful work landed but the next step depends on a user decision.
- `blocked`: there is no safe next step without a decision or a missing input.
- **Write invariant**: `partial` and `blocked` still write the artifact, with the blocker recorded in its digest. Resume always reads from disk, never from the conversation.

## Rounds

Repeatable skills (`loga-intake`, `loga-inventory`, `loga-analyze`, `loga-explorer`, `loga-challenger`) append one entry to `rounds[]` in `state.toml` per run: `{n, skill, question, result}`. New entries in an artifact carry their round tag, as in `F-07 [R3]`.

Two consecutive `no-progress` rounds are the trigger for the orchestrator to propose `loga-explorer`, with the reason stated. The user confirms; it never starts on its own.

## Evidence precedence

When sources disagree, the higher row wins and the conflict is recorded:

1. output of a query script, reproducible by rerunning the same command
2. an artifact entry in `record/` that carries a resolving `file:line` citation
3. what the user stated
4. model memory — never a source; if it is all there is, the answer is "not verified"

A finding from `loga-explorer` is exploratory: it cannot support `outcome: confirmed` until a script reproduces it or the user validates it.

## Resume

Read `state.toml` first, then run `loga_progress`, then read the `## Digest` of the artifacts it points at. Validate the declared status against the files on disk; if they disagree, trust the files and say so. Resume at the first step `loga_progress` reports as unfinished. If two or more analyses are open and the request is ambiguous, ask which one — never guess.
