# experimental/

Incubation copies: harnesses still being built and tested. Validated versions live in [../stable/](../stable/README.md); a harness is promoted by copying it there, and the two copies are allowed to diverge. When both exist, the one in `stable/` is the one to use.

## Harnesses

| Harness | What it is |
|---|---|
| [sdd-lite](./sdd-lite/README.md) | Lighter SDD for bounded changes. The validated copy is in `stable/`. |
| [sdd-v2](./sdd-v2/README.md) | Fuller SDD lifecycle, still incubating. |
| [blueprint-harness](./blueprint-harness/README.md) | Read-only discovery harness (RFCs, bug triage, audits) with an optional handoff into sdd-lite. |
| [sdd-lite-evals](./sdd-lite-evals/README.md) | Provider-aware evaluations against an existing sdd-lite installation. |
| [sdd-lite-bak](./sdd-lite-bak/README.md) | Frozen snapshot of an older sdd-lite. Do not use. |
