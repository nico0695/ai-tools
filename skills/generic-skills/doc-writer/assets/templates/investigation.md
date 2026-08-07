---
template:
  id: investigation
  name: Investigation Report
  description: Records a question, the evidence gathered, and what that evidence supports - including the hypotheses that were examined and rejected.
  audience: [developers, decision makers, whoever picks this up next]
  use_when:
    - a question was researched and the findings need to survive the session
    - debugging or analysis produced conclusions someone will act on
    - a recommendation needs its evidence attached
  required: [question, evidence, findings, conclusion, summary]
  optional: [context, observations, hypotheses, rejected-hypotheses, unknowns, recommended-actions]
  visuals: [flow, sequence, timeline]
  toc: required
---

# Investigation: [Question]

> [One or two lines: what was investigated and what came out of it.]

## Table of Contents

- [Question](#question)
- [Context](#context)
- [Evidence](#evidence)
- [Observations](#observations)
- [Findings](#findings)
- [Hypotheses](#hypotheses)
- [Rejected Hypotheses](#rejected-hypotheses)
- [Conclusion](#conclusion)
- [Unknowns](#unknowns)
- [Recommended Actions](#recommended-actions)
- [Summary](#summary)

## Question

[The question this investigation set out to answer, stated precisely enough to be answerable. A vague
question produces a document nobody can act on.]

## Context

[Why this was investigated, what prompted it, what was already known going in.]

## Evidence

[What was examined and what it showed. Each item traceable — a file and line, a log excerpt, a
measurement, a commit. Evidence is what makes the conclusion reviewable rather than trusted.]

| Source | What it shows |
|---|---|

## Observations

[What was seen, separated from what it means. Keeping observation and interpretation apart is what
lets a later reader disagree with the conclusion without discarding the work.]

## Findings

[What the evidence supports. Mark the strength of each: directly confirmed, inferred, or suggested
but not established. A finding stated at the wrong confidence is the way this kind of document does
damage.]

| Finding | Support | Confidence |
|---|---|---|

## Hypotheses

[Explanations still on the table, and what would confirm or eliminate each.]

## Rejected Hypotheses

[What was considered and ruled out, with the evidence that ruled it out. This is the section that
makes the report trustworthy — without it a reader cannot tell what was examined and dismissed from
what was never considered, and the next person re-runs the same dead ends.]

| Hypothesis | Ruled out by |
|---|---|

## Conclusion

[The answer to the question, at the confidence the evidence supports. "The evidence does not settle
this" is a valid conclusion and a far better one than a confident guess.]

## Unknowns

[What remains open, and what would resolve it.]

## Recommended Actions

[What to do about it, and how firm each recommendation is. Mark anything nobody has accepted yet as a
recommendation, not a plan.]

| Action | Rationale | Priority |
|---|---|---|

## Summary

[The question, the answer, the confidence, and what should happen next.]
