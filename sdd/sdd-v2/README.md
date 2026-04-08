# SDD v2

Status: Foundation through Stage 8 Codex wrapper implementation completed inside `sdd-v2`.

This directory incubates the new SDD v2 system without mixing it with v1 or global roots.

Current scope:
- Canonical package layout is in place.
- Shared contracts, schemas, orchestrator rules, bootstrap skills, and formalization skills are implemented.
- Stage 6 execution contracts are implemented for `sdd-apply` and `stage-qa`.
- Stage 7 final-verification and archive contracts are implemented for `sdd-verify`, `sdd-archive`, `verify-report.md`, and `archive-report.md`.
- Stage 8 Codex-facing wrapper and usage example are implemented under `examples/codex/`.

Current implementation highlights:
- `orchestrator/SDD-ORCHESTRATOR.md` defines routing, checkpoints, resume, and lifecycle behavior.
- `skills/_shared/` defines canonical ids, artifact ownership, persistence, interaction, and openspec conventions.
- `skills/project-map-init`, `skills/skill-registry`, and `skills/sdd-init` define bootstrap behavior.
- `skills/sdd-explore`, `skills/sdd-propose`, `skills/sdd-spec`, `skills/sdd-design`, and `skills/sdd-tasks` define the formalization pipeline.
- `skills/sdd-apply` and `skills/stage-qa` define controlled batch execution, pre-apply checkpoints, dirty-tree blocking, and incremental QA.
- `skills/sdd-verify` and `skills/sdd-archive` define final verification, closeout review routing, archival guardrails, and planner exclusion from archive.
- `templates/artifacts/tasks.md` and `templates/artifacts/apply-progress.md` support batch execution and incremental QA traceability.
- `templates/artifacts/verify-report.md` and `templates/artifacts/archive-report.md` support evidence-heavy closeout and auditable archival closure.
- `examples/codex/` defines the minimum Codex wrapper surface, installation convention, and usage flow without duplicating canonical SDD logic.

Decision continuity:
- Use [`docs/decisions/stage-6-compact-handoff.md`](/Users/nicolasschmidt/Documents/develop/ai-tools/sdd/sdd-v2/docs/decisions/stage-6-compact-handoff.md) for the compact Stage 6 continuity snapshot.
- Use [`docs/decisions/stage-7-compact-handoff.md`](/Users/nicolasschmidt/Documents/develop/ai-tools/sdd/sdd-v2/docs/decisions/stage-7-compact-handoff.md) for the compact Stage 7 continuity snapshot.
- Use [`docs/decisions/stage-8-compact-handoff.md`](/Users/nicolasschmidt/Documents/develop/ai-tools/sdd/sdd-v2/docs/decisions/stage-8-compact-handoff.md) for the compact Stage 8 continuity snapshot.
- [`docs/decisions/stage-7-new-chat-prompt.md`](/Users/nicolasschmidt/Documents/develop/ai-tools/sdd/sdd-v2/docs/decisions/stage-7-new-chat-prompt.md) is kept as a historical prompt from when Stage 7 was still pending.
