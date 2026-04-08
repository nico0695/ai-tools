# sdd-phase-common

This contract is canonical for every SDD v2 phase skill.

## Scope

Use this document to keep phase outputs, state transitions, and read/write behavior consistent across the system.

This contract governs:
- shared ids
- context loading order
- the common envelope
- status semantics
- skill resolution values
- write discipline

## Canonical ids

### Objective ids

| Value | Meaning |
|---|---|
| `new-feature` | new behavior or functional expansion |
| `bug-fix` | defect correction with cause and regression awareness |
| `planner` | formalize the change without implementing it |
| `refactor-rework` | structural improvement while preserving integrity |

### Mode ids

| Value | Meaning |
|---|---|
| `lite` | low-risk, narrow-scope work |
| `standard` | default productive mode |
| `deep` | higher-risk or higher-uncertainty work |

### Phase ids

These ids are the canonical phase names used across contracts, state, and schemas.

| Value | Meaning |
|---|---|
| `sdd-explore` | discovery and affected-area analysis |
| `sdd-propose` | change proposal and trade-offs |
| `sdd-spec` | expected behavior and acceptance criteria |
| `sdd-design` | technical design and implementation risk |
| `sdd-tasks` | executable task breakdown |
| `sdd-apply` | controlled implementation |
| `stage-qa` | incremental technical validation |
| `sdd-verify` | final verification |
| `sdd-archive` | archival closure |

### Resolution ids

`skill_resolution.mode` must use one of these values:

| Value | Meaning |
|---|---|
| `exact-skill` | the canonical skill handled the phase directly |
| `merged-shortcut` | the phase was intentionally merged with another allowed phase |
| `inline` | the orchestrator handled a narrow step without delegation |
| `delegated` | work ran through a delegated worker or host wrapper |
| `resumed` | work continued from persisted state |
| `bootstrap-required` | the phase could not proceed until bootstrap was completed or refreshed |

## Context ladder

Every phase should recover context in this order unless a phase-specific contract says otherwise:

1. `openspec/config.yaml`
2. `openspec/changes/{change-name}/state.yaml`
3. `.sdd/project-map.md`
4. `.sdd/skill-registry.md`
5. current change artifacts
6. project docs and executable project config
7. user clarification

Rules:
- persisted artifacts win over chat memory
- project-specific evidence wins over generic assumptions
- phases should not skip directly to the user if the answer can be recovered from the ladder

## Common envelope

Every phase result must be representable with this envelope.

### Required fields

| Field | Type | Notes |
|---|---|---|
| `status` | enum | `success`, `partial`, or `blocked` |
| `executive_summary` | string | short result summary |
| `artifacts` | array | changed or referenced artifact ids/paths |
| `next_recommended` | object | next phase or next action |
| `risks` | array | active risks after the phase completes |
| `skill_resolution` | object | how the system resolved the phase execution |

### Optional fields

| Field | Type | Notes |
|---|---|---|
| `decision_required` | boolean | true when the next safe step depends on a user decision |
| `decision_options` | array | options to unblock a decision checkpoint |
| `evidence` | array | commands, files, or observations backing the result |
| `errors` | array | structured failures or validation issues |

## Status semantics

### `success`

Use `success` when the current phase achieved its intended output for the current scope.

Examples:
- `sdd-spec` produced an acceptable `spec.md`
- `sdd-verify` completed and produced a verdict, archive gate, and evidence
- `sdd-archive` completed and produced an archived folder plus closure report

### `partial`

Use `partial` when useful work was completed but the phase did not fully close.

Typical cases:
- a phase created a draft that still needs confirmation
- a phase advanced safely but the next step depends on a pending decision
- a phase updated artifacts but left known follow-up work

`partial` may still recommend advancing, but only when the remaining gap is explicit and controlled.

### `blocked`

Use `blocked` when the phase cannot move forward safely.

Typical cases:
- missing bootstrap or stale bootstrap
- missing prerequisite artifact
- unresolved user decision with meaningful trade-offs
- tool failure or validation failure that prevents reliable progress

If `status` is `blocked`, at least one of these must be true:
- `decision_required` is `true`
- `errors` is non-empty

## Decision and evidence rules

- If `decision_required` is `true`, the envelope must include `decision_options`.
- The recommended option should be marked with `recommended: true`.
- Free-form user input is always allowed even when options are provided.
- `evidence` is mandatory for `sdd-verify`.
- `evidence` is recommended for `stage-qa` and for `sdd-apply` when commands were run or notable code checks occurred.
- `sdd-verify` should leave a stable verdict model in its primary artifact: `pass`, `pass_with_warnings`, or `fail`.
- `sdd-archive` should leave evidence for the source path, destination path, and any gating decision that allowed closure.
- When `stage-qa` runs, evidence should make the checked batch, the checks run, and the resulting continuation recommendation easy to recover from `apply-progress.md`.
- When `sdd-apply` recommends or hands off to `stage-qa`, the current batch entry should keep the checkpoint and decision references needed for resume.
- `errors` should use short stable codes where possible and explain whether retry is safe.

## Write discipline

- A phase must read its prerequisite artifacts before generating replacements.
- A phase may own and rewrite its own artifact, but it must not silently rewrite upstream approved artifacts owned by another phase.
- Operational truth belongs in `state.yaml`.
- Semantic change content belongs in the phase artifact `.md` files.
- Project-wide durable context belongs in `config.yaml`, `.sdd/project-map.md`, and `.sdd/skill-registry.md`.
- The chat transcript is never the canonical source of truth.

## Flow-specific rules

- `planner` stops after `sdd-tasks` and sets lifecycle state to `planned`.
- `planner` never runs `sdd-apply`, `sdd-verify`, or `sdd-archive`.
- `sdd-verify` may transition the change to `verified` on `pass`, `verified_pending_archive` on `pass_with_warnings`, or `blocked` on `fail`.
- `sdd-archive` only runs after a successful verification result and any required `closeout_review` decision.
- `sdd-archive` moves the full active change folder into the canonical archive tree and creates `archive-report.md` only inside that archived copy.
- `judgment-day` may be suggested before archive for unusually sensitive changes, but it is optional unless another explicit policy says otherwise.
- `verified_pending_archive` is a valid stable state when the user wants to review before closure.
