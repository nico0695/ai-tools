# Codex Example

This directory contains the minimum Codex-facing wrapper surface for SDD v2.

It is intentionally thin.
The canonical source of truth remains:
- `orchestrator/SDD-ORCHESTRATOR.md`
- `skills/`
- `skills/_shared/`
- `schemas/`
- `templates/`

## What this example is for

Use this example when you want to run SDD v2 in Codex without depending on an informal reading of the whole planning document.

This example gives you:
- a recommended repo-local installation convention
- thin wrapper prompts for Codex
- a minimal end-to-end usage flow

## Recommended installation convention

Inside the target project, vendor the full `sdd-v2` package in a stable repo-local path.

Recommended package location:

```text
tools/sdd-v2/
```

Why this convention:
- it is repo-local, versionable, and host-neutral
- it does not turn `.codex` into the source of truth
- it keeps host-specific wrappers separate from canonical SDD contracts

Keep these generated runtime artifacts at the target project root:

```text
.sdd/
openspec/
```

Do not split the package by copying only a few skills.
At minimum, keep the full canonical package surface together:
- `orchestrator/`
- `skills/`
- `schemas/`
- `templates/`

## Files in this example

- `agents.md`
  - thin Codex wrapper prompts for bootstrap and orchestration
- `example-flow.md`
  - a minimal usage sequence from bootstrap to an active change

## Operating model in Codex

Use two layers:

1. Bootstrap
   Run `sdd-init` first when the project is new to SDD v2 or when bootstrap refresh is needed.
2. Orchestration
   After bootstrap, run the Codex orchestrator wrapper.
   That wrapper should follow the canonical orchestrator contract and delegate to phase skills as needed.

Important rules:
- `sdd-init` stays outside the normal orchestrator flow
- Codex wrappers must not duplicate logic that already lives in `SKILL.md`, `_shared`, or `SDD-ORCHESTRATOR.md`
- project truth lives in `.sdd/`, `openspec/`, and repo reality, not in Codex chat memory

## Quick start

1. Vendor this package into the target repo as `tools/sdd-v2/`.
2. Open `agents.md` and use the bootstrap wrapper prompt first.
3. Confirm that bootstrap created or refreshed:
   - `.sdd/project-map.md`
   - `.sdd/skill-registry.md`
   - `openspec/config.yaml`
4. Start a second Codex interaction with the orchestrator wrapper prompt from `agents.md`.
5. Drive changes through the normal phase flow.

For a concrete session outline, see `example-flow.md`.
