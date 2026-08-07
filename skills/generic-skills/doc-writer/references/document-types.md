# Document Types

Read this in Phase 4, before listing `assets/templates/`. It answers "which document does this
situation call for", which is upstream of "which file do I fill in".

Contents:
- [Choosing by intent](#choosing-by-intent)
- [Disambiguation](#disambiguation)
- [The catalog](#the-catalog)
- [When nothing fits](#when-nothing-fits)

## Choosing by intent

The type follows from what the reader needs to do afterwards, not from what the material is about.
The same subsystem can legitimately produce five different documents.

| The reader needs to... | Type |
|---|---|
| understand how the system is put together | `architecture` |
| get oriented on a project or service overall | `technical-overview` |
| understand or change one capability | `feature` |
| call an interface correctly | `api` |
| know why a choice was made, and what it cost | `adr` |
| execute or recover an operation under pressure | `runbook` |
| know what was found and what it means | `investigation` |
| see what was done, where it stands, what is left | `project-report` |
| none of the above cleanly | `generic` |

If two types both fit, the material is probably two documents. Say so — one focused document plus a
link beats one document that serves neither reader.

## Disambiguation

The pairs that get confused, and the question that separates them:

**architecture vs technical-overview** — does the reader need the *structure* (boundaries,
components, how they interact) or the *orientation* (what this is, what it does, how to work on it)?
Overview answers "what am I looking at"; architecture answers "how does it fit together". Onboarding
usually wants overview; a change to a boundary wants architecture.

**feature vs api** — is the subject the *behavior* (what it does, for whom, under which rules) or the
*contract* (how to call it, what comes back, what fails)? A feature doc explains the checkout flow;
an API doc lets someone call `POST /orders` without reading it.

**adr vs investigation** — was a decision *made*, or was a question *answered*? An ADR records a
commitment and its consequences. An investigation records evidence and findings, and may end with a
recommendation nobody has accepted yet. Research that ended in a decision is often both: the
investigation is the evidence, the ADR is the commitment.

**runbook vs feature** — is the reader *operating* it or *changing* it? Runbooks are written for
someone under time pressure who needs the next command, not the design rationale.

**project-report vs technical-overview** — is the subject the *work* or the *system*? A report is
bounded in time (a sprint, a migration, a project) and goes stale by design. An overview describes a
current state and is maintained.

## The catalog

Each entry gives the section skeleton the type expects. The template file in `assets/templates/`
carries the fillable form; this is the shape to check a plan against.

### `generic`
Free-form technical document with a solid backbone. Use when the material is genuinely
type-agnostic, or as the base when a proposed type would leave most sections empty.

```
Overview / Purpose · Context · [content sections] · Open questions · References · Summary
```

### `technical-overview`
Orients someone on a project, service or subsystem: what it is, what it does, how it is built, how
to work on it.

```
Overview · Purpose and scope · Key concepts · Architecture at a glance · Main components ·
How it runs · Configuration · Development workflow · Limitations · Summary
```

### `architecture`
Structure, boundaries, components, interactions. The type most likely to need a diagram, and the
one where an invented relationship does the most damage.

```
Overview · System context · Architecture · Components and responsibilities · Main flows ·
Data model · External integrations · Deployment · Cross-cutting concerns · Constraints ·
Known limitations · Summary
```

### `feature`
One capability: the problem, the behavior, the edges, the impact on the rest of the system.

```
Overview · Problem · Goals · Non-goals · Behavior · Flow · Architecture impact ·
Data · Interfaces · Edge cases · Errors · Configuration · Testing · Limitations · Summary
```

### `api`
A contract someone calls. Every endpoint needs a real example; a schema without one gets the shape
right and the semantics wrong.

```
Overview · Base information · Authentication · Endpoints (request / response / errors per
endpoint) · Errors · Pagination · Rate limits · Versioning · Summary
```

### `adr`
One decision, its alternatives, and what accepting it costs. Short by design — an ADR that needs a
table of contents is describing more than one decision.

```
Status (header) · Context · Decision · Alternatives considered · Rationale · Consequences ·
Risks · Follow-ups
```

The section that carries the value is **Consequences**, and it is the one most often written as a
list of benefits. A decision with no cost was not a decision.

### `runbook`
Executed under pressure. Ordered, unambiguous steps, exact commands, an explicit verification, and a
rollback that exists before it is needed.

```
Purpose · Prerequisites · Quick reference · Procedure · Verification · Rollback ·
Troubleshooting · Escalation
```

Never write a runbook step from inference. An unverified command in a runbook gets run at 3am.

### `investigation`
A question, the evidence, and what it supports. The section that makes it trustworthy is **Rejected
hypotheses** — without it a reader cannot tell what was examined and dismissed from what was never
considered.

```
Question · Context · Evidence · Observations · Findings · Hypotheses · Rejected hypotheses ·
Conclusion · Unknowns · Recommended actions · Summary
```

### `project-report`
Consolidates work over a period: what changed, what was decided, where it stands, what is left.
Include the problems encountered — a report where everything went smoothly is not a report.

```
Executive summary · Scope · Timeline · Major changes · Architecture changes · Features ·
Technical decisions · Problems encountered · Testing and validation · Current state ·
Technical debt · Open work · Summary
```

## When nothing fits

Use `generic` and shape it from the context map's goal and audience rather than forcing a type that
half-applies. Then say so in the plan: a document type that had to be forced is a signal the catalog
is missing one, and a new template in `assets/templates/` is the fix — it is picked up automatically,
with no change to `SKILL.md` or to this file.
