# stable/

Validated copies of the experimental skills, audited for determinism and genericity and ready to copy into a project.
Each one keeps two docs, for two different readers:

- **`USAGE.md`** — what it does, when to use it, how to invoke it, a minimal example. Read this first.
- **`README.md`** — how it's built and why: the internal rules, the routing logic, the trade-offs.
  Read this to extend or audit the skill.

`SKILL.md` is the file the agent reads; the two docs above are for people maintaining or installing the skill.

## Install in a project

Copy or symlink the selected skill folder into the target project's skills directory:
`.claude/skills/` for Claude Code, or `.agents/skills/` for Codex and other agents that follow the
`AGENTS.md` convention. Keep the whole folder, including `SKILL.md` and any `assets/` or `references/`
it uses. The agent discovers it from there.

The routing cases in `../evals/trigger-cases.json` are static expectations for review; they are not automated
agent runs. End-to-end execution tests remain future work.

## Git safety boundary

These skills treat Git as read-only: they may inspect status, diffs, history, and references, but they do
not run `add`, `commit`, `push`, `stash`, create PRs, or otherwise change repository state. An explicit
request to perform a write is not executed.

## Skills

| Skill | What it does | Use it | How it's built |
|---|---|---|---|
| `doc-writer` | Turns available context into a grounded Markdown document — an ADR, an investigation, a report, a system doc | [USAGE.md](./doc-writer/USAGE.md) | [README.md](./doc-writer/README.md) |
| `standard-code-review` | One-pass review of a git diff, commits, branch, or PR | [USAGE.md](./standard-code-review/USAGE.md) | [README.md](./standard-code-review/README.md) |
| `4r-review` | Risk-tiered code review across four lenses, sized to what the change actually risks | [USAGE.md](./4r-review/USAGE.md) | [README.md](./4r-review/README.md) |
| `judgment-day` | Adversarial dual review: two blind judges, convergence decides what counts | [USAGE.md](./judgment-day/USAGE.md) | [README.md](./judgment-day/README.md) |
| `commit-closer` | Drafts a commit message and/or PR description from resolved git changes, read-only | [USAGE.md](./commit-closer/USAGE.md) | [README.md](./commit-closer/README.md) |
