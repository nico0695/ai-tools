---
name: loga-report
description: >
  Write the report a human acts on — findings when there is a conclusion, status when the
  analysis pauses without one — and clear the citation gate before it is shown. Step 5b.
---

# loga-report

## Goal

Produce one dated report under `reports/`, built only from what the record already holds, with
every citation verified. The report is the artifact that leaves the harness: it is read by
someone who will not open the logs.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. Do not touch `state.toml` or `SUMMARY.md`.

**This skill owns gate 2.** `loga_verify_citations` must exit `0` on the report before it is
returned. Exit `5` means the report is not emitted — fix the citations and rerun. Never edit a
citation to make the check pass: the check exists because a plausible-looking citation pointing
at the wrong line is the failure the reader cannot catch.

## Scope

**Should**: report what the record established · state the mechanism when there is one · be
explicit about limits · make the ruled-out section useful.

**Should not**: introduce a finding that is not in `record/` · run a new query to strengthen the
story · upgrade `probable` to `confirmed` because the report reads better · hide a coverage gap
in a subordinate clause.

## Reads / Writes / Scripts

- **Reads**: the bodies of everything in `record/`, including the `## Discarded` sections;
  `state.toml` for `ref`, `title` and the incident window
- **Writes**: `reports/<YYYYMMDD>-findings.md` or `reports/<YYYYMMDD>-status.md` — and nothing
  else. A report already on disk is never edited: a new emission is a new dated file.
- **Scripts**: `loga_verify_citations` (mandatory). No query script: new evidence means another
  `loga-analyze` round, not a report that quietly grew.

## Workflow

1. Take the type from the handoff. `findings` when there is a conclusion; `status` when the
   analysis pauses or closes without one. If the record does not support the requested type, say
   so and return `blocked` rather than writing the wrong one.
2. Collect what currently stands — live entries only. Anything under `## Discarded` belongs in
   `Ruled out`, never in the evidence table.
3. Write the conclusion as a mechanism, not a restatement of the symptom. If the chain from
   cause to symptom has a missing link, the outcome is `probable` and the report names the link
   that is missing.
4. Build the evidence table: one row per `F-xx` that carries the conclusion, with its citation.
   Excerpts stay verbatim. An entry sourced from `loga-explorer` and never reproduced is labeled
   as exploratory, wherever it appears.
5. Write `Limits` concretely: what these logs cannot show, and what would be needed — more days,
   another screen, a specific counter. "More investigation is needed" is not a limit.
6. Write the `For Jira` block: 5 to 8 lines someone can paste without editing.
7. Run `loga_verify_citations` on the file. Exit `5` → fix and rerun until it exits `0`. If a
   citation cannot be made to resolve, remove the claim it supports and say so in the digest.
8. Return, naming the verification result.

## Length and audience

Under 800 words. The reader is a support engineer or a developer who has the ticket and not the
logs, so every claim is either cited or labeled as an inference, and the outcome value —
`confirmed`, `probable`, `inconclusive`, `not-an-issue` — is stated in words, not implied by
tone. `inconclusive` with a clear account of what is missing is a good report.

## Artifact shape

`templates/reports/findings.md` or `templates/reports/status.md`. The date in the file name is
`YYYYMMDD`; dates inside the document are ISO strings.

## Validation

- `loga_verify_citations` exits `0`. Nothing is returned before that.
- Every claim traces to an entry in `record/`; the report introduced nothing new.
- Nothing discarded appears as evidence.
- The outcome named matches what the evidence supports.
- Under 800 words, and the `For Jira` block is pasteable as is.

## Expected output

The five result fields. `artifacts` names the report path. `status: blocked` when the citation
gate cannot be cleared or the record does not support the requested type — with the report file
written anyway and the blocker in its digest, so the next run starts from disk. The orchestrator
sets `concluded` and its `outcome` only after this returns `ok`.
