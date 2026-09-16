---
name: loga-import
description: >
  Triage the log files waiting in inbox/ and move the ones that belong to this analysis into
  its logs/ folder, renaming on collision and leaving everything else behind with a reason.
  Use at step 3, once the intake is done and the analysis has no logs yet.
---

# loga-import

## Goal

Get the right files from `inbox/` into `analyses/<id>/logs/`, so the analysis can start. People
drop whole folders, nested and mixed, with names that mean something only to them — this step
sorts that out once, explicitly, instead of leaving it to every later script.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. Do not touch `state.toml` or `SUMMARY.md`.

**This skill proposes; the orchestrator moves.** A worker's write scope is
`analyses/<id>/{record,reports}`, and `logs/` is outside it. So the plan comes back as part of
the result and the orchestrator executes it, which keeps the write-scope rule intact.

This step runs **after** the intake. Gate 1 is already open by then, so reading the inbox with a
script is allowed — but nothing found here is a finding. The triage exists to identify and place
files, not to explain the incident.

## Scope

**Should**: find every log under `inbox/`, however it is nested · identify which screen each one
belongs to · propose a destination for each · say what it is leaving behind and why.

**Should not**: diagnose · draw conclusions from what it scanned · overwrite anything · delete a
file it did not place · unzip an archive · move something it could not identify.

## Reads / Writes / Scripts

- **Reads**: `inbox/` (recursively), `record/intake.md` digest, `state.toml` for the analysis id
- **Writes**: nothing directly. Returns the move plan; the orchestrator applies it
- **Scripts**: `loga_scan --path inbox/` for the triage

## Workflow

1. Walk `inbox/` recursively. Folder depth is not a signal — people zip and unzip and re-nest,
   so a file three levels down is as valid as one at the top.
2. Split what is there. **Candidate logs**: text files that parse as Dex Player lines.
   **Leftovers**: everything else — screenshots, `.zip` (compressed logs are out of scope in
   v1 and are never unzipped), `.DS_Store`, spreadsheets, anything that does not parse.
3. `loga_scan --path inbox/` over the candidates: screen, platform, player version, date range,
   parse rate. Minimal by design — this is identification, not inventory. `loga-inventory` does
   the real scan afterwards, over the files once they are in place.
4. Decide the destination layout. One screen → `logs/` flat. Two or more → `logs/<screen>/`,
   exactly one level deep, as the persistence contract requires.
5. Decide names. **Keep the original file name**: it is what the user's ticket refers to, and
   renaming it silently breaks that link. Rename only to resolve a collision — two folders each
   holding `20260220-0.log` — by prefixing with the source folder, never by overwriting and
   never by appending a counter that means nothing.
6. Check the files against the intake: if a date range or a screen has nothing to do with the
   incident window, say so in the plan rather than moving it quietly. The user decides.
7. Return the plan: one row per file with source, destination and reason, plus the leftovers
   list with why each one stayed.
8. The orchestrator shows the plan, gets confirmation, moves the files, and reports what
   remains in `inbox/`.

## The move, once approved

Moves are destructive by design: `inbox/` is a staging area, and the originals live wherever the
user downloaded them. Still, two rules hold without exception:

- **Nothing is overwritten.** A collision is resolved in the plan, before anything moves. If a
  destination already exists and was not accounted for, stop and report.
- **Nothing is deleted that was not placed.** Leftovers stay in `inbox/` with their reason. A
  non-empty inbox after an import is not a failure — it is the signal that something needs a
  human look.

## Validation

- Every candidate log has a destination in the plan, or an explicit reason it has none.
- No destination path collides with an existing file or with another row of the plan.
- Original file names are preserved except where a collision forced a prefix.
- The layout is `logs/` flat or `logs/<screen>/` one level deep — never deeper.
- Every leftover is listed with why it stayed.
- Nothing in the plan claims anything about the incident.

## Expected output

The five result fields, plus the move plan in `summary` or as a table in `next_action`.
`status: ok` when every candidate has a destination; `partial` when some file could not be
identified — it stays in the inbox and is named; `blocked` when `inbox/` holds no parseable log
at all, in which case the next action is asking the user for the logs, not retrying.

`round_result` is `progress` when files were placed.
