---
name: loga-intake
description: >
  Capture the incident in the user's own words before any log is queried: symptom, what was
  expected instead, scope, what changed, what was already tried. Use at step 2, and again
  whenever the analysis returns to needs-info.
---

# loga-intake

## Goal

Turn what the user knows into `record/intake.md`, and satisfy gate 1: the symptom, what was
expected instead, and logs present. Until that is on disk, nothing in the harness may open a log.

## The line that makes this step worth a turn

> The logs know what the player **did**. Only the user knows what was **seen**, and what
> **changed** around it.

So the questions that earn the user's turn are the ones no log can answer: what was on the
screen, who noticed and when, what was deployed or swapped or reconfigured that week, what was
already tried and what it did. Anything a query script will answer later is not asked here — and
at this point the harness has not opened a single log, so there is nothing to look up first
either. Everything at this step is the user's to give.

## Runtime operating rules

Main session, not a worker. Do not route steps: this skill asks, writes its file and returns.

Do not write `state.toml`. Hypotheses and open questions are **returned**; the orchestrator
persists them. Do not open a log, not even to check a date — gate 1 is not open yet.

## Scope

**Should**: read back what is already settled · ask only what no log can answer · keep the
user's words intact · park what they cannot answer.

**Should not**: diagnose · propose a cause · name a component or a platform the user did not
name · ask for something already in `state.toml` or in a previous intake round · infer an answer
from silence.

## Reads / Writes / Scripts

- **Reads**: `state.toml`, `record/intake.md` when rerunning
- **Writes**: `record/intake.md` — and nothing else
- **Scripts**: none

## Workflow

1. Read `state.toml` and any existing intake. Split what is known into **settled** (stated
   explicitly by the user, here or when the analysis was created) and **open** (everything the
   template still needs, plus anything answered with "creo que", "por ahora" or "no sé").
2. Read back the settled set in one short block: *"tomo esto como dado, corregime si no"*. Never
   re-ask it. A user repeating themselves to the harness is the failure this step is designed
   around.
3. Ask one question block over the open set, in dependency order — what happened → on which
   screens → when → what changed around it → what was already tried. Format, size and the
   `saltear N` / `frenar` affordances are in `skills/_shared/loga-user-interaction-contract.md`.
4. Carry a recommendation **where options exist** — scope, dates, platform, which logs to
   request. Leave the question open where the user's own words are the data: the symptom, what
   they expected instead, what changed. Suggesting an answer there contaminates the only
   uncontaminated evidence in the analysis.
5. Route the answers as they come: a cause the user proposes becomes a hypothesis for
   `hypotheses.md` with `source: user`, carrying the same weight as any other open hypothesis;
   anything skipped, unanswered, or belonging to someone who is not in the room becomes an open
   question with the reason. Parking is not dropping.
6. Ask another block only if a gate-1 field is still missing, or if an answer opened a
   genuinely blocking follow-up. Two rounds of polish on a complete intake is a worse outcome
   than starting the analysis.
7. Write `record/intake.md`: symptom **verbatim**, entries tagged `[R<n>]`, nothing from an
   earlier round removed.
8. Read back what the intake now holds and what stayed open, get confirmation, and return.

## Verbatim, and why

"Se ve negro" is written down as "se ve negro". It does not become "black screen after a failed
playlist sync" — that is a hypothesis, and turning it into one here launders a guess into the
record as if the user had said it. Excerpts of what the user reported are quoted, not tidied,
not translated, not diagnosed. Every later step reads this file believing it.

## Artifact shape

`templates/record/intake.md`. Repeatable: a rerun appends a round and never discards or rewrites
what the user said before. If a later round contradicts an earlier one, both stay and the
contradiction is named in the digest — the user changing their account is itself evidence.

## Validation

- Gate 1 is met, or the blocker says exactly which of the three fields is missing.
- The symptom is the user's wording, with no diagnosis in it.
- Every hypothesis the user offered is returned with its `H-xx` route and `source: user`.
- Every skipped or unanswered question is recorded as an open question, with its reason.
- Nothing settled was asked again.
- The digest matches the body.

## Expected output

The five result fields. `status: ok` when gate 1 is met; `blocked` when it is not — and the file
is written anyway, with the missing field named in the digest, so the next attempt starts from
disk rather than from the conversation. `open_risks` carries what is still unanswered and would
limit any conclusion drawn later.
