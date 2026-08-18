<!-- sdd-lite:start generated_at="<generated_at>" version="0.2" package_root="<package-root>" -->
You have access to `sdd-lite`, a structured workflow for bounded repository changes.

## Worker bypass — evaluate first

If the current prompt is a delegated handoff containing all of these controls:

```yaml
sddl_role: phase-worker | review-worker
stage: sddl-*
orchestration_allowed: false
runtime_loading_allowed: false
```

do not activate or read the sdd-lite runtime, do not load orchestration modules, do not ask for session mode, and do not route stages. Execute only the named canonical skill under `<package-root>/skills/`, honor its scope and injected standards, return its result contract, and stop. A worker never launches descendants.

## Main-session activation

Activate sdd-lite for the main agent when:

- the user explicitly asks for sdd-lite (`sdd`, `sddl`, `con sdd-lite`, or equivalent)
- a feature, refactor, or fix has uncertain scope or approach
- work spans multiple files, lacks acceptance criteria, or carries non-trivial risk

Do not auto-activate for explanations, clear one-line fixes, or conversational exploration. For substantial work not explicitly requesting SDD, offer it once without forcing it; proceed normally if declined or ignored.

## Main-session runtime

When active, read `<package-root>/orchestrator/SDDL-RUNTIME.md` once and keep it as the main session's orchestration authority. Follow its module trigger table; never preload every module. The main agent alone owns routing, approvals, result processing, and orchestrator-owned ledger writes.

Use canonical skills under `<package-root>/skills/`, standards at `./sdd-lite/skill-catalog.md`, and schemas under `<package-root>/schemas/`. Run bootstrap preflight first, recover from persisted evidence before asking, and keep persisted artifacts in English while chat may be `es` or `en`.

## Platform: Claude Code

- Delegate each canonical stage through the native Agent tool with a fresh context and the compact handoff from `SDDL-RUNTIME.md`; do not use the Skill or Task tool as the stage delegation mechanism.
- `interactive`/`auto` controls pacing only. It never bypasses `stage_approval` or another mandatory gate.
- Parallelize only independent read-only work or fully disjoint write scopes. Never overlap artifact writes.
- For 4R and judgment-day, first load `<package-root>/orchestrator/modules/review-runtime.md`, then launch the selected read-only Agent workers as one waited batch where appropriate. Judges remain blind; workers return findings only.
- Every child receives the worker-bypass controls. If it discovers out-of-scope work, it returns `partial` or `blocked`; it does not delegate.

If the Agent tool is denied or unavailable, state that fresh-context isolation is unavailable, continue inline under the complete runtime contract, persist state after each stage, and explain the degradation when a mandatory delegation trigger fires.
<!-- sdd-lite:end -->
