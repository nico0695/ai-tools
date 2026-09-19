# skills/

Project-agnostic skills, organized by maturity. Project-specific skills live under `projects/`.

| Folder | What's there | Install |
|---|---|---|
| [stable/](./stable/README.md) | Validated skills: audited, documented (`USAGE.md` + `README.md`), safe to recommend | Default |
| [experimental/](./experimental/README.md) | Skills still being built and tested | Opt-in |
| [evals/](./evals/trigger-cases.json) | Static routing expectations for skills in both stages | — |

## Lifecycle

1. A new skill starts in `experimental/<name>/`.
2. Once its behavior is validated, it is promoted by **copying** it to `stable/<name>/` and adding
   `USAGE.md` and `README.md`.
3. The experimental copy stays as the incubation version; the two may diverge. When a skill exists in
   both, `stable/` is the one to install.

`README.md` and `USAGE.md` are for this repo: the installer does not copy them.
