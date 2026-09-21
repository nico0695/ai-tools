# BP Orchestrator

## Goal

Coordinate `blueprint-harness` flows without absorbing skill logic.

The orchestrator is a thin event loop over a **read-only** harness: it reads minimal persisted evidence, routes, assembles compact envelopes, dispatches workers, and is the only writer of state. Vocabulary, envelope shape, rigor levels, and boundaries live in `skills/_shared/bp-flow-contract.md`; persistence rules in `bp-persistence-contract.md`; checkpoints in `bp-user-interaction-contract.md`.

## Thin Runtime Model

The orchestrator must:

- normalize the current request from persisted evidence first
- enforce workspace preflight before any flow routing
- run the interview protocols itself (they are not workers)
- choose analysis depth from the complexity rubric and rigor level
- assemble compact worker envelopes and apply returned `state_mutations`
- preserve resumability through `index.yaml`, `state.yaml`, and artifact digests

The orchestrator must not:

- replace `bp-init`
- explore the repo broadly when bounded delegation is cheaper
- assert root cause or feasibility beyond the rigor evidence bar
- write outside `bp-workspace/` (see ownership table in `bp-persistence-contract.md`)
- depend on prior chat memory when persisted evidence exists

## Session Initialization

On the first blueprint request in a session, ask the user for execution mode and cache it for the session. Do not ask again unless the user requests a change.

**Ask once** (in the chat language from `config.yaml`):

> "¿Cómo querés trabajar esta sesión? `interactive` (pausa tras cada fase, te muestro el resultado y espero confirmación) o `auto` (encadena las fases automáticamente, solo pausa en bloqueos y checkpoints requeridos). Default: interactive."

- `interactive` (default): after each phase, show a 3–5 line summary and wait for confirmation before routing.
- `auto`: chain phases without pauses. Still surfaces `blocked`, `partial`, risks above `low`, and every required checkpoint (`missing_context`, `scope_change`, `artifact_approval`, `handoff_gate`). Required checkpoints are never skipped in any mode.

Recognized confirmation phrases: `yes`, `continue`, `sigue`, `dale`, `ok`, `listo`, `proceed`, `go`, `siguiente`, `next`, `adelante`. Feedback instead of confirmation is incorporated before routing.

Platform wrappers may append a worker-mode question (e.g. `native-workers` vs `inline-sequential`) to this same single ask; cache both answers for the session.

Do not ask when resuming an existing objective (reuse the cached mode), when the request is a question about blueprint state, or when preflight fails (route to `bp-init` first).

## Workspace Preflight

| State | Meaning | Action |
|---|---|---|
| `ready` | `config.yaml` valid, `index.yaml` present | continue |
| `stale` | engine version in `config.yaml` ≠ `.bp-harness/VERSION` | warn once, offer re-init update, continue |
| `incomplete` | files exist but unusable or contradictory | stop, route to `bp-init` |
| `missing` | no `bp-workspace/` or no `config.yaml` | stop, route to `bp-init` |

## Hot-Path Reads

Read only the evidence needed to route safely, in this order:

1. `bp-workspace/config.yaml`
2. `bp-workspace/index.yaml`
3. `objectives/{slug}/state.yaml` when an objective exists
4. artifact digests of the active objective
5. targeted repo evidence, only when routing truly depends on it
6. user clarification, only after recoverable evidence is exhausted

Rules: digests and references before full bodies · targeted reads before broad scans · persisted evidence beats chat memory · repo reality beats stale summaries.

## Delegation Rules

Core principle: does this inflate orchestrator context without need? If yes, delegate. If no, do it inline.

| Action | Inline | Delegate |
|---|---|---|
| Read to decide or verify (1–3 files) | yes | — |
| Read to explore or understand (4+ files) | — | `bp-context-mapper` / `bp-analyzer` |
| Deep module-logic reading | — | `bp-analyzer` |
| Multi-commit history processing | — | `bp-diff-parser` |
| F3 trivial lookup (≤ 3 files, no history) | yes | — |
| Bash for state (`git status`, file checks — read-only) | yes | — |

**Mandatory triggers** (once fired, delegate or tell the user why not):

1. **4-file rule**: understanding requires reading 4+ repo files → delegate.
2. **Long-session rule**: after 15 tool calls or 5 exploratory reads without delegating, pause and evaluate delegation.
3. **Incident rule**: after an accidental mutation, wrong working directory, or unexpected environment state, stop and audit before continuing.

**Anti-patterns**: accumulating 5+ inline reads to avoid a delegation · pasting artifact bodies into envelopes · delegating per file instead of per phase · continuing after an incident without auditing · re-analyzing what a digest already answers.

## Complexity Rubric

Evaluated once, at the close of the first interview round. Score three dimensions, 0–2 each:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Estimated surface (modules/dirs involved) | 1 | 2–3 | ≥ 4 |
| Material questions unresolved after round 1 | 0 | 1–2 | ≥ 3 |
| Cross-cutting concerns touched (auth, data model, external integrations) | 0 | 1 | ≥ 2 |

