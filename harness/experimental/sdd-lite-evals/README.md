# sdd-lite-evals

Local, provider-aware evaluations for an **existing installation** of `sdd-lite`.
The package is a sibling of `sdd-lite`, but it does not import or modify that source
tree. Each project profile points to the copy that is actually installed in the
project under review.

Spanish operating guide: [USER_GUIDE_ES.md](./USER_GUIDE_ES.md). Case authoring:
[docs/authoring-cases.md](./docs/authoring-cases.md).

## Principles

- enter through a skill or the deterministic CLI
- keep the evaluator out of child sessions
- run model-backed probes in disposable project fixtures
- validate contracts before spending model tokens
- record evidence, environment, usage, and an explicit baseline locally
- never initialize or repair a missing sdd-lite installation automatically

All generated project profiles, cases, runs, reports, and history live below
`workspaces/` and are ignored by Git.

## Three levels

| Level | Purpose | Model calls |
|---|---|---:|
| 1 | Static package, wrapper, route, skill, schema, and installation integrity | 0 |
| 2 | Clean-session trigger, routing, worker-bypass, resume, and approval probes | 1 per probe |
| 3 | Main flow: proposal → spec → design → plan → human approval → executor → QA | 1 per checkpoint |

Optional 4R review, Judgment Day, delivery, and archive are deliberately outside
the default level-3 flow.

## Quick start

From the project to review, explicitly load `skills/sddl-eval-init/SKILL.md` in the
active CLI the first time. The skill validates the project and runs:

```bash
python3 /path/to/sdd-lite-evals/scripts/sddl_eval.py init \
  --project-root "$PWD" --provider codex --install-method symlink
```

Then use the installed `sddl-eval-level-1`, `sddl-eval-level-2`,
`sddl-eval-level-3`, or `sddl-eval-report` skill. The optional `sddl-eval` skill
only helps select one of them.

Direct CLI use is also supported:

```bash
python3 scripts/sddl_eval.py level1 --workspace slow
python3 scripts/sddl_eval.py level2 --workspace slow --case main-flow-example \
  --provider codex
python3 scripts/sddl_eval.py level2 --workspace slow --case main-flow-example \
  --provider codex --execute
```

Model-backed commands are dry runs unless `--execute` is present. The harness
shows the number of child sessions before execution but does not enforce a token
or monetary cap.

## Workspace model

```text
workspaces/<project>/
  project.yaml
  cases/*.yaml
  campaigns/*.yaml
  fixtures/<run-id>/
  runs/<campaign>/<provider>/<run-id>/
  reports/<campaign>/
  history/index.json
```

The project profile and test case are independent. A case may be copied to another
workspace and adjusted without changing the harness skills.

## Safety and comparability

- `init` blocks when sdd-lite bootstrap, runtime, or wrappers are missing.
- Project skill installation never injects an evaluator wrapper.
- Fixture assembly excludes `sddl-eval*` skills and `.sdd-lite-evals` data.
- Level 3 records approval after the plan exists and resumes in a new CLI process.
- A baseline must be named explicitly; model or CLI differences appear as
  comparability warnings.
- The installed sdd-lite tree receives a content hash. A human version label is
  optional and is not treated as proof that two installations are identical.

## Development checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/sddl_eval.py --help
```
