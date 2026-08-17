# Claude Code adapter

- Executable: `claude`
- Child command: `claude -p --output-format stream-json --no-session-persistence --permission-mode acceptEdits <prompt>`
- Use a new process for every probe and level-3 checkpoint.
- Capture stream JSON, stderr, CLI version, usage, and reported cost when present.
- Do not use `--continue` or `--resume`.
- Do not bypass permissions.
- The project-facing evaluator skills normally live under `.claude/skills/`.

Provider review must inspect whether `CLAUDE.md` imports an `AGENTS.md` that already
contains a full sdd-lite wrapper. Two full wrappers in the resolved context are a
warning because they duplicate tokens and may give conflicting worker guidance.

