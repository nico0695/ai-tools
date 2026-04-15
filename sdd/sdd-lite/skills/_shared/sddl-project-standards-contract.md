# sddl-project-standards-contract

This contract defines how `sdd-lite` represents project conventions, quality expectations, and language discipline.

## Persisted language rule

The following stay in English:

- shared contracts
- `SKILL.md` files
- schemas
- template files
- generated Markdown artifacts
- persistent keys and structured values

Chat interaction may use `es` or `en`.
Changing the chat language must not change persisted artifact language.

## Project profile representation

Project standards should be recoverable from `./sdd-lite/openspec/config.yaml` and `./sdd-lite/project-context.md` using these categories:

| Category | Examples |
|---|---|
| stack | languages, frameworks, runtime, package manager |
| structure | source roots, test roots, config roots, important directories |
| commands | install, test, build, lint, typecheck, format |
| conventions | naming, file placement, testing style, code style |
| sources of truth | manifests, lockfiles, maintained docs, executable config |
| risk notes | legacy zones, generated code, fragile modules, unclear ownership |

## Source-of-truth order

When project standards conflict, prefer this order:

1. executable project config and lockfiles
2. source tree reality
3. maintained docs
4. bootstrap artifacts under `./sdd-lite/`
5. user clarification

Older summaries must not override current executable evidence without explicit confirmation.

## Quality command shape

`config.yaml` should store quality commands as arrays of command strings.

Canonical keys:

- `install`
- `test`
- `build`
- `lint`
- `typecheck`

Optional keys:

- `format`
- `dev`

## Naming stability

These lite artifact names are fixed for the MVP:

- `project-context.md`
- `skill-catalog.md`
- `config.yaml`
- `state.yaml`
- `proposal-spec.md`
- `design-plan.md`
- `execution-log.md`
- `qa-report.md`
- `macro-plan.md`

## Conflict handling

If project standards are ambiguous or contradictory:

- prefer the safer execution path
- record the conflict in the relevant artifact or state
- ask the user only if the ambiguity changes scope, risk, or the chosen route

## Reusable support references

Support agents may be referenced from `skill-catalog.md` as reusable patterns.
Those references guide routing and analysis, but they are not persisted runtime artifacts by themselves.
