# sdd-lite-mapping

Correspondence between `blueprint-harness` (`bp-*`) and `sdd-lite` (`sddl-*`) vocabulary. Contracts are blueprint-owned but mirror sdd-lite deliberately (analysis decision D9); this doc exists to keep the mirroring conscious. Physical sharing (`sdd/_shared/`) is deferred until both stabilize.

| Concept | blueprint-harness | sdd-lite | Notes |
|---|---|---|---|
| Result envelope | `bp-flow-contract` "Result envelope" | `sddl-flow-contract` "Common result structure" | bp adds `user_message`, `state_mutations`; bp workers must report `artifacts: []` |
| State writer | orchestrator only (applies `state_mutations`) | skills write their own state sections | deliberate bp improvement |
| Worker boundary | `bp-flow-contract` "Worker execution boundary" | orchestrator "Standard Worker Handoff" | same intent, bp adds read-only clause |
| Checkpoints | 7 types, `bp-user-interaction-contract` | 12 types, `sddl-user-interaction-contract` | bp subset; `smart skip` and recording rules identical in spirit |
| Severity | `bp-findings-contract` | `sddl-review-ledger-contract` "Severity Model" | same scale (`critical…info`) |
| Evidence | `fact / inference / unknown`, `evidence_class` | deep-explorer + review protocols | same taxonomy |
| Digests | fixed block, `bp-persistence-contract` | per-artifact digest sections | bp fixes one format for all artifacts |
| Unit of work | `objectives/{slug}/` | `changes/{change-name}/` | same isolation pattern |
| Language rule | English persisted, chat es/en | identical | required for handoff compatibility |
| Handoff | `bp-handoff` → `openspec/inbox/{slug}.md` | consumed by `sddl-proposal` (patch) | only coupling point between harnesses |
| Bug objective | `bug-triage` (diagnose) | `bug-fix` (implement) | routing rule lives in wrappers |
