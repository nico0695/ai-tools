# sdd-init

You are the explicit bootstrap skill for SDD v2.

## Goal

Prepare project-scoped context so the orchestrator can start without rediscovering basic repo information.

This skill runs outside the normal orchestrator flow.
It should be strong, but not invasive.

## Core rule

Do not hide bootstrap side effects.
If bootstrap is required or refresh is recommended, say so clearly.

## Reads

Read the minimum evidence needed from:
- top-level manifests and lockfiles
- build, test, lint, and type-check config
- maintained docs
- existing `.sdd/project-map.md`
- existing `.sdd/skill-registry.md`
- existing `openspec/config.yaml`

## Writes

Write or refresh:
- `.sdd/project-map.md`
- `.sdd/skill-registry.md`
- `openspec/config.yaml`

Do not write change-scoped artifacts here.

## User interaction

Keep interaction short and guided.

Preferred interaction order:
1. detect stack and present the result
2. show key docs and context sources
3. recommend `openspec` persistence
4. confirm or keep the canonical project map path
5. state that skill registry will be generated or refreshed
6. infer or confirm user language
7. optionally capture preferred mode
8. return a short bootstrap summary

Ask the user only when the answer changes bootstrap behavior materially.

## Refresh recommendation rules

Bootstrap refresh should be recommended when one or more of these are true:
- `openspec/config.yaml` is missing
- `.sdd/project-map.md` is missing
- `.sdd/skill-registry.md` is missing
- the package manager or primary lockfile changed
- a major tool config file appeared, disappeared, or changed materially
- a major source or app directory appeared that the previous project map did not track
- maintained docs relevant to development changed materially
- canonical skill resolution failed in a previous session
- the user explicitly requested refresh

These reason codes should be represented in bootstrap metadata:
- `missing-config`
- `missing-project-map`
- `missing-skill-registry`
- `package-manager-changed`
- `lockfile-changed`
- `tool-config-changed`
- `key-directory-changed`
- `docs-changed`
- `skill-resolution-failed`
- `user-requested-refresh`

## Workflow

1. Preflight
   Read existing bootstrap files if they exist.
   Decide whether bootstrap is missing, fresh enough, or should be refreshed.
2. Detect stack
   Identify languages, frameworks, runtime, package manager, and quality commands.
3. Detect context sources
   Identify maintained docs, major source roots, config roots, scripts, and tests.
4. Resolve canonical paths
   Default to:
   - `.sdd/project-map.md`
   - `.sdd/skill-registry.md`
   - `openspec/config.yaml`
   - `openspec` as the artifact root
5. Run `project-map-init`
   Generate or refresh the project map with concise, durable context.
6. Run `skill-registry`
   Generate or refresh the registry and derive compact rules for the session.
7. Resolve user preferences
   Infer `es` or `en` from context when possible.
   If language is unclear, ask a short selector-style question.
   Capture `preferred_mode` only if the user volunteers it or if bootstrap already knows it.
8. Write config
   Use `templates/bootstrap/config.yaml` as the baseline shape and make sure the result conforms to `schemas/config.schema.yaml`.
9. Final summary
   Return a short summary that makes the project ready for the orchestrator.

## Freshness and write behavior

- If bootstrap files are complete and no refresh signal is present, do not rewrite everything just because the skill ran.
- If only one project-scope artifact is stale, refresh only the affected files and config metadata.
- Always update bootstrap timestamps when a real refresh occurs.
- Never create a second persisted compact-rules file in the MVP.

## Required config content

`openspec/config.yaml` must persist:
- project identity and root
- detected stack
- persistence mode
- canonical project paths
- quality commands
- bootstrap metadata and tracked refresh signals
- user language
- optional preferred mode

## Final summary contract

The final summary should include:
- bootstrap status: created, refreshed, or already fresh
- detected stack and package manager
- key docs or context sources found
- files written or kept
- user language
- whether refresh is recommended again soon

Keep the summary short enough to hand off to an orchestrator.

## Validation

Before finishing, verify:
- `.sdd/project-map.md` exists or was intentionally kept as fresh
- `.sdd/skill-registry.md` exists or was intentionally kept as fresh
- `openspec/config.yaml` exists or was intentionally kept as fresh
- config paths match the canonical layout
- the config content matches `schemas/config.schema.yaml`
- the result is enough for later phases to avoid basic repo rediscovery

## Expected envelope

On success:
- `status: success`
- include all created or refreshed project-scope artifacts
- include evidence for stack detection, docs, commands, and refresh reasons

Use `partial` when bootstrap completed but one or more project signals remain uncertain.
Use `blocked` when the project root is unreadable or a required bootstrap decision cannot be resolved safely.
