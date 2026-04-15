# sddl-user-interaction-contract

This contract defines how `sdd-lite` asks the user for decisions without turning the workflow into a questionnaire.

## Core rules

- Ask only when the answer changes scope, risk, direction, quality, or the chosen execution path.
- Do not ask for facts already recoverable from `config.yaml`, `state.yaml`, bootstrap artifacts, maintained docs, or executable project files.
- Keep prompts short, contextual, and explicit about why the question matters.
- Persisted keys, artifact content, and structured decision records stay in English even when chat uses Spanish.

## Checkpoint types

| Type | When to use it | Required |
|---|---|---|
| `language_selection` | bootstrap cannot infer `es` or `en` confidently | conditional |
| `missing_context` | essential context cannot be recovered safely | conditional |
| `scope_change` | the requested work expands or redirects materially | conditional |
| `risk_review` | two viable paths have meaningful trade-offs | conditional |
| `stage_approval` | immediately before a code-touching execution stage | mandatory when code will change |
| `macro_plan_review` | the best lite path is to stop and write `macro-plan.md` first | conditional |
| `escalation_review` | the request no longer fits safe lite execution | conditional |
| `final_review` | final QA found warnings, blockers, or a closeout decision is still needed | conditional |

## Standard checkpoint shape

Each checkpoint should be representable with:

- a short summary
- a concrete question
- 2 to 4 options when options are useful
- one recommended option when the system has a justified preference
- free-form input allowed

## `stage_approval` minimum content

Each `stage_approval` checkpoint should include:

- stage id
- stage goal
- expected file or module scope
- whether the stage touches code
- the quick validation planned after the stage

Recommended options:

- approve this stage
- pause
- revise the plan first

## `macro_plan_review` minimum content

Each `macro_plan_review` checkpoint should include:

- why the request is too large for direct execution
- the expected output of `macro-plan.md`
- what work would remain after the macro plan

Recommended options:

- create the macro plan
- narrow the scope
- stop

## `escalation_review` minimum content

Each `escalation_review` checkpoint should include:

- why lite is no longer the safe path
- the recommended escalation target
- the unresolved risks or unknowns driving the escalation

Recommended options:

- escalate to `sdd-v2`
- narrow the request and stay in lite
- stop

## `final_review` minimum content

Each `final_review` checkpoint should include:

- the QA verdict
- remaining warnings or blockers
- the recommended next action

Recommended options:

- accept and close
- return for fixes
- hold for review

## Decision recording

`state.yaml` should record checkpoints under `checkpoints[]` with at least:

- `id`
- `type`
- `stage`
- `summary`
- `question`
- `options`
- `free_input_allowed`
- `created_at`
- `resolved_at`

`state.yaml` should record decisions under `decisions[]` with at least:

- `id`
- `checkpoint_id`
- `selected_option_id`
- `free_text`
- `rationale`
- `recorded_at`

## Result rules

- Use `blocked` when no safe next step exists without a decision.
- Use `partial` when useful work exists but the next safe move still depends on the user.
- The recommended next action must make the unblock path explicit.

## Avoided patterns

- asking the user to restate repository facts already in bootstrap
- requiring confirmation for obvious mechanical choices
- offering too many weak options when only one or two are defensible
