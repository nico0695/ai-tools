---
id: adr
required: [context, decision, alternatives-considered, consequences]
optional: [risks, follow-ups]
closing: consequences
toc: disabled
---

<!-- One decision, its alternatives, and what accepting it costs. Short by design - an ADR that needs
     a table of contents is describing more than one decision. -->

# ADR-[NNNN]: [the decision, in a few words]

**Status:** [proposed | accepted | superseded by ADR-NNNN] · **Date:** [YYYY-MM-DD]

## Context

<!-- The situation that forced a choice: the constraint, the pressure, what was already true.
     Facts only - what made this a decision. The argument for the chosen option belongs in Decision. -->

## Decision

<!-- What was decided, in the present tense and as a commitment ("We use X"), followed by why it won.
     The why lives here, not in a separate section: a decision separated from its reason gets
     reversed by whoever finds only one of the two. -->

## Alternatives Considered

<!-- The options that were real, and what disqualified each one. An alternative listed without a
     reason for losing reads as a strawman. Include "do nothing" when it was genuinely on the table. -->

| Alternative | Why it was not chosen |
|---|---|

## Consequences

<!-- What accepting this costs and enables. This is the section that carries the value of an ADR and
     the one most often written as a list of benefits - a decision with no cost was not a decision.
     Split explicitly: what gets better, what gets worse, what is now harder to reverse.
     This is the closing section - no separate summary. -->

**Positive:**

**Negative:**

**Neutral / accepted trade-offs:**

<!-- OPTIONAL SECTIONS - copy the exact heading only when at least one confirmed fact fills it.

## Risks
     | Risk | Impact | Mitigation |
     What could make this decision wrong later, and what would signal it. Only real risks - a risk
     with no mitigation and no trigger is a worry.

## Follow-ups
     Work this decision creates: migrations, deprecations, docs to update, a date to revisit.
-->
