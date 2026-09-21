# openspec-convention

This contract defines the canonical repo-local layout for SDD v2 persistence.

## Canonical layout

```text
openspec/
  config.yaml
  changes/
    {change-name}/
      state.yaml
      explore.md
      proposal.md
      spec.md
      design.md
      tasks.md
      apply-progress.md
      verify-report.md
    archive/
      YYYY-MM-DD-{change-name}/
        state.yaml
        explore.md
        proposal.md
        spec.md
        design.md
        tasks.md
        apply-progress.md
        verify-report.md
        archive-report.md

.sdd/
  project-map.md
  skill-registry.md
```

## `change-name` rule

`change-name` must use lowercase kebab-case:

```text
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Rules:
- no spaces
- no slashes
- no dates inside the active change name
- archive adds the date prefix externally

## Artifact naming rules

- use `proposal.md`, not `propose.md`
- use a single `spec.md` per change in MVP
- use `verify-report.md` for final verification
- use `archive-report.md` only inside the archive folder

## Active versus archived changes

- Active changes live under `openspec/changes/{change-name}/`.
- Verified-but-not-archived changes remain in the active folder with lifecycle status `verified_pending_archive`.
- `sdd-archive` moves the full active folder into `openspec/changes/archive/YYYY-MM-DD-{change-name}/`.
- `archive-report.md` is created during archive, not before.
- `planner` never archives; it stops at `planned` in the active change path.
- Optional review hooks such as `judgment-day` do not change the canonical archive layout by themselves.

## MVP persistence rule

For MVP execution, `openspec` is the only persistence mode that should be treated as operationally complete.

Other modes may exist in schemas or config, but they must not change canonical artifact expectations for the core flow.
