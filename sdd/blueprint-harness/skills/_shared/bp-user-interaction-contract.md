# bp-user-interaction-contract

## Root rule

Ask only when the answer changes scope, direction, risk, or approval. Never ask for facts recoverable from `config.yaml`, `state.yaml`, or digests.

## Checkpoint types

| Type | When | Behavior |
|---|---|---|
| `missing_context` | interview rubric finds a gap that blocks analysis | required |
| `scope_change` | the user's ask drifts from the recorded objective | required |
| `phase_validation` | closing interview / analysis / strategy | smart-skippable |
| `artifact_approval` | before a final artifact leaves `draft` | required |
| `handoff_gate` | before writing the sdd-lite seed | required |
| `audit_persist_offer` | closing a consultation | offer-once |
| `deep_interview_suggestion` | complexity rubric threshold met | offer-once |

## Shape

Short summary + one concrete question + 2–4 options + one marked recommended + free-form allowed.

## Rules

- **Smart skip:** if the user already answered or told the flow to proceed, skip the checkpoint and record it as implicitly approved (`response.implicit: true`). Never skip while ambiguity remains or any open risk is above `medium`.
- **Offer-once:** offers are made exactly once, never block progress, and the response is recorded as a decision. A resolved checkpoint is never re-asked.
- Every checkpoint and its resolution persist to `state.yaml` (`checkpoints[]`, `decisions[]`).
- **List selections** (multiple candidates): explicit action set `all / none / <indices> / inspect N / done`; `inspect N` answers from persisted digests and returns to the same checkpoint; unrecognized input restates the action set instead of being interpreted.
