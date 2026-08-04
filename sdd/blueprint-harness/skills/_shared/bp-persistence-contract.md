# bp-persistence-contract

Layout, ownership, naming, digest format, and budgets. Single source for persistence rules.

## Runtime layout

```
bp-workspace/
├── config.yaml            # schemas/bp-config.schema.yaml
├── index.yaml             # global objective index (shape below)
├── objectives/{slug}/     # state.yaml + intermediates
├── ideas/rfc-{slug}.md    # final RFCs
├── bugs/bug-{slug}.md     # final bug reports
├── audits/audit-{slug}.md # persisted audits
└── templates/             # user-owned; seeded once by bp-init, never overwritten
```

## Naming and language

- Slugs: `^[a-z0-9]+(?:-[a-z0-9]+)*$`. No dates in filenames — dates live in digests.
- Everything persisted (artifacts, keys, structured values) is written in **English**. Chat may be `es` or `en`; changing chat language never changes persisted language.

## Ownership

| Path | Only writer |
|---|---|
| `state.yaml`, `index.yaml`, `objectives/{slug}/*.md` (intermediates) | orchestrator (`bp-init` creates the empty `index.yaml` and directory skeleton at install) |
| `.bp-harness/` (engine copy) | `bp-init` |
| `ideas/`, `bugs/`, `audits/` finals | `bp-doc-exporter` |
| `./sdd-lite/openspec/inbox/{slug}.md` | `bp-handoff` |
| `config.yaml`, `templates/` seed, wrapper blocks, skill copies in `.claude/`/`.agents/`, platform permission settings (confirmed) | `bp-init` |

No other write is legitimate anywhere.

## Digest format (fixed)

Every artifact opens with a `## <Name> Digest` block of 3–6 flat bullet fields, no prose:

```
## <Name> Digest
- status: working | draft | approved | handed-off | superseded
- objective: {slug}
- updated: YYYY-MM-DD
- summary: <one line>
```

Digests are the anchor for routing and resume; update the digest in the same edit as the body. `state.yaml.artifacts` keeps a one-line copy of each summary.

## Artifact lifecycle

Intermediates stay `working`. Finals: `draft → approved → handed-off | superseded`. Status changes only through orchestrator checkpoints (`artifact_approval`, `handoff_gate`, `audit_persist_offer` — audits are born `approved`), executed via `bp-doc-exporter` `update-status`.

## index.yaml shape

```yaml
objectives:
  - slug: <slug>
    type: <objective type>
    lifecycle_status: <state enum>
    updated_at: YYYY-MM-DD
    digest: <one line>
```

## Budgets (hard caps, words)

| Artifact | Budget |
|---|---|
| interview-notes | 150–300 |
| analysis | 300–500 |
| alternatives | 300–500 |
| RFC | 400–800 |
| bug report | 300–600 |
| audit | 200–400 |
| handoff seed | 200–400 |

Budgets count the entire file — digest block and headings included. The four shared contracts stay under ~1,500 words combined; every SKILL.md under ~150 lines. Over budget means trim before persisting, not ask.
