# Stage 8 Compact Handoff

## Purpose

This file is a compact continuity snapshot for the completed Stage 8 work.
It exists so continuation does not depend on chat history alone.

## Date

- recorded_at: 2026-04-05

## Stage 8 progress

### Completed

- Replaced the placeholder Codex example README.
- Added a thin Codex wrapper surface under `examples/codex/`.
- Documented a recommended repo-local installation convention:
  - vendor the package under `tools/sdd-v2/`
  - keep generated project state in `.sdd/` and `openspec/`
- Added thin wrapper prompts for:
  - bootstrap via `sdd-init`
  - orchestration via `SDD-ORCHESTRATOR.md`
- Added a minimal end-to-end usage flow for Codex.

## Files changed in Stage 8

- `examples/codex/README.md`
- `examples/codex/agents.md`
- `examples/codex/example-flow.md`
- `README.md`
- `docs/decisions/README.md`

## Current Codex packaging stance

- Codex wrappers are adapters, not the source of truth.
- Canonical behavior still lives in:
  - `orchestrator/SDD-ORCHESTRATOR.md`
  - `skills/`
  - `skills/_shared/`
  - `schemas/`
  - `templates/`
- The Codex wrapper layer should stay thin and should not duplicate phase logic or orchestration rules.

## Current usage model

1. Vendor `sdd-v2` into the target repo at `tools/sdd-v2/`.
2. Run bootstrap through the Codex bootstrap wrapper.
3. Confirm `.sdd/project-map.md`, `.sdd/skill-registry.md`, and `openspec/config.yaml`.
4. Run the Codex orchestrator wrapper for actual change work.

## Remaining risks and follow-up

- Stage 8 was completed as a wrapper/docs/example pass, not as a runtime validation pass across all objectives and modes.
- No install/setup scripts were added in this stage; the installation convention is documented, not automated.
- `examples/codex/` is enough for manual use in Codex, but Stage 10 still needs end-to-end validation and hardening.

## Recommended next step

Proceed to Stage 10:
- execute full end-to-end scenarios
- verify resume behavior
- test bootstrap refresh paths
- test verify failure and archive blocking
- harden docs and prompts based on real runs
