@AGENTS.md

## Platform: Claude Code

This section governs in Claude Code. Everything imported above applies, **except** the `## Platform: AGENTS.md / Codex` section, which does not.

- Delegate through the native Agent tool as the named type `loga-worker`. Fresh context; wait for the result. Do not use the Skill tool, a history fork, or the built-in Explore type as the launcher.
- Delegate per step and per question, never per log file. Workers never launch descendants.
- Parallelize only independent read-only script queries. Never overlap writes to the same `record/` file.
- The adapter sets no `model` and no `effort`: the worker inherits the session's.
- If the `loga-worker` agent type is unavailable (adapter missing or stale), launch `general-purpose`, paste the body of `.claude/agents/loga-worker.md` at the top of the handoff, state that host-level tool limits are not enforced, and recommend rerunning `loga-init`.
- Under `auto` or `bypassPermissions` the host ignores an adapter's `permissionMode`, so the worker's write scope is prompt-level only. A worker writing outside `analyses/<id>/{record,reports}/` is an incident: discard its result and say so.
- If the Agent tool is denied or unavailable, state that fresh-context isolation is unavailable and execute the named skill in the main context — do not claim a named agent ran.
