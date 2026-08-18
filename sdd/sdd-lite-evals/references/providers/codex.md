# Codex adapter

- Executable: `codex`
- Child command: `codex exec --json --ephemeral --sandbox workspace-write <prompt>`
- Use a new process for every probe and level-3 checkpoint.
- Capture JSONL stdout, stderr, CLI version, and the greatest observed token counters.
- Do not use `codex resume`; sdd-lite resume must come from persisted files.
- Do not use approval or sandbox bypass flags.
- The project-facing evaluator skills normally live under `.agents/skills/`.

Provider review should flag prompts that assume Claude-specific `Agent`/`Task`
tool names instead of describing native sub-agent behavior by capability.

