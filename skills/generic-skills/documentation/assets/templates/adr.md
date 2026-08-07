---
template:
  id: adr
  name: Architecture Decision Record
  description: Records one decision - its context, the alternatives, the reasoning, and what accepting it costs. Short by design.
  audience: [developers, architects, future maintainers]
  use_when:
    - a choice was made that someone will later ask "why" about
    - two viable options were weighed and one won
    - a decision constrains future work
  required: [status, context, decision, alternatives, consequences]
  optional: [rationale, risks, follow-ups]
  visuals: [rarely - only if the decision is structural]
  toc: disabled
---

# ADR-[NNNN]: [Decision in one line]

| | |
|---|---|
| **Status** | Proposed / Accepted / Superseded by ADR-NNNN / Deprecated |
| **Date** | YYYY-MM-DD |
| **Deciders** | [who] |

## Context

[The forces that made a decision necessary: the problem, the constraints, what was already true, what
breaks if nothing changes. Written so a reader in two years understands the pressure without having
been there. State facts, not the preferred conclusion — the argument belongs in Rationale.]

## Decision

[What was decided, stated as a commitment, in present tense. One decision per record — a record
covering three is three records.]

## Alternatives Considered

### [Alternative]

**What it was:** [the option]

**Why not:** [the specific reason it lost, tied to the context above]

[Repeat. An ADR whose alternatives are obviously bad documents nothing — if the real competitor is
missing, add it. If there was genuinely no alternative, say that instead of inventing straw options.]

## Rationale

[Why the chosen option beats the others given these constraints. The reasoning a reader needs to
judge whether the decision still holds when the constraints change.]

## Consequences

[What follows from accepting this — both directions. The favorable half is easy and the costly half
is what makes the record worth keeping; a decision with no cost was not a decision.]

**Positive**
- [what gets better]

**Negative**
- [what gets worse, what is now harder, what is locked in]

**Neutral**
- [what changes without being better or worse]

## Risks

| Risk | Impact | Mitigation |
|---|---|---|

## Follow-ups

- [ ] [work this decision creates]
