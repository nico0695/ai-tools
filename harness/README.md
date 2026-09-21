# harness/

Project-agnostic agent harnesses, organized by maturity. A harness is a packaged workflow (orchestrator + skills + templates + schemas), not a single skill.

| Folder | What's there | Use |
|---|---|---|
| [stable/](./stable/README.md) | Validated harnesses, safe to copy into a project | Default |
| [experimental/](./experimental/README.md) | Harnesses still being built and tested | Opt-in |

## Lifecycle

1. A new harness starts in `experimental/<name>/`.
2. Once its behavior is validated, it is promoted by **copying** it to `stable/<name>/`.
3. The experimental copy stays as the incubation version; the two may diverge. When a harness exists in both, `stable/` is the one to use.

Install `sdd-lite` with the repo installer (project only; not into this catalog repo):

```bash
./install.sh harness --project ~/app
```

That copies `stable/sdd-lite` to `~/app/sdd-lite/` and the `sddl-init` skill into the chosen agent. Then run `sddl-init` in the agent to bootstrap the project. Other harnesses are still copied by hand (`bp-init` and equivalents).
