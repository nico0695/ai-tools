# Stage 7 New Chat Prompt

Status: Historical prompt captured before Stage 7 implementation.

Stage 7 is no longer pending.
The verify and archive contracts were completed inside `sdd-v2`.

Do not use this file as the current resume source for Stage 7 work.
Prefer:
- `docs/decisions/stage-7-compact-handoff.md` for the completed Stage 7 continuity snapshot
- `README.md` for current high-level repo status

Why this file remains:
- it preserves the exact kickoff prompt that was used to continue Stage 7 from a fresh chat
- it documents the user-confirmed constraints that shaped the implementation slices

Historical note:
- the original content of this file described Stage 7 as pending and split into controlled substeps
- that plan has now been executed through `Stage 7A` and `Stage 7B`

Current Stage 7 outcome summary:
- `skills/sdd-verify/SKILL.md` is implemented
- `skills/sdd-archive/SKILL.md` is implemented
- `templates/artifacts/verify-report.md` is implemented
- `templates/artifacts/archive-report.md` is implemented
- orchestrator and shared contracts were aligned with:
  - verify verdicts
  - `closeout_review`
  - `verified_pending_archive`
  - archive guardrails
  - planner exclusion from archive
  - optional `judgment-day` recommendation hook
