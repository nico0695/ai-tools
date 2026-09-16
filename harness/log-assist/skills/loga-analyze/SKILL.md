---
name: loga-analyze
description: >
  Answer one question about the logs with script evidence, and turn the answer into findings,
  hypotheses and — when more than one screen is in scope — a comparison. Use at step 4, once
  per round, with the single question the orchestrator handed over.
---

# loga-analyze

## Goal

Answer **the one question in the handoff**, with evidence a rerun of the same command would
reproduce. Not the incident as a whole, not the next question too: this round's question.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. Do not touch `state.toml` or `SUMMARY.md`.

The question is the boundary. Something important that falls outside it goes into `open_risks`
for the orchestrator to route — it does not silently become this round's work.

## Scope

**Should**: choose the script that answers the question · narrow with flags · cite every claim ·
curate what no longer stands · say when the round found nothing.

**Should not**: read raw log text (that is `loga-explorer`, and only when proposed and
confirmed) · assume a threshold · extend the catalog · report a truncated result as a total ·
keep a finding alive because it was expensive to get.

## Reads / Writes / Scripts

- **Reads**: the digests of `record/intake.md` and `record/inventory.md`, the bodies of
  `record/findings.md` and `record/hypotheses.md`, `record/exploration.md` and
  `record/challenge.md` when they exist
- **Writes**: `record/findings.md`, `record/hypotheses.md`, `record/comparison.md`,
  and full outputs under `record/runs/` via `--save`
- **Scripts**: every query script. Pick with the symptom table in
  `skills/loga-scripts/SKILL.md`; `loga_index` lists what exists.

## Workflow

1. Read the question and the digests. Check what earlier rounds already settled — re-deriving a
   standing finding wastes the round.
2. If the symptom resembles something known, start with `loga_check`: a catalog hit brings its
   own citations and ends the round early. `insufficient_data` means the logs cannot evaluate
   that signature, not that the signature is absent.
3. Choose the narrowest command that answers the question. Filter with flags — `--file`,
   `--level`, `--component`, `--signal`, `--screens` — never with a shell pipe, so the same
   command runs unchanged on Windows. `--save` the outputs that back a finding.
4. Read the envelope first. `truncated: true` means what came back is a page, not a total;
   either page through with `next` or report the figure as "at least N", never as N.
5. Turn results into `F-xx` entries: one observation each, with `screen`, `source`, a resolving
   `file:line` citation with a verbatim excerpt, and a confidence. An observation you cannot
   cite is not a finding — it is a question for the next round.
6. Revisit what already stands. Anything this round contradicts or supersedes moves to
   `## Discarded` with its round transition, the reason and the citation. A refuted hypothesis
   is a result, not a failure.
7. Write hypotheses so they can die: `would confirm` and `would refute` must each name an
   observation **this corpus could actually produce**. Two or more screens in scope → fill
   `record/comparison.md` and promote any divergence worth acting on to an `F-xx`.
8. Update the digests, then return with `round_result`.

## Evidence rules that bind every entry

- **Measure, never assume a threshold.** Cadence, RAM range and error rates differ by platform
  and by screen; webOS ticks every 300 s where Tizen ticks every 60 s. Compare against what the
  scripts measured in *this* corpus, and cite the measurement alongside the claim.
- **Level is read positionally, and a nested status wins over the line level.** When they
  differ, the script says so — carry that note into the entry rather than dropping it.
- **Noise is derived by frequency, never from a list of component names.** Component names vary
  by screen, template and customer.
- **Timestamps carry no timezone.** Comparing clocks across screens is an assumption, and it is
  labeled as one.
- **Correlation is not a mechanism.** "A happens before B" is a finding; "A causes B" needs the
  link, or the hypothesis stays `open`.
- Evidence precedence, when sources disagree, is in `skills/_shared/loga-flow-contract.md`.

## Artifact shape

`templates/record/findings.md`, `templates/record/hypotheses.md`,
`templates/record/comparison.md`. Ids are assigned once and never reused, even after a discard.
Every entry carries the round that produced it.

## Validation

- Every standing claim resolves: the file exists, the line exists, the excerpt matches.
- No threshold appears that the corpus did not produce.
- Every hypothesis names what would refute it.
- Everything discarded this round left a line under `## Discarded`.
- The digests match the bodies.

## Expected output

The five result fields, plus `round_result`. `progress` when the question was answered or a
standing entry moved; `no-progress` when it was not — and that is reported plainly, because two
consecutive `no-progress` rounds are what triggers the explorer proposal. Padding an empty round
as progress disables the harness's only stall detector.
