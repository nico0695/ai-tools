# user-interaction-contract

This contract defines how SDD v2 asks the user for decisions without turning the flow into a questionnaire.

## Interaction rules

- Ask only when the answer changes scope, risk, direction, or closure behavior.
- Do not ask for information already available in bootstrap, config, state, or project docs.
- Keep user-facing messages short and contextual.
- Internal storage keys stay in English even when the conversation is in Spanish.

## Checkpoint types

| Type | When to use it | Required |
|---|---|---|
| `language_selection` | bootstrap cannot infer `es` or `en` confidently | conditional |
| `missing_context` | essential context cannot be recovered from artifacts or docs | conditional |
| `shortcut_confirmation` | a non-trivial merge or skip is proposed | conditional |
| `scope_change` | a phase discovers a meaningful expansion or redirection | conditional |
| `risk_review` | two viable options have different trade-offs | conditional |
| `pre_apply` | immediately before each code-touching `sdd-apply` batch executes | mandatory |
| `incremental_qa` | before running `stage-qa` for a relevant code-touching batch | conditional |
| `closeout_review` | `sdd-verify` returned `pass_with_warnings`, or verify passed but review-worthy observations still matter before archive | conditional |

## Standard checkpoint shape

Each checkpoint should be representable with:
- a short summary
- a concrete question
- 2 to 4 options when options are appropriate
- one recommended option when the system has a justified preference
- free-form input allowed

## `pre_apply` minimum content

Each `pre_apply` checkpoint should include:
- batch id
- included task ids
- batch goal
- expected file or module scope
- whether the batch touches code
- the validation note planned for that batch
- snapshot policy summary
- dirty working tree result when already known

Recommended options:
- approve this batch
- pause
- replan or revise tasks

## `incremental_qa` minimum content

Each `incremental_qa` checkpoint should include:
- batch id
- changed scope
- why incremental QA is being recommended now
- the planned checks
- whether the alternative is defer or stop-and-fix

Recommended options:
- run incremental QA now
- defer and continue
- stop and revise before more execution

## `closeout_review` minimum content

Each `closeout_review` checkpoint should include:
- verify verdict
- remaining warnings or open issues
- archive gate state
- the recommended next step

Recommended options:
- accept and proceed to archive
- hold for further review
- return for fixes

## `decision_options` shape

When a phase needs a structured decision, each option should include:
- `id`
- `label`
- `description`
- `recommended`

The recommended option must be justified in the surrounding summary, not only flagged.

## State recording

`state.yaml` should record checkpoints under `checkpoints[]` with at least:
- `id`
- `type`
- `phase`
- `summary`
- `options`
- `free_input_allowed`
- `response`
- `created_at`
- `resolved_at`

`state.yaml` should record decisions under `decisions[]` with at least:
- `id`
- `checkpoint_id`
- `selected_option_id`
- `free_text`
- `rationale`
- `recorded_at`

## Envelope interaction rules

- If a phase sets `decision_required: true`, it must also provide `decision_options`.
- Use `status: blocked` when no safe path exists without a decision.
- Use `status: partial` when useful progress exists but a decision still gates the next step.
- The next recommended action should make the unblock path explicit.

## Avoided patterns

- asking the user to restate repo facts already present in bootstrap
- requesting confirmation for obvious mechanical choices
- presenting too many options when only one or two are defensible
