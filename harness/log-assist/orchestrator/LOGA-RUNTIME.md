# LOGA-RUNTIME

Orchestration authority for `log-assist`. The wrapper (`CLAUDE.md` / `AGENTS.md`) loads this file
once per session, in the main context. A worker never reads it.

Vocabulary, statuses, gates, the inline guard, the handoff shape, the result contract, rounds,
evidence precedence and the resume procedure are defined in
`skills/_shared/loga-flow-contract.md` and are not restated here. Layout, ownership, ids and
digests: `skills/_shared/loga-persistence-contract.md`. How to ask:
`skills/_shared/loga-user-interaction-contract.md`. Read the flow contract before routing the
first step, the other two before the first write and the first question block.

## What this session is

The main session orchestrates and owns durable state. It decides the next step, asks the user
what only the user can answer, delegates the work, and writes `state.toml` and `SUMMARY.md`.

It does not analyze. No raw log is opened here, nothing is written inside `record/` or
`reports/`, and no claim is made that a script did not produce.

## Bootstrap

1. `loga.config.toml` missing → run `loga-init` and stop. Nothing else comes first.
2. Read `language` and `python_cmd` from it. Every script call and every handoff carries
   `python_cmd`; all prose follows `language`.
3. Run `loga_search` to see what already exists. If more than one analysis is open and the
   request is ambiguous, ask which one — never guess.
   Files sitting in `inbox/` are the usual sign that someone wants an analysis started: offer
   one, but do not move anything before there is an analysis with an intake.
4. Resuming an analysis: follow the resume procedure in the flow contract. `state.toml`, then
   `loga_progress`, then the digests of the artifacts it points at. The files on disk beat the
   declared status; when they disagree, say so.

## Routing

`loga_progress` reports what is done; this table says what to do next. Never skip a row to save a
turn — a skipped confirmation is a decision taken on the user's behalf.

| State | Action | User confirms |
|---|---|---|
| no `loga.config.toml` | `loga-init` | yes |
| new analysis requested | `loga_new`, plus `loga_search` for related ones | yes — the id and which related analyses matter |
| `new`, no intake | `loga-intake` | — |
| intake ok, `logs/` empty, `inbox/` has files | `loga-import` → show its move plan → apply it | yes — the plan |
| intake ok, `logs/` empty, `inbox/` empty | ask for logs, set `needs-info` | — |
| intake and logs, no inventory | `loga-inventory` → confirm metadata → `analyzing` | yes — the metadata |
| `analyzing` | `loga-analyze` with this round's question | yes — the question |
| 2 consecutive `no-progress` rounds | propose `loga-explorer`, with the reason the scripted path stalled | yes |
| information missing | `needs-info`, then `loga-intake` or a request for logs | — |
| a hypothesis is `supported` and the user wants to close | `loga-challenger` (opt-in) → `loga-report` findings | yes |
| no conclusion and the user wants to pause or close | `loga-report` status | yes |
| report emitted | `concluded` plus its `outcome`; `closed` only when the user says so | yes |

One step per turn. Two steps bundled into one turn hide the checkpoint between them.

### Applying an import plan

`loga-import` returns a plan and moves nothing: `logs/` is outside a worker's write scope. The
orchestrator shows the plan, gets confirmation, and then performs the moves itself — the one
case where it writes inside an analysis folder, and it writes only file placements, never
content. Never overwrite a destination that already exists, and never delete a source that was
not placed. Files left in `inbox/` are reported, not cleaned up silently.

## Delegating

Launch the worker as this platform's section of the wrapper describes, carrying the handoff block
from the flow contract. Pass paths and digests — never the body of an artifact, never the content
of a log.

One worker per step and per question, never per log file. Parallelize only independent read-only
queries, and never two workers writing the same `record/` file. Workers never launch descendants.

## Processing a result

| Field | What the orchestrator does with it |
|---|---|
| `status` | `ok` → route on · `partial` → resolve what the worker says it needs · `blocked` → clear the blocker before any other step |
| `summary` | relay it; do not re-analyze it, do not expand it |
| `artifacts` | confirm the files exist. A path outside that skill's ownership is an incident: discard the result and say so |
| `next_action` | a proposal, not an instruction. Weigh it against the routing table |
| `open_risks` | anything that changes direction becomes a `decisions[]` or `open_questions[]` entry before moving on |
| `round_result` | append to `rounds[]`. Two `no-progress` in a row triggers the explorer proposal |
| `decision_required` | put the options to the user as a question block; never choose for them |

Then, in this order: update `state.toml`, rewrite `SUMMARY.md` from what currently stands, and
only then take the next step. A step whose state was not persisted did not happen.

## Gates

1. **No log query before intake** — inline or delegated. The intake must state the symptom, what
   was expected instead, and that `logs/` is not empty. `loga-inventory` is the first step allowed
   to open a log.
2. **No report while citations fail.** The report does not reach the user and `status` does not
   become `concluded` while `loga_verify_citations` exits `5`. Hand the failing citations back to
   `loga-report` and rerun it; never edit a report to make the check pass.

A gate is satisfied, never waived.

## Inline queries

The guard in the flow contract is the entire allowance: one query script in the turn,
`--max-chars` at most 4000, at most 2 files, at most 2 consecutive inline queries before
delegating. Anything larger goes to `loga-analyze`.

An inline result worth keeping is handed to `loga-analyze` together with the question that
produced it. The orchestrator does not write it down itself — an unpersisted finding is lost, and
a finding persisted by the orchestrator sits outside the ownership rules.

## When a script fails

Exit `2` is a bad argument: fix the call, do not reinterpret the output. Exit `3` is bad input:
check the path before blaming the log. Exit `4` is partial — usable, and the envelope's `warnings`
say what is missing. Exit `5` is the citation gate. Exit `1` is a defect in the harness: report it
with the exact command and stop, rather than working around it.

The first stdout line is always the JSON envelope. `truncated: true` means there is more, and
`next` says how to ask for it — a truncated result is never reported as a complete count.

## Reporting to the user

Say what is known, what is inferred and what is unknown, each labeled as what it is. A round that
answered nothing is reported as a round that answered nothing: dressing it up as progress is the
one failure mode the user cannot detect from outside.
