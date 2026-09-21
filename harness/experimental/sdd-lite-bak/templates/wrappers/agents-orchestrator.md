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

do not activate or read the sdd-lite runtime, do not load orchestration modules, do not ask for session or worker mode, and do not route stages. Execute only the named canonical skill under `<package-root>/skills/`, honor its scope and injected standards, return its result contract, and stop. A worker never launches descendants.

## Main-session activation

Activate sdd-lite for the main agent when:

- the user explicitly asks for sdd-lite (`sdd`, `sddl`, `con sdd-lite`, or equivalent)
- a feature, refactor, or fix has uncertain scope or approach
- work spans multiple files, lacks acceptance criteria, or carries non-trivial risk

Do not auto-activate for explanations, clear one-line fixes, or conversational exploration. For substantial work not explicitly requesting SDD, offer it once without forcing it; proceed normally if declined or ignored.

## Main-session runtime

When active, read `<package-root>/orchestrator/SDDL-RUNTIME.md` once and keep it as the main session's orchestration authority. Follow its module trigger table; never preload every module. The main agent alone owns routing, approvals, result processing, and orchestrator-owned ledger writes.

Use canonical skills under `<package-root>/skills/`, standards at `./sdd-lite/skill-catalog.md`, and schemas under `<package-root>/schemas/`. Run bootstrap preflight first, recover from persisted evidence before asking, and keep persisted artifacts in English while chat may be `es` or `en`.

## Platform: AGENTS.md

This wrapper is vendor-neutral for assistants driven by `AGENTS.md`/`.agents/`.

After bootstrap preflight passes on the first main-session SDD stage request, ask worker mode together with the runtime's execution-mode question and cache both:

- `native-workers` (recommended when supported): fresh native sub-agent per canonical stage.
- `inline-sequential`: main context executes stages sequentially when selected or native delegation is unavailable.

Worker mode controls isolation only; `interactive`/`auto` controls pacing only. Neither changes approvals or guardrails.

### Native workers

- Delegate per phase or approved execution stage, not per file.
- Pass the compact runtime handoff, including every worker-bypass control, and wait for the result before routing.
- Parallelize only independent read-only work or fully disjoint writes. Children never launch descendants.
- For 4R and judgment-day, first load `<package-root>/orchestrator/modules/review-runtime.md`, then use waited native fan-out. Judges remain blind; workers return findings only.

### Inline fallback

State that fresh-context isolation is unavailable. Retain state, decisions, digests, and the current handoff; prefer targeted persisted reads and do not claim conversation context was manually removed. Persist state after every stage and apply the full runtime result, routing, approval, and module rules. Explain the degradation when a mandatory delegation trigger fires.
<!-- sdd-lite:end -->
