# skill-registry

You generate the canonical skill registry for SDD v2 and derive compact rules for the current session.

## Goal

Produce or refresh `.sdd/skill-registry.md` so the orchestrator can discover canonical SDD skills and a compact set of project rules without re-reading everything.

The registry is durable.
The compact rules are session-scoped and should not be persisted as a second file in the MVP.

## When to use

Use this skill during `sdd-init` when:
- bootstrap is missing
- bootstrap refresh is recommended
- the user explicitly asks for refresh
- skill resolution failed in a previous run

## Reads

Read:
- canonical SDD v2 skills under `sdd/sdd-v2/skills/`
- `_shared` contracts relevant to skill routing
- repo-local custom skills when they clearly exist inside the project
- existing `.sdd/skill-registry.md` if present
- `openspec/config.yaml` and `.sdd/project-map.md` when available

Ignore host-global skills that are not readable from the repo context unless the host exposes them normally.

## Writes

Write or refresh:
- `.sdd/skill-registry.md`

Do not create a separate persisted compact-rules file in the MVP.

## Discovery scope

Always register:
- core SDD skills
- support SDD skills
- `_shared` contracts that affect routing or constraints

Optionally register:
- repo-local support skills that are likely to matter during implementation

Do not bloat the registry with generic host capabilities that add no routing value.

## Output structure

Use the template at `templates/bootstrap/skill-registry.md` as the baseline shape.

The registry should contain:
- metadata
- canonical SDD skills table
- support skills table
- project-local auxiliary skills table when applicable
- compact rules summary
- tracked refresh signals

## Compact rules

The compact rules section should summarize only the reusable facts that phases repeatedly need, such as:
- canonical artifact root
- project map path
- skill registry path
- language preference
- package manager
- quality commands
- major repo conventions
- important risk notes

Keep this section short enough for session injection.

## Workflow

1. Read canonical SDD skills and classify each as `core`, `support`, or `shared-contract`.
2. Capture path, responsibility, and stage readiness for each canonical skill.
3. Optionally include project-local skills that are clearly reusable and inside the repo.
4. Derive compact rules from `openspec/config.yaml`, `.sdd/project-map.md`, and strong project signals.
5. Record the refresh signals that later runs should compare:
   - lockfiles
   - tool config files
   - maintained docs
   - key source directories
6. Write `.sdd/skill-registry.md` in English.

## Quality bar

- The registry should help routing, not mirror the entire filesystem.
- Responsibilities must stay short and stable.
- Compact rules must not repeat full project-map sections.
- If a skill is reserved but not yet production-ready, say so explicitly.

## Validation

Before finishing, verify:
- every canonical SDD skill is present
- support skills are not misclassified as core
- compact rules can be read quickly by an orchestrator
- tracked refresh signals are specific enough to justify rerunning bootstrap later

## Expected envelope

On success:
- `status: success`
- include `.sdd/skill-registry.md` in `artifacts`
- include evidence for discovered skills and tracked refresh signals

Use `partial` when the canonical registry is complete but project-local skill discovery remains uncertain.
Use `blocked` only when canonical skills cannot be resolved or the package location is ambiguous.
