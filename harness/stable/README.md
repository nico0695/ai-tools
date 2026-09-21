# stable/

Validated copies of experimental harnesses, ready to copy into a project.

When a harness exists in both stages, this is the one to use. The experimental copy may keep moving.

## Harnesses

| Harness | What it does | Start here |
|---|---|---|
| `sdd-lite` | Structured workflow for bounded repo changes: bootstrap, proposal, spec, design, plan, one execution stage at a time, QA, optional review/delivery/archive | [USER-GUIDE.md](./sdd-lite/USER-GUIDE.md) |

## Install in a project

```bash
./install.sh harness --project /path/to/your-project
```

The installer copies this package to `./sdd-lite/` in the target project (updates keep `project-context.md`, `skill-catalog.md`, and `openspec/`) and copies `sddl-init` into the chosen agent. Then run `sddl-init` in the agent. Runtime artifacts stay under `./sdd-lite/` in the target project, not in this repository.
