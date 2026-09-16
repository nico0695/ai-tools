# production/

Validated copies of the generic skills, audited for determinism and genericity and ready to install.
Each one keeps two docs, for two different readers:

- **`USAGE.md`** — what it does, when to use it, how to invoke it, a minimal example. Read this first.
- **`README.md`** — how it's built and why: the internal rules, the routing logic, the trade-offs.
  Read this to extend or audit the skill.

`SKILL.md` is the one Claude reads; the two docs above are for you.

## Skills

| Skill | What it does | Use it | How it's built |
|---|---|---|---|
| `doc-writer` | Turns available context into a grounded Markdown document — an ADR, an investigation, a report, a system doc | [USAGE.md](./doc-writer/USAGE.md) | [README.md](./doc-writer/README.md) |
| `4r-review` | Risk-tiered code review across four lenses, sized to what the change actually risks | [USAGE.md](./4r-review/USAGE.md) | [README.md](./4r-review/README.md) |
| `judgment-day` | Adversarial dual review: two blind judges, convergence decides what counts | [USAGE.md](./judgment-day/USAGE.md) | [README.md](./judgment-day/README.md) |
