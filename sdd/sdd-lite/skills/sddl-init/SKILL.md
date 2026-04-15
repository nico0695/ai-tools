# sddl-init

You are the explicit bootstrap skill for `sdd-lite`.

## Goal

Prepare durable project bootstrap context under `./sdd-lite/` so later lite stages can operate without rediscovering basic repository facts.

This skill stays shallow and high-signal.
It should gather enough evidence to bootstrap the flow, not perform deep exploration.

## Reads

Read the minimum project evidence needed from:

- top-level manifests and lockfiles
- package manager signals
- build, test, lint, and typecheck configuration
- maintained docs and contributor guidance
- obvious source, app, package, test, and config roots
- existing `./sdd-lite/project-context.md`
- existing `./sdd-lite/skill-catalog.md`
- existing `./sdd-lite/openspec/config.yaml`

## Writes

Write or refresh only:

- `./sdd-lite/project-context.md`
- `./sdd-lite/skill-catalog.md`
- `./sdd-lite/openspec/config.yaml`

Do not write change-scoped artifacts.
Do not write outside `./sdd-lite/`.

## User Interaction

Keep interaction short and selective.

State clearly:

- what you read
- what you inferred from repository evidence
- what you will write
- what remains uncertain

Ask the user only when the answer materially improves bootstrap quality.
Valid reasons to ask include:

- multiple plausible package managers or runtimes
- missing or contradictory quality commands
- ambiguous source roots in a multi-app or multi-package repository
- unclear preferred chat language between `es` and `en`

Do not ask for confirmation of obvious local choices already implied by the approved runtime.

Persisted content must remain in English.
Chat interaction may follow the detected or confirmed `chat_language`.

## Workflow

1. Preflight
   Read existing bootstrap files if they exist and determine whether bootstrap is missing, stale, or already usable.
2. Shallow repo scan
   Inspect only high-signal files and directories to detect:
   - languages, frameworks, runtime, and package manager
   - maintained docs and operating conventions
   - source roots, test roots, and config roots
   - candidate quality commands
3. Infer project bootstrap facts
   Infer project identity, canonical runtime paths, and bootstrap metadata from visible evidence.
4. Build project context
   Generate `./sdd-lite/project-context.md` from the bootstrap template using compact, reusable facts.
5. Build skill catalog
   Generate `./sdd-lite/skill-catalog.md` through an internal helper flow.
   This is not a separate skill.
6. Build config
   Generate `./sdd-lite/openspec/config.yaml` with the approved local runtime:
   - runtime root: `./sdd-lite/`
   - artifact root: `./sdd-lite/openspec/`
7. Final summary
   Return a short bootstrap summary that distinguishes reads, writes, inferences, and any questions asked.

## Validation

Before finishing, verify:

- bootstrap writes only target `./sdd-lite/`
- detected paths match the approved local runtime layout
- `project-context.md` captures stack, directories, docs, commands, conventions, and risks
- `skill-catalog.md` lists the canonical `sddl-*` skills and support agents
- `config.yaml` includes project identity, stack, quality commands, bootstrap metadata, canonical paths, and chat language support
- persisted artifacts remain English even when `chat_language` is `es`

## Expected Output

On success, provide:

- bootstrap status: `created`, `refreshed`, or `already_usable`
- files written or kept
- detected stack and package manager
- key docs, source roots, and quality commands found
- inferred items versus user-confirmed items
- unresolved bootstrap questions, if any

Use `partial` when bootstrap is usable but one or more high-value signals remain uncertain.
Use `blocked` only when the project cannot be scanned safely or a material contradiction prevents a reliable bootstrap.
