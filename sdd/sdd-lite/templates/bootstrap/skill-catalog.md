# Skill Catalog

## Metadata

- generated_at:
- generated_by: sddl-init internal helper
- runtime_root: ./sdd-lite

## Canonical Lite Skills

| Skill Id | Responsibility | Writes | Notes |
|---|---|---|---|
| sddl-init | Bootstrap project context and runtime configuration | `./sdd-lite/project-context.md`, `./sdd-lite/skill-catalog.md`, `./sdd-lite/openspec/config.yaml` | Generates the skill catalog through an internal helper. |
| sddl-proposal-spec | Produce the compact functional change artifact | `./sdd-lite/openspec/changes/{change-name}/proposal-spec.md` | Canonical lite formalization entry point. |
| sddl-design-plan | Produce the technical design and staged execution plan | `./sdd-lite/openspec/changes/{change-name}/design-plan.md` | `planner` ends here. |
| sddl-executor | Execute one approved stage at a time | `./sdd-lite/openspec/changes/{change-name}/execution-log.md` | Stops on contradiction, drift, or blast-radius expansion. |
| sddl-deep-explorer | Run bounded deep analysis when the lite flow needs more evidence | none by default | On-demand support skill. |
| sddl-qa-review | Review stage outcomes and final closure | `./sdd-lite/openspec/changes/{change-name}/qa-report.md` | Final mode is the lite closeout. |

## Support Agents

These are logical support agents for `sdd-lite`.
They are not separate persisted skills.

| Agent Id | Role | Base Pattern | Reuse Note |
|---|---|---|---|
| sddl-context-agent | Bounded repository analysis | `agents/agents-generic/deep-context-analyzer.agent.md` | Reusable when deeper evidence is needed without widening scope. |
| sddl-planning-agent | Planning support for `sddl-design-plan` | `agents/agents-generic/strategic-planner.agent.md` | Reusable for turning approved analysis into an execution plan. |
| sddl-review-agent | Review support for `sddl-qa-review` | `agents/agents-generic/pr-code-reviewer.agent.md` | Reusable for structured findings-first review output. |

## Operating Notes

- All persisted artifacts remain in English.
- Chat interaction may be Spanish or English, but artifact language does not change.
- `macro-plan.md` exists only when explicitly needed and approved.