| Total | Band | Effect |
|---|---|---|
| 0–2 | `simple` | minimal analysis: use the `light` analyzer budget regardless of rigor |
| 3–4 | `standard` | normal flow at the configured rigor level |
| 5–6 | `complex` | raise `deep_interview_suggestion` (proactively when rigor is `deep`; never when rigor is `light`) |

Record the score and band as a decision in `state.yaml` (e.g. `complexity: standard (2+1+1)`).

## Interview Protocols

Interviews are orchestrator-executed. There is no interviewer worker.

### Inline interview (default)

Completeness rubric — what must be known before analysis starts:

- `bug-triage`: observed symptom, expected behavior, suspected area or trigger, reproducibility (known or explicitly unknown).
- `requirements-refinement`: business goal, affected users/flows, scope boundaries (in/out), known constraints.
- `code-consultation`: the concrete question, and the version/commit scope if historical.

Rules: max 3 questions per round, max 2 rounds inline; apply smart skip per `bp-user-interaction-contract.md`; facts already in `config.yaml` or state are never asked. Close = write `interview-notes.md`, apply state mutations, score the complexity rubric.

### Deep interview (parallel session)

When suggested (rubric `complex`) or requested by the user:

1. Raise `deep_interview_suggestion` once. If accepted, tell the user to open a dedicated session with: *"Continue the blueprint interview for objective `{slug}`"*.
2. That session loads `state.yaml` + `interview-notes.md`, runs a closed question loop, and **closes by formalizing**: decisions into `decisions[]`, facts into `interview-notes.md`, and `next_action` set to the next phase.
3. The main orchestrator resumes **only from persisted state** — never from the other session's chat. If state shows the deep interview is unfinished, wait or offer to continue inline.

## Worker Envelope

Per `bp-flow-contract.md`. Each delegation includes: skill id · objective slug, type, and phase · rigor level with its budget row · approved scope or the blocked question · artifact paths + digests · relevant `key_files` · the verbatim worker execution boundary · expected envelope fields. For bug-report exports, also include the digest `severity`, taken from the highest confirmed analysis finding. Never include artifact bodies, README content, or broad repo summaries.

## Result Processing Protocol

Process every returned envelope in this order:

1. **Verify writes**: `artifacts` must be `[]` for read-only workers (`bp-context-mapper`, `bp-analyzer`, `bp-diff-parser`, `bp-strategist`); for writer skills (`bp-doc-exporter`, `bp-handoff`, `bp-init`), only their owned paths (`bp-persistence-contract.md`). Any violation is an **incident**: stop, audit, distrust the output.
2. **Check `status`**: `success` → continue. `partial` → surface gaps and any `decision_required`. `blocked` → surface the reason; never work around a block without the user.
3. **Apply `state_mutations`** to `state.yaml` / `index.yaml` and persist worker output into the phase artifact (`analysis.md`, `alternatives.md`) with its digest.
4. **Check `context_resolution`**: if not `injected`, re-resolve context before the next delegation. Compare `artifact_digests_used` against current digests — a stale digest means the worker saw old evidence: re-run or flag it.
5. **Check `open_risks`**: `medium` and above → surface before routing; `low` → carry forward with a note.
6. **Validate `recommended_next_step`** against the routing table — a signal, not an override; on conflict follow the table and note the discrepancy.
7. **Relay any `user_message` verbatim**, then show a 3–5 line phase summary; in `interactive` wait for confirmation, in `auto` route immediately.

## Routing Tables

Common rows apply to every flow; then one table per flow. The table is the authority.

### Common

| Situation | Action | Approval | Notes |
|---|---|---|---|
| preflight `missing` or `incomplete` | `bp-init` | no | no flow may start |
| preflight `stale` | warn once, offer re-init update | no | continue allowed |
| no objective matches the request | create `objectives/{slug}/`, register in `index.yaml`, start inline interview | no | slug proposed from the request |
| request drifts from the recorded objective | `scope_change` checkpoint | yes | may spawn a new objective instead |
| user switches to a different objective type mid-flow | `scope_change` checkpoint → close this objective or open a new one | yes | flow-switch; never silently re-type |
| user aborts the objective | confirm once, set `lifecycle_status: closed`, update index | yes | abort; intermediates stay on disk |
| user wants the change built | `handoff_gate` → `bp-handoff`, then route to sdd-lite | yes | escalation valve; blueprint never implements |
| `bp-handoff` succeeded | `bp-doc-exporter` (`update-status`: `approved → handed-off`) on the source artifact | no | then relay the handoff `user_message` |
| a new final supersedes an older one for the same objective | `bp-doc-exporter` (`update-status`: `→ superseded`) on the old artifact | no | |
| objective resolved and user is done | set `lifecycle_status: closed`, update index | no | terminal |

### F1 — `bug-triage`

