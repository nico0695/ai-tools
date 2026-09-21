# persistence-contract

This contract defines where persistent data lives, who owns it, and how state changes are recorded.

## Persistence modes

| Value | Meaning | MVP support |
|---|---|---|
| `openspec` | versioned repo-local persistence | active and required |
| `hybrid` | repo artifacts plus auxiliary memory layer | reserved, not MVP-operational |
| `none` | disposable no-persistence flow | reserved, not MVP-operational |

The MVP must behave as if `openspec` is the only production-ready mode.

## Canonical paths

### Project scope

| Path | Role | Owner |
|---|---|---|
| `.sdd/project-map.md` | durable project map | `project-map-init` |
| `.sdd/skill-registry.md` | durable skill registry | `skill-registry` |
| `openspec/config.yaml` | project-level SDD config | `sdd-init` |

### Change scope

| Path | Role | Owner |
|---|---|---|
| `openspec/changes/{change-name}/state.yaml` | operational change state | orchestrator + active phase |
| `openspec/changes/{change-name}/explore.md` | discovery output | `sdd-explore` |
| `openspec/changes/{change-name}/proposal.md` | change proposal | `sdd-propose` |
| `openspec/changes/{change-name}/spec.md` | expected behavior | `sdd-spec` |
| `openspec/changes/{change-name}/design.md` | technical approach | `sdd-design` |
| `openspec/changes/{change-name}/tasks.md` | executable plan | `sdd-tasks` |
| `openspec/changes/{change-name}/apply-progress.md` | execution trace | `sdd-apply` and `stage-qa` |
| `openspec/changes/{change-name}/verify-report.md` | final evidence and verdict | `sdd-verify` |

### Archive scope

| Path | Role | Owner |
|---|---|---|
| `openspec/changes/archive/YYYY-MM-DD-{change-name}/` | archived change folder | `sdd-archive` |
| `openspec/changes/archive/YYYY-MM-DD-{change-name}/archive-report.md` | closure report | `sdd-archive` |

## `config.yaml` minimum shape

`openspec/config.yaml` is project-scoped and should persist:
- project identity
- detected stack and package manager
- canonical SDD paths
- persistence mode
- bootstrap metadata
- quality commands
- user language and preferred mode

Only `sdd-init` should own normal writes to this file unless the user explicitly approves a maintenance change.

## `state.yaml` minimum shape

`state.yaml` is change-scoped and should persist:
- `change_name`
- `objective`
- `mode`
- `lifecycle_status`
- `current_phase`
- per-phase status
- artifact paths
- checkpoints and decisions
- approved shortcuts
- active risks
- verification evidence summary
- next recommended phase

`state.yaml` is operational memory, not a chat transcript.

Batch-level execution history does not belong in `state.yaml`.

Use this split:
- `tasks.md` for visible task and batch status
- `apply-progress.md` for the execution ledger and batch evidence
- `state.yaml` for lifecycle, checkpoints, decisions, open risks, and next-step routing

## Lifecycle status model

| Value | Meaning |
|---|---|
| `draft` | change folder exists but formalization is not established yet |
| `planning` | the change is being explored or formalized |
| `planned` | planning is complete and the flow intentionally stops before apply |
| `implementing` | approved implementation is in progress |
| `verifying` | final verification is running or required |
| `verified` | final verification returned `pass` and the change is ready to archive |
| `verified_pending_archive` | final verification returned `pass_with_warnings`, or closure is intentionally held for review before archive |
| `archived` | archival closure completed |
| `blocked` | progress is halted by a meaningful blocker, including failed final verification |

## Per-phase status model

Each phase entry in `state.yaml` must use one of:
- `pending`
- `in_progress`
- `completed`
- `blocked`
- `skipped`

## Write rules

- Project-scope artifacts must not be rewritten by change phases.
- A phase can update `state.yaml` before and after meaningful work.
- A phase owns its primary artifact and may refresh it on rerun.
- Downstream phases may reference upstream artifacts but must not silently rewrite them.
- `sdd-apply` should not store a per-batch ledger as custom top-level state fields in the MVP.
- Dirty-tree blockers and pre-apply approvals should be persisted through `checkpoints[]`, `decisions[]`, phase status, and `next_recommended_phase`.
- Clean-tree baseline metadata may be recorded in `apply-progress.md` instead of dedicated snapshot fields in `state.yaml`.
- `closeout_review` outcomes should be persisted through `checkpoints[]`, `decisions[]`, lifecycle status, and `next_recommended_phase`.
- `verified_pending_archive` must keep the active change folder in place.
- `sdd-archive` is the only phase allowed to move a change into `openspec/changes/archive/`.
- `sdd-archive` should move the full active change folder as one archived unit rather than creating a partial archive copy.
- `archive-report.md` should be created only inside the archived destination.

## Session-only data

The following are session-scoped and should not be persisted as separate repo files in the MVP:
- compact rules cache
- mini operational memory snapshots
- transient tool call outputs

They may appear in envelope results or orchestrator memory, but durable truth still belongs in the canonical project and change files.
