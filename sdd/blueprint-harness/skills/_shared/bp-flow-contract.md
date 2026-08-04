# bp-flow-contract

Canonical vocabulary and runtime flow rules. Rules stated here are not restated elsewhere — other files reference this contract in one line.

## Canonical ids

- Objective types: `bug-triage`, `requirements-refinement`, `code-consultation`.
- Skills: `bp-init`, `bp-context-mapper`, `bp-analyzer`, `bp-diff-parser`, `bp-strategist`, `bp-doc-exporter`, `bp-handoff`.
- Phases: `interview`, `context_mapping`, `analysis`, `history`, `strategy`, `export`, `handoff`, `inline_answer` (plus `none` before the first phase).

## Result envelope

Every delegated skill ends its reply with exactly one fenced YAML block:

- Required: `status` (`success | partial | blocked`), `executive_summary` (≤ 3 lines), `artifacts` (files created or updated — must be `[]` for read-only workers), `next_action`, `open_risks`.
- Optional: `user_message`, `state_mutations`, `findings` (rows per `bp-findings-contract`), `decision_required` + `decision_options`, `context_resolution` (`injected | fallback | none`), `artifact_digests_used`, `recommended_next_step`.

Rules:

- `partial` = useful output with declared gaps. `blocked` = a precondition or user input is missing; name it in `next_action`.
- The orchestrator is the **only writer** of `state.yaml` and `index.yaml`. It applies `state_mutations` after verifying the envelope. A read-only worker that reports written files is an **incident**: stop, audit, distrust its output.
- `recommended_next_step` is a signal; the orchestrator's routing table is the authority.
- Workers receive pre-resolved context (paths + short digests, never artifact bodies). If `context_resolution` is not `injected`, the orchestrator re-resolves context before the next delegation.

## Worker execution boundary

Included verbatim in every delegation envelope. For read-only workers (`bp-context-mapper`, `bp-analyzer`, `bp-diff-parser`, `bp-strategist`):

> You are a phase executor. Work read-only. Do NOT write any file, do NOT launch sub-agents, do NOT orchestrate further steps. Complete your phase and return the result envelope.

For writer skills (`bp-doc-exporter`, `bp-handoff`, `bp-init`), the write clause becomes: "Write ONLY the owned path(s) named in this envelope (`bp-persistence-contract.md`)." Everything else is identical.

## Rigor levels

`config.yaml.rigor_level` modulates depth. Single source:

| Level | Analyzer budget | Strategist alternatives | Root-cause evidence bar | Deep interview |
|---|---|---|---|---|
| `light` | 1 pass, ≤ 4 files | max 2 | inference allowed (labeled) | never suggested |
| `standard` | 1–2 passes, ≤ 8 files | 2–3 | label inference; prefer fact when available | suggested when the complexity rubric fires |
| `deep` | ≤ 3 passes, ≤ 15 files | 3, plus discarded options | only `deterministic` evidence may assert cause; otherwise `unknown` | suggested proactively |

## Flow rules

- Every flow starts by creating or resuming `objectives/{slug}/` and registering the objective in `index.yaml`.
- Escalation valve: when the user wants the change built, close the objective (optionally via `bp-handoff`) and route to sdd-lite. Blueprint never implements.
- Phase-close consolidation: at the close of interview, analysis, and strategy the orchestrator persists state + digests and suggests compacting. Chat memory is disposable; persisted state is not.

## Resume rules

Resume reads `index.yaml` → the objective's `state.yaml` → artifact digests, in that order, never prior chat memory. If state and digests disagree, digests win and state is repaired.
