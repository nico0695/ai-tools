---
name: sddl-eval-init
description: >-
  Initialize a local sdd-lite-evals workspace for the current project and active CLI.
  Use before the first sdd-lite evaluation, when evaluator skills need project-local
  installation, or when the project profile must be recreated. This validates but
  never installs or repairs sdd-lite itself.
---

# sddl-eval-init

Create evaluation control data without changing the sdd-lite installation.

## Resolve the harness

Resolve the real directory of this skill. If its package root contains
`scripts/sddl_eval.py`, use it. For a copied installation, read `.harness-root`.
Block if neither resolves to an existing harness.

## Inspect before asking

Determine the project root, active provider, existing `sdd-lite/`, Git state,
installed wrappers, and chat language. Ask no more than three short questions, and
only for unresolved choices:

- workspace id when the repository name is unsuitable
- symlink or copy installation method; recommend symlink
- confirmation of the inferred provider or a non-default sdd root

## Execute

Run:

```text
python3 <harness>/scripts/sddl_eval.py init
  --project-root <project>
  --provider <codex|claude|opencode>
  --workspace-id <id>
  --install-method <symlink|copy>
  --language <auto|es|en>
```

If the command returns `blocked`, explain the missing or incompatible sdd-lite
setup and stop. Do not call `sddl-init`, inject wrappers, or offer to repair the
project in the same action.

On success, report workspace path, installed evaluator skill paths, sdd-lite hash,
and Level 1 findings. Mention that evaluator skills are excluded from child fixtures.

