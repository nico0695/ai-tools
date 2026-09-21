# project-standards-contract

This contract defines how project conventions and quality expectations are represented for SDD v2.

## Internal language rule

The following stay in English:
- shared contracts
- `SKILL.md` files
- artifact names
- persistent keys
- project map content

User-facing conversation may still be Spanish or English.

## Project profile representation

Project standards should be recoverable from `openspec/config.yaml` and `.sdd/project-map.md` with these categories:

| Category | Examples |
|---|---|
| stack | languages, frameworks, runtime, package manager |
| structure | important directories, module boundaries, entry points |
| commands | build, test, lint, type-check, format, dev |
| conventions | naming, file placement, code style, testing style |
| sources of truth | lockfiles, package manifests, build config, maintained docs |
| risk notes | repo-specific caveats, generated code, legacy zones |

## Source-of-truth order

When project standards conflict, prefer this order:

1. executable project config and lockfiles
2. source tree reality
3. maintained project docs
4. bootstrap summaries
5. user clarification

The system should not let old docs override executable reality without explicit confirmation.

## Quality command representation

`openspec/config.yaml` should represent quality commands in a stable shape:
- `test`
- `build`
- `lint`
- `typecheck`

Each value may be a list of command strings because some repos require more than one command per category.

## Naming stability

These names are fixed for MVP contracts:
- `proposal.md`
- `spec.md`
- `design.md`
- `tasks.md`
- `apply-progress.md`
- `verify-report.md`
- `archive-report.md`
- `refactor-rework`

## Conflict-handling rule

If project standards are ambiguous or contradictory:
- prefer the safer execution path
- surface the conflict in the relevant artifact or envelope
- ask the user only if the ambiguity affects scope, risk, or the chosen approach
