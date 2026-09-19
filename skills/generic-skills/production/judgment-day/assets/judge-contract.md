<!-- Orchestrator: append this file to every judge prompt, starting at the heading below. A judge
     that does not receive it cannot assign severity, evidence_class or causal_disposition, because
     nothing else in its context defines them. This comment is the only part you leave out. -->

## Severity

| Value | Meaning |
|---|---|
| `BLOCKER` | must not ship / must not be acted on: an incident, data loss, data exposure, or a decision reversed at real cost is the likely outcome |
| `CRITICAL` | severe defect with a concrete failure path, or a claim that would mislead someone acting on this document |
| `WARNING` | real weakness, tolerable in the short term |
| `SUGGESTION` | improvement opportunity, not a defect |

`BLOCKER` and `CRITICAL` are the severe values — only they can be confirmed, become a suspect, or be
escalated as a contradiction. `WARNING` and `SUGGESTION` are always `info`: reported once, never
blocking, never adjudicated.

## Evidence class

| Value | Meaning |
|---|---|
| `deterministic` | the defect is visible in the target as written — the path, the value, or the missing guard is there to point at |
| `inferential` | the defect depends on a chain of reasoning about runtime, callers, or data you did not read |

Record this honestly. Convergence — not a refuter pass — is this protocol's corroboration mechanism: an
inferential finding one judge invents and the other does not becomes a suspect, never confirmed.

## Causal disposition

| Value | Meaning |
|---|---|
| `introduced` | this change (or, in artifact mode, this document) created the defect |
| `behavior-activated` | the defect existed but was unreachable; this change put it on a live path |
| `worsened` | the defect existed and this change made it more likely or more damaging |
| `pre-existing` | the defect is inside the target, and this change neither created nor touched it |
| `unknown` | you cannot tell from the review reference alone |

Only the first three can block. In `artifact` mode, `causal_disposition` is `introduced` unless the
defect demonstrably comes from a source the document cites — then it is `pre-existing`.

## Round-one assessment contract

For a round-one prompt, return at least one assessment for each criterion in the supplied criteria
block; a criterion may have several, one per location you assessed. Use `not_assessed` when the
criterion does not apply or the target does not provide enough evidence. A `correct` assessment must
name the concrete location you verified (`path:line`, `path:start-end`, or a section anchor), never a
whole file or the whole target: only a located `correct` can contradict another reviewer's claim.

```yaml
assessments:
  - criterion: correctness
    location: "path/to/file.ext:42"      # or an artifact section anchor
    status: correct | broken | not_assessed
    claim: "one-sentence reason for the status"
    proof_refs: ["concrete proof: file:line, command output, spec section"]
```

`correct` is an explicit statement that the behavior at that location is sound; `broken` identifies a
defect and should normally have a matching finding; `not_assessed` is not approval.

## Findings contract

Return this findings shape for round-one prompts. Never assign ids or statuses — the orchestrator does
that when merging.

```yaml
findings:
  - location: "path/to/file.ext:42"      # code mode: path:line or path:start-end
                                          # artifact mode: a section anchor, e.g. design.md#risks
    severity: BLOCKER | CRITICAL | WARNING | SUGGESTION
    claim: "observable incorrect behavior, one sentence"
    evidence_class: deterministic | inferential
    causal_disposition: introduced | behavior-activated | worsened | pre-existing | unknown
    proof_refs: ["concrete proof: file:line, command output, spec section"]
evidence: ["what you inspected"]
```

For round-one prompts, return both `assessments` and `findings` (the findings list may be empty), plus
`evidence`. Scoped re-judgment prompts use the `results` shape defined in `references/judge-prompts.md`
and do not require round-one assessments.

## Precision gate

Report a finding only if it is a real, defensible defect; when in doubt, downgrade it to
`WARNING`/`SUGGESTION` or stay silent. Style and preference findings are banned unless they obscure a
defect. In `code` mode the standard is the surrounding code, never your own taste; in `artifact` mode
the standard is whether the gap would mislead or block a reader acting on the document, never a
phrasing preference.

## Worker boundary

You are a read-only reviewer. Do NOT edit anything, run state-changing commands, launch sub-agents, or
widen scope beyond the review reference. Run one exhaustive sweep, return the output the active prompt requires, and stop. If
the target is clean, return an empty findings list plus evidence of what you inspected.
