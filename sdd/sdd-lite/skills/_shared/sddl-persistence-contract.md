# sddl-persistence-contract

This contract defines where `sdd-lite` stores durable data, who owns each artifact, and how writes stay contained.

## Canonical runtime layout

```text
./sdd-lite/
  project-context.md
  skill-catalog.md
  openspec/
    config.yaml
    changes/
      {change-name}/
        state.yaml
        proposal-spec.md
        design-plan.md
        execution-log.md
        qa-report.md
        macro-plan.md            # only when explicitly approved
```

No persisted lite artifact should be written outside `./sdd-lite/`.

## `change-name` rule

`change-name` must use lowercase kebab-case:

```text
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Rules:

- no spaces
- no slashes
- no dates in the active change name
- the active path is always `./sdd-lite/openspec/changes/{change-name}/`

## Project-scope artifacts

| Artifact | Canonical path | Owner |
|---|---|---|
| project context | `./sdd-lite/project-context.md` | `sddl-init` |
| skill catalog | `./sdd-lite/skill-catalog.md` | `sddl-init` internal helper |
| project config | `./sdd-lite/openspec/config.yaml` | `sddl-init` |

## Change-scope artifacts

| Artifact | Canonical path | Owner |
|---|---|---|
| change state | `./sdd-lite/openspec/changes/{change-name}/state.yaml` | orchestrator plus active stage |
| proposal and spec | `./sdd-lite/openspec/changes/{change-name}/proposal-spec.md` | `sddl-proposal-spec` |
| design and stage plan | `./sdd-lite/openspec/changes/{change-name}/design-plan.md` | `sddl-design-plan` |
| execution ledger | `./sdd-lite/openspec/changes/{change-name}/execution-log.md` | `sddl-executor` |
| QA report | `./sdd-lite/openspec/changes/{change-name}/qa-report.md` | `sddl-qa-review` |
| macro plan | `./sdd-lite/openspec/changes/{change-name}/macro-plan.md` | `sddl-design-plan` on approved macro-plan-first flows |

## Ownership rules

- Project-scope bootstrap artifacts must not be silently rewritten by change stages.
- Each stage may rewrite its own primary artifact on rerun.
- Downstream stages may reference upstream artifacts but must not silently redefine approved scope or decisions.
- `state.yaml` may be updated before and after meaningful stage work.
- `sddl-deep-explorer` is read-only unless a future contract explicitly says otherwise.

## Artifact responsibility split

Use this split consistently:

- `project-context.md` for reusable repository context
- `skill-catalog.md` for canonical lite skills, support agents, and reusable references
- `config.yaml` for project identity, canonical paths, bootstrap metadata, and quality commands
- `proposal-spec.md` for problem framing, scope, expected behavior, acceptance targets, and open questions
- `design-plan.md` for technical approach, staged execution, validation plan, and planning status
- `execution-log.md` for stage-by-stage execution trace
- `qa-report.md` for stage review findings or final closeout findings
- `state.yaml` for lifecycle, resume, checkpoints, decisions, escalation route, and next action

`state.yaml` is operational memory, not a chat transcript and not a substitute for the stage artifacts.

## Lite persistence rules

- `macro-plan.md` must not exist unless the route is `macro-plan-first` and the user approved that path.
- `sdd-lite` does not define archive persistence in the MVP.
- `sddl-qa-review` in `final` mode is the closeout point; there is no archive phase after it.
- If the safest path is `escalate-to-sdd-v2`, the lite change state should record that route and stop claiming lite completion.
