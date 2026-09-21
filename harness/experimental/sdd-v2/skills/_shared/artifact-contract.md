# artifact-contract

This contract defines which artifacts each phase reads, writes, and requires before it can proceed.

## Project-scope artifacts

| Artifact | Canonical path | Owner |
|---|---|---|
| project map | `.sdd/project-map.md` | `project-map-init` |
| skill registry | `.sdd/skill-registry.md` | `skill-registry` |
| project config | `openspec/config.yaml` | `sdd-init` |

## Change-scope artifacts

| Artifact | Canonical path |
|---|---|
| change state | `openspec/changes/{change-name}/state.yaml` |
| explore | `openspec/changes/{change-name}/explore.md` |
| proposal | `openspec/changes/{change-name}/proposal.md` |
| spec | `openspec/changes/{change-name}/spec.md` |
| design | `openspec/changes/{change-name}/design.md` |
| tasks | `openspec/changes/{change-name}/tasks.md` |
| apply progress | `openspec/changes/{change-name}/apply-progress.md` |
| verify report | `openspec/changes/{change-name}/verify-report.md` |
| archive report | `openspec/changes/archive/YYYY-MM-DD-{change-name}/archive-report.md` |

## Phase prerequisites and ownership

| Phase | Reads | Writes | Hard prerequisites | Notes |
|---|---|---|---|---|
| `project-map-init` | repo layout, project docs, executable config | `.sdd/project-map.md` | none | project-scope bootstrap helper |
| `skill-registry` | available skill paths, project-specific skill sources | `.sdd/skill-registry.md` | none | project-scope bootstrap helper |
| `sdd-init` | repo layout, docs, `project-map`, `skill-registry` | `openspec/config.yaml` | bootstrap invocation | owns project bootstrap summary and config |
| `sdd-explore` | `config.yaml`, `project-map`, `skill-registry`, existing `state.yaml` if present | `explore.md`, `state.yaml` | bootstrap completed or refreshed | first change phase |
| `sdd-propose` | `explore.md`, `config.yaml`, `state.yaml` | `proposal.md`, `state.yaml` | completed `sdd-explore` | proposal is always required before downstream formalization |
| `sdd-spec` | `proposal.md`, `explore.md`, `state.yaml` | `spec.md`, `state.yaml` | completed `sdd-propose` | may be merged with `sdd-propose` only by allowed shortcut |
| `sdd-design` | `proposal.md`, `explore.md`, `spec.md` when present, `state.yaml` | `design.md`, `state.yaml` | completed `sdd-propose` | may run after `sdd-spec` or in parallel once proposal exists |
| `sdd-tasks` | `proposal.md`, one or both of `spec.md` / `design.md`, `state.yaml` | `tasks.md`, `state.yaml` | completed `sdd-propose`; at least one of `spec.md` or `design.md` | for `planner`, this is the terminal phase |
| `sdd-apply` | `proposal.md`, `tasks.md`, available `spec.md`, available `design.md`, `state.yaml` | code changes, `apply-progress.md`, `tasks.md`, `state.yaml` | completed `sdd-tasks`; user approval before the current code-touching batch | batch-scoped execution; use `Suggested Batches` when available; block on dirty working tree; preserve batch traceability |
| `stage-qa` | changed code, `tasks.md`, `apply-progress.md`, `state.yaml` | `apply-progress.md`, `state.yaml` | relevant `sdd-apply` batch completed and user approved incremental QA | incremental validation layer, not final verify |
| `sdd-verify` | changed code, `proposal.md`, `tasks.md`, available `spec.md`, available `design.md`, `apply-progress.md`, `state.yaml` | `verify-report.md`, `state.yaml` | completed `sdd-apply` for implementation flows | mandatory when code changed; produces the compliance matrix, evidence-heavy verdict, and archive gate |
| `sdd-archive` | `verify-report.md`, full change folder, `state.yaml` | archive folder, `archive-report.md`, `state.yaml` | successful `sdd-verify`; required `closeout_review` decision resolved when the archive gate is not immediately ready | moves the full active change folder into the archive tree; not used for `planner`; may record optional `judgment-day` reference when relevant |

## Objective x mode minimum gate

This matrix defines the minimum artifact set before a phase can move into implementation or planned closure.

| Objective | `lite` | `standard` | `deep` |
|---|---|---|---|
| `new-feature` | `proposal + spec + tasks`; `design` optional | `proposal + spec + tasks`; `design` recommended by default | `proposal + spec + design + tasks` |
| `bug-fix` | `proposal + spec + tasks`; `design` optional if root cause and blast radius are clear | `proposal + spec + tasks`; `design` required when cause or impact is still unclear | `proposal + spec + design + tasks` |
| `planner` | `proposal + tasks + (spec or design)`; stop at `planned` | same minimum; the system should recommend both `spec` and `design` when the change is non-trivial | `proposal + spec + design + tasks`; stop at `planned` |
| `refactor-rework` | `proposal + design + tasks`; `spec` required when functional invariants must be preserved | `proposal + design + tasks`; `spec` strongly recommended when behavior preservation matters | `proposal + design + tasks`; `spec` required unless the change is proven internal-only |

## Shortcut policy

- `sdd-propose` and `sdd-spec` may merge only when complexity and risk are clearly low.
- `merged-shortcut` is never the default for `deep`.
- `sdd-design` may be omitted only where the matrix above allows it.
- `sdd-spec` and `sdd-design` may run in parallel only after `proposal.md` already exists.
- If code will change, `tasks.md` is mandatory.
- `planner` never pretends to be implemented or archived.

## Ownership guardrails

- Upstream artifacts are inputs, not rewrite targets, unless the owning phase is explicitly rerun.
- `proposal.md` is the gate into formal downstream work.
- `tasks.md` is the gate into execution.
- `tasks.md` keeps the visible task and batch board.
- `apply-progress.md` keeps the append-oriented execution ledger.
- `state.yaml` keeps operational phase state, checkpoints, and decisions.
- `verify-report.md` is the gate into archive and must carry the final verdict plus archive gate state.
- `archive-report.md` belongs only inside the archived copy and records closure traceability, not planning or verification semantics.
