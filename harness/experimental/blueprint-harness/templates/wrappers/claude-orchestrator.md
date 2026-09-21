<!-- bp-harness:start generated_at="<generated_at>" version="<version>" engine_root=".bp-harness" -->
# blueprint-harness

Read-only discovery harness: formalize requirements (RFCs), triage bugs (diagnose, never fix), consult code and history, audit changes. Engine: `.bp-harness/`. Workspace: `bp-workspace/`.

## When to use blueprint-harness

- "Formalize this idea / write an RFC", "why does X fail" (diagnosis), "how does X work / what changed", "evaluate this refactor".
- **Cross-harness routing:** "I have a bug" → blueprint `bug-triage` when the user wants understanding or a documented diagnosis; sdd-lite `bug-fix` when they want it fixed. When in doubt, triage first — its output hands off cleanly.
- Never for implementing changes. When the user wants the change built, blueprint closes with a handoff seed and routes to sdd-lite.

## When blueprint-harness is active

- Load `.bp-harness/orchestrator/BP-ORCHESTRATOR.md` and follow it. Contracts live in `.bp-harness/skills/_shared/`.
- Session mode (`interactive`/`auto`) is asked once per session by the orchestrator.

## Read-only enforcement (recommended permission set)

Blueprint performs **no** mutation of source code, the working tree, git history, or remotes — no exceptions. Recommended platform enforcement (offered by `bp-init`, applied to `.claude/settings.json` only with your confirmation; otherwise apply manually):

- deny `Edit`/`Write` outside: `bp-workspace/**`, `sdd-lite/openspec/inbox/**`, and the `bp-init` setup paths (`.bp-harness/**`, `.claude/skills/**`, `.agents/skills/**`, `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`) — the setup paths exist so re-init/update keeps working
- allow read-only git only: `git log`, `git show`, `git diff`, `git status`, `git blame`
- deny `git commit`, `git add`, `git push`, `git checkout`, `git reset`, `git tag`, and any state-changing bash

## Platform: Claude Code

- Launch each delegated phase (`bp-context-mapper`, `bp-analyzer`, `bp-diff-parser`, `bp-strategist`, `bp-doc-exporter`, `bp-handoff`) with the **Agent tool**, one call per phase, waited — never fire-and-forget.
- Analysis workers are read-only: prefer a read-only agent type when available.
- Do not use the Skill tool for phase delegation — the Agent tool is the only delegation mechanism; interviews are orchestrator-executed, never delegated.

### Fallback if the Agent tool is unavailable

- Run phases inline, sequentially, declaring the isolation loss visibly.
- Persist `state.yaml` and the phase artifact after every phase.
- Compress context between phases: keep state, decisions, and the next envelope; drop artifact bodies.
<!-- bp-harness:end -->
