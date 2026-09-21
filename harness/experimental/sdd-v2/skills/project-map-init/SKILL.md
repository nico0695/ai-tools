# project-map-init

You generate the canonical project map used by SDD v2.

## Goal

Produce or refresh `.sdd/project-map.md` so later phases can recover project context without depending on chat memory.

The project map must stay concise, evidence-based, and versionable.

## When to use

Use this skill during `sdd-init` when:
- bootstrap is missing
- bootstrap refresh is recommended
- the user explicitly asks to refresh project context

Do not use this skill as a substitute for deeper change-specific discovery. That belongs to `sdd-explore`.

## Reads

Read the minimum project evidence needed to establish durable context:
- top-level manifests and lockfiles
- build, test, lint, and type-check config
- maintained docs near the root or under `docs/`
- shallow directory structure
- existing `.sdd/project-map.md` if it exists
- `openspec/config.yaml` if it exists

Prefer shallow, high-signal reads first. Do not recursively scan the whole repo unless the structure is genuinely ambiguous.

## Writes

Write or refresh:
- `.sdd/project-map.md`

## Output structure

Use the template at `templates/bootstrap/project-map.md` as the baseline shape.

The final map must include:
- metadata
- stack summary
- package manager and quality commands
- important directories
- architecture and module signals
- maintained docs and sources of truth
- conventions
- repo-specific risks or oddities

## Workflow

1. Resolve the canonical output path from `openspec/config.yaml` when available.
   Default to `.sdd/project-map.md`.
2. Detect stack signals from manifests, lockfiles, and executable project config.
3. Identify the package manager from lockfiles and manifest conventions.
4. Detect quality command candidates from package scripts or equivalent config.
5. Build a shallow directory map of important areas only.
6. Capture maintained docs and source-of-truth files.
7. Summarize conventions that are strongly supported by evidence.
8. Record notable risks or unusual repo layout decisions.
9. Write the project map in English.

## Quality bar

- Prefer observed facts over inferred architecture stories.
- Name uncertainty explicitly when evidence is incomplete.
- Do not duplicate full docs into the project map.
- Keep the file readable enough for repeated bootstrap use.

## Validation

Before finishing, verify that the map answers these questions:
- What stack and package manager does the repo use?
- Where should later phases look for source, tests, config, scripts, and docs?
- What commands matter for build, test, lint, and type-check?
- What structural or process risks should later phases remember?

## Expected envelope

On success:
- `status: success`
- include `.sdd/project-map.md` in `artifacts`
- include evidence for the manifests, docs, and directories used

Use `partial` when the map is usable but still contains explicit unknowns.
Use `blocked` only when the repo cannot be read reliably or the root is ambiguous.
