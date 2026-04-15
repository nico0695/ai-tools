# sddl-flow-contract

This contract defines the canonical ids, execution flow, lifecycle, and result shape for `sdd-lite`.

## Scope

Use this contract to keep all lite skills aligned on:

- canonical objective ids
- route ids
- stage ids
- lifecycle rules
- context loading order
- common result structure

## Canonical ids

### Objective ids

| Value | Meaning |
|---|---|
| `new-feature` | introduce or expand behavior |
| `bug-fix` | correct a defect with regression awareness |
| `planner` | formalize the work without implementing it |
| `refactor-rework` | restructure code while preserving behavior unless explicitly stated otherwise |

### Route ids

| Value | Meaning |
|---|---|
| `continue-lite` | the request fits the normal lite flow |
| `macro-plan-first` | the request is too large to execute directly and should stop after an approved macro plan |
| `escalate-to-sdd-v2` | the request exceeds lite safety or complexity limits |

### Stage ids

These ids are the canonical change-stage names used in state and contracts.

| Value | Meaning |
|---|---|
| `sddl-deep-explorer` | bounded deep analysis when shallow context is not enough |
| `sddl-proposal-spec` | compact functional framing and acceptance contract |
| `sddl-design-plan` | technical approach plus staged execution plan |
| `sddl-executor` | approved stage-by-stage execution |
| `sddl-qa-review` | stage review or final closeout |

### Stage status ids

- `pending`
- `in_progress`
- `completed`
- `blocked`
- `skipped`

### Lifecycle status ids

| Value | Meaning |
|---|---|
| `draft` | change record exists but formalization is incomplete |
| `planning` | the change is being formalized or re-scoped |
| `planned` | planning is complete and the flow intentionally stops before implementation |
| `implementing` | approved execution is active |
| `reviewing` | QA review is in progress or required |
| `completed` | final QA closeout succeeded |
| `blocked` | safe progress cannot continue |

## Context ladder

Recover context in this order unless a stage-specific contract requires a tighter order:

1. `./sdd-lite/openspec/config.yaml`
2. `./sdd-lite/openspec/changes/{change-name}/state.yaml`
3. `./sdd-lite/project-context.md`
4. `./sdd-lite/skill-catalog.md`
5. current change artifacts
6. maintained docs and executable project configuration
7. user clarification

Rules:

- persisted artifacts beat chat memory
- executable repo evidence beats older summaries
- the user should only be asked after the recoverable evidence is exhausted

## Common result structure

Every lite stage result must be representable with:

### Required fields

| Field | Notes |
|---|---|
| `status` | `success`, `partial`, or `blocked` |
| `executive_summary` | short stage outcome |
| `artifacts` | created, updated, or referenced artifact paths |
| `next_action` | the safest recommended next step |
| `open_risks` | still-active risks after the stage |

### Optional fields

| Field | Notes |
|---|---|
| `decision_required` | true when the next safe step depends on the user |
| `decision_options` | structured options for the pending decision |
| `evidence` | commands, files, or observations backing the result |
| `errors` | structured blocking issues or validation failures |

## Flow rules

- `sddl-init` is bootstrap-only and does not create change-scoped artifacts.
- `sddl-proposal-spec` is the first canonical change stage and should initialize `state.yaml` when the change starts.
- `sddl-design-plan` requires `proposal-spec.md` and defines the executable stage plan.
- `planner` stops after `sddl-design-plan` and leaves `lifecycle_status: planned`.
- `sddl-executor` must not start a code-touching stage without an explicit recorded approval.
- `sddl-deep-explorer` is read-only and on-demand.
- `sddl-qa-review` in `stage` mode never marks the change `completed`.
- `sddl-qa-review` in `final` mode is the only lite path that may set `lifecycle_status: completed`.
- `macro-plan.md` exists only on the `macro-plan-first` route and only after explicit approval.
- `escalate-to-sdd-v2` should preserve lite state and recommendations without pretending the work is still safely executable in lite.

## Resume rules

- `state.yaml` is the operational resume anchor.
- `proposal-spec.md`, `design-plan.md`, `execution-log.md`, and `qa-report.md` hold the semantic detail for their owning stages.
- Resume should rebuild the next safe move from persisted files, not from chat memory.