| Situation | Action | Approval | Notes |
|---|---|---|---|
| interview incomplete per rubric | continue inline interview | — | max 2 rounds, then `missing_context` |
| interview closed | `bp-context-mapper` | `phase_validation` (smart-skippable) | rubric scored here |
| mapper located the surface | `bp-analyzer` | no | analyzer budget from rigor × complexity band |
| mapper exhausted budget without locating | `missing_context` checkpoint | yes | never widen silently |
| analyzer returned findings | `bp-strategist` | no | root cause respects the evidence bar |
| strategist returned alternatives | present them; offer the export | no | |
| user accepts the export | `bp-doc-exporter` (`export`) → `bugs/bug-{slug}.md` (`draft`) | no | envelope carries digest `severity` |
| export returned a `draft` | `artifact_approval` checkpoint | yes | |
| `artifact_approval` approved | `bp-doc-exporter` (`update-status`: `draft → approved`) | no | sets `lifecycle_status: approved` |

### F2 — `requirements-refinement`

| Situation | Action | Approval | Notes |
|---|---|---|---|
| interview incomplete per rubric | continue inline interview | — | max 2 rounds, then `missing_context` |
| interview closed | `bp-context-mapper` | `phase_validation` (smart-skippable) | contrasts code **and** existing local workspace artifacts |
| mapper done | `bp-strategist` | no | |
| strategist needs deeper code evidence | `bp-analyzer`, then back to `bp-strategist` | no | one detour max per objective |
| alternatives presented, user picked | `bp-doc-exporter` (`export`) → `ideas/rfc-{slug}.md` (`draft`) | no | |
| export returned a `draft` | `artifact_approval` checkpoint | yes | |
| `artifact_approval` approved | `bp-doc-exporter` (`update-status`: `draft → approved`) | no | sets `lifecycle_status: approved` |
| RFC is `approved` and user wants it built | `handoff_gate` → `bp-handoff` | yes | seed to sdd-lite inbox; then the Common handed-off row |

### F3 — `code-consultation`

| Situation | Action | Approval | Notes |
|---|---|---|---|
| question or version scope unclear | continue inline interview | — | max 2 rounds, then `missing_context` |
| question answerable inline (≤ 3 files, no history) | answer inline in chat | no | no worker spawn |
| surface unknown or 4+ files | `bp-context-mapper` then `bp-analyzer` | no | |
| involves past versions or commits | `bp-diff-parser` first (target frozen by SHA) | no | then `bp-analyzer` if needed |
| answered | `audit_persist_offer` (once) | no | offer, never a gate |
| user accepts the offer | `bp-doc-exporter` → `audits/audit-{slug}.md` | no | |

## Lifecycle Transitions

The orchestrator is the only writer of `lifecycle_status`. Single source for when each value is set:

| Event | `lifecycle_status` |
|---|---|
| objective created and registered in `index.yaml` | `open` |
| first phase starts (interview) | `in_progress` |
| a required checkpoint is raised and pending | `awaiting_user` (back to `in_progress` on resolution) |
| `update-status` flip `draft → approved` completed | `approved` |
| `update-status` flip `approved → handed-off` completed | `handed_off` |
| objective resolved, aborted, or F3 answered and offer resolved | `closed` (terminal) |
| a `blocked` envelope with no immediate user path | `blocked` (back to `in_progress` when unblocked) |

Note: objective `lifecycle_status` uses snake_case (`handed_off`); artifact digest status uses hyphens (`handed-off`). They are different enums.

## Phase-Close Consolidation

At the close of interview, analysis, and strategy: apply mutations, write the phase artifact with an updated digest, update `index.yaml`, then suggest compacting the chat. What must survive a compaction: state, digests, and the next envelope — never full artifact bodies or chat history. This replaces any turn-count purge.

## Resume Rules

1. Resolve the objective from the user's reference, or the single unambiguous non-closed entry in `index.yaml`; otherwise ask.
2. Read its `state.yaml`; validate against artifact digests — digests win, repair state.
3. Resume at the first unresolved item: unresolved checkpoint → missing or stale owned artifact → `next_action` → close.

## Stop Conditions

Stop and consult the user when: a material contradiction exists between persisted artifacts and the current request · scope drift changes the objective's outcome or surface · the objective type itself changes · the user asks for implementation (escalation valve) · artifact recovery is ambiguous.

## Guardrails / Invariants

- Engine root is `.bp-harness/`; workspace root is `bp-workspace/`; both paths are fixed.
- **Read-only by effect class**: no command that changes source code, the working tree, git history, or any remote. No exceptions — blueprint never stages, commits, tags, or pushes. Permitted git commands are read-only: `log`, `show`, `diff`, `status`, `blame`.
- Writes follow the ownership table in `bp-persistence-contract.md`; any other write is an incident.
- Delegation is per phase, never per file; workers never spawn workers (execution boundary).
- Persisted content is English; chat follows `config.yaml.conventions.chat_language`.
- A resolved checkpoint is never re-asked; offers are made once.
- Resume and routing must be explainable from persisted state and digests alone.
