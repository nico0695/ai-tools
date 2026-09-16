---
name: loga-challenger
description: >
  Attack the standing conclusion before it becomes a report: alternative explanations,
  correlation read as cause, coverage the evidence never had. Opt-in, step 5a, on the user's
  explicit request.
---

# loga-challenger

## Goal

Try to break what the analysis believes. The value of this step is entirely in how honestly it
fails: a challenge that sets out to confirm the conclusion produces nothing, and costs a round.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. Do not touch `state.toml` or `SUMMARY.md`.

Do not edit `findings.md` or `hypotheses.md`. This skill writes a verdict; `loga-analyze` is what
acts on it. Attacking and rewriting in the same pass hides what the attack found.

## Scope

**Should**: argue against each standing hypothesis · look for the explanation nobody proposed ·
check whether the evidence would look the same on a healthy screen · verify counts survive the
corpus traps.

**Should not**: invent an alternative it cannot cite · reject a hypothesis for being
uncomfortable · soften a verdict because the analysis took effort · re-run the whole analysis.

## Reads / Writes / Scripts

- **Reads**: the bodies of `record/findings.md`, `record/hypotheses.md`, `record/intake.md`,
  `record/inventory.md`, and `record/comparison.md` / `record/exploration.md` when they exist
- **Writes**: `record/challenge.md` — and nothing else
- **Scripts**: any query script, to test an alternative. `loga_compare` and `loga_gaps` are the
  usual ones: they answer "did a healthy screen do the same thing?" and "was the screen even
  reporting then?".

## Workflow

1. Read what currently stands, and the intake — including the user's own hypotheses, which are
   the ones most often left unaddressed.
2. Work the checklist in the template. Each row gets a verdict and evidence, including the rows
   that pass.
3. **Coverage first.** Do the logs actually cover the incident window? A conclusion drawn from
   days that do not include the incident fails here and nothing below it matters.
4. **Correlation as cause.** For each hypothesis, ask what else produces the same sequence. Boot
   banners, scheduled reboots, clock corrections and stack traces all look like events and are
   not. Name the alternative and cite it, or say the attack found nothing.
5. **The healthy-screen test.** Would this evidence look the same on a screen with no problem?
   When another screen is in scope, `loga_compare` answers it instead of an opinion.
6. **The counts.** Boot count halved for the 53-`=` banner? Stack-trace frames excluded from the
   ERROR count? Noise derived by frequency and not from a name list? Any figure that fails this
   is attacked with the corrected number.
7. Give each hypothesis a verdict — `holds`, `weakened` or `refuted` — with the strongest
   argument against it, what survives that argument, and what observation would end the debate.
8. Write `record/challenge.md` and return.

## Artifact shape

`templates/record/challenge.md`. Appends a round.

## Validation

- Every checklist row has a verdict, including `unknown` where the logs cannot say.
- Every alternative explanation carries a citation, or is declared as unverified speculation.
- Every standing hypothesis has a verdict — none is skipped for being obviously right.
- The weakest point of the analysis is named in the digest, even when the verdict is that
  everything holds.

## Expected output

The five result fields, plus `round_result`. A challenge that changes nothing still returns
`ok`, with the digest saying plainly that the conclusion survived and which attacks it survived —
that sentence is what makes the report trustworthy. `open_risks` carries anything that should
appear in the report's `Limits` section.
