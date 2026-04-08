# Codex Example Flow

This is a minimal usage sequence for Codex after vendoring `sdd-v2` into:

```text
tools/sdd-v2/
```

## Step 1: Bootstrap

Open a Codex interaction and use the bootstrap wrapper from `agents.md`.

Expected result:
- `.sdd/project-map.md`
- `.sdd/skill-registry.md`
- `openspec/config.yaml`

## Step 2: Start orchestration

Open a second Codex interaction and use the orchestrator wrapper from `agents.md`.

Then add the actual work request, for example:

```text
Plan and implement a bug fix for duplicated invoice totals in the checkout summary.
```

Expected early behavior:
- objective inference
- mode inference
- `change-name` inference
- current artifact/state reuse when present
- route into `sdd-explore` or the next safe phase

## Step 3: Resume later

When the change already exists, invoke the orchestrator wrapper again with a resume-oriented request, for example:

```text
Continue the existing change `fix-checkout-invoice-totals` and tell me the next safe phase.
```

Expected behavior:
- read `openspec/changes/{change-name}/state.yaml`
- resume from persisted lifecycle status
- avoid rediscovering bootstrap context

## Step 4: Bootstrap refresh case

If the package manager, lockfile, major tool config, or project map assumptions changed, run the bootstrap wrapper again before continuing implementation-heavy flow.

## Guardrail reminder

- bootstrap first
- orchestrator second
- canonical rules stay in the vendored `sdd-v2` package
- generated project state stays in `.sdd/` and `openspec/`
