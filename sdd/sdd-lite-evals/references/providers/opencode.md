# OpenCode adapter

- Executable: `opencode`
- Child command: `opencode run --format json --dir <fixture> <prompt>`
- Use a new process and omit `--continue`/`--session` for every probe and checkpoint.
- Capture JSON events, stderr, CLI version, model, variant, and usage when exposed.
- Do not use `--dangerously-skip-permissions`.
- The project-facing evaluator skills default to `.opencode/skills/`; the path is
  configurable in the project profile for installations using another convention.

Provider review should flag wrapper text that promises native descendants when the
configured OpenCode agent cannot launch them; the expected behavior is the explicit
inline fallback from the AGENTS wrapper.

