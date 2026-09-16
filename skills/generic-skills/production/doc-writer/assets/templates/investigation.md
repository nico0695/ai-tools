---
id: investigation
required: [question, evidence, findings, rejected-hypotheses, conclusion]
optional: [context, unknowns, recommended-actions]
closing: conclusion
toc: auto
---

<!-- A question that was answered with evidence: a debug session, a spike, an audit, a root-cause
     analysis. The document has to let someone else re-check the reasoning, not just read the answer. -->

# Investigation: [the question, in a few words]

> [One line: what was asked and what was concluded.]

## Table of Contents

<!-- Only when the finished document has 5 or more `##` sections. -->

## Question

<!-- The question as it was actually asked, and why it mattered. One paragraph.
     A question that cannot be answered yes/no/with-a-value is two questions. -->

## Evidence

<!-- What was observed and where it came from. Logs, code, metrics, reproductions, commits.
     Every item carries its location so a reader can go look. Observation is not interpretation:
     what the log said belongs here, what it means belongs in Findings. -->

| What was observed | Source |
|---|---|

## Findings

<!-- What the evidence supports, one finding per item, each tied to the evidence above.
     The confidence column is not decoration - it is how a reader knows what to trust. -->

| Finding | Evidence | Confidence |
|---|---|---|

<!-- Confidence: confirmed (a source states it) / inferred (follows from evidence) / suspected
     (consistent with evidence, not established). Never leave the column blank. -->

## Rejected Hypotheses

<!-- What was considered and ruled out, and what ruled it out. This is the section that makes an
     investigation auditable: without it a reader cannot tell what was examined and dismissed from
     what was never considered. If nothing was rejected, say that the search was narrow. -->

| Hypothesis | Ruled out by |
|---|---|

## Conclusion

<!-- The answer to the Question, in the terms the Question was asked. Say plainly whether it is
     settled or partial. This is the closing section - no separate summary. -->

<!-- OPTIONAL SECTIONS - copy the exact heading only when at least one confirmed fact fills it.

## Context
     What was happening that made the question urgent: the incident, the symptom, the deadline.
     Include it when a reader six months out would not know why anyone was looking.

## Unknowns
     What stayed open, and what would settle it. An unknown with no way to close it is a risk, and
     should say so.

## Recommended Actions
     What to do about it. Separate what follows from the findings from what is an opinion, and mark
     which recommendations nobody has accepted yet.
-->
