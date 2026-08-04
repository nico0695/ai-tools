# `blueprint-harness` — Specification v1

> Status: **frozen for first implementation** (2026-08-03).
> Supersedes `planning/blueprint-initial-idea.md`. Decision log: `planning/blueprint-analysis.md` (D1–D12). Implementation plan: `planning/blueprint-macro-plan.md`.
> This spec is the **design reference**. Once built, the engine files (orchestrator, contracts, skills) are the normative source at runtime — each rule lives in exactly one engine file; this document describes the system, it does not duplicate runtime rules.

---

## 1. Identity and scope

`blueprint-harness` is an agentic harness for the **discovery, ideation, and diagnosis** phase of a product. It is the read-only sibling of `sdd-lite`: it formalizes requirements, triages bugs, answers code questions, and audits repository history — and hands approved work off to `sdd-lite` for implementation.

- **In scope:** requirement formalization (RFCs), bug triage (root-cause diagnosis, not fixing), code consultation, historical audit (as an optional persistence of consultations).
- **Out of scope:** writing or modifying source code, running tests or builds, executing anything that mutates the repository, the working tree, or any remote.
- **Execution boundary:** strictly read-only over source code and version history. The only write surface is `bp-workspace/` (plus the `sdd-lite` inbox during handoff, and confirmed setup writes during init).
- **Environment autonomy:** advanced CLI tools (`rg`, `gh`, AST parsers) are used when detected by `bp-init`; every capability has a documented fallback to standard LLM reading. `gh` (PR access) is optional and never assumed.

### Naming

| Concept | Name |
|---|---|
| Harness | `blueprint-harness` |
| Skill prefix | `bp-` |
| Engine (embedded, immutable) | `.bp-harness/` |
| Workspace (mutable) | `bp-workspace/` |
| Objective types | `bug-triage`, `requirements-refinement`, `code-consultation` |

`bug-triage` (not `bug-fix`) avoids colliding with the `sdd-lite` objective of the same name: blueprint diagnoses, sdd-lite fixes. The routing rule between harnesses lives in the wrappers (§10).

---

## 2. Topology

### 2.1. Engine

The source package lives in `ai-tools/sdd/blueprint-harness/`. `bp-init` copies it into the target repo as `.bp-harness/`, stamped with a `VERSION` file. Re-running `bp-init` on an existing copy detects the version and offers an update (re-copy of the engine, **always preserving `bp-workspace/`**, user templates included).

```
.bp-harness/
├── VERSION
├── orchestrator/
│   └── BP-ORCHESTRATOR.md          # event loop, routing tables, protocols
├── skills/
│   ├── bp-init/
│   ├── bp-context-mapper/
│   ├── bp-analyzer/
│   ├── bp-diff-parser/
│   ├── bp-strategist/
│   ├── bp-doc-exporter/
│   ├── bp-handoff/
│   └── _shared/                    # 4 contracts + sdd-lite mapping doc
├── schemas/
│   ├── bp-config.schema.yaml
│   └── bp-state.schema.yaml
└── templates/
    ├── artifacts/                  # seeds for workspace templates
    ├── wrappers/                   # claude-orchestrator.md, agents-orchestrator.md
    └── bootstrap/                  # config.yaml seed
```

Note: there is **no `bp-chat-interviewer` skill**. Interviewing is an orchestrator-executed protocol (§6.3), following the pattern proven by sdd-lite's review protocols.

### 2.2. Workspace

`bp-workspace/` is local, per-user tooling. Keeping it (and `.bp-harness/`) out of version control is the recommended default, but **it is the user's responsibility — `bp-init` never modifies `.gitignore`** (nor any repo file outside its owned writes). Artifacts are local to the user's machine; final documents are exported elsewhere manually by the user. The institutional memory that `bp-context-mapper` indexes is therefore whatever exists in the *local* workspace — never assumed to be shared across machines or teammates.

```
bp-workspace/
├── config.yaml                     # product identity, glossary, rigor, language, capabilities
├── index.yaml                      # global objective index (one line-sized entry each)
├── objectives/
│   └── {slug}/                     # one directory per objective (concurrent-safe)
│       ├── state.yaml              # per-objective operational state
│       ├── interview-notes.md      # intermediates, skill-owned, digest-first
│       ├── analysis.md
│       └── alternatives.md
├── ideas/                          # final RFCs            (rfc-{slug}.md)
├── bugs/                           # final bug reports     (bug-{slug}.md)
├── audits/                         # persisted audits      (audit-{slug}.md)
└── templates/                      # user-owned export templates (seeded once by bp-init, never overwritten)
```

- Slugs: `^[a-z0-9]+(?:-[a-z0-9]+)*$`, no dates in names (dates live in digests).
- Final artifacts carry a lifecycle status in their digest: `draft → approved → handed-off | superseded`.
- Working knowledge lives in `objectives/{slug}/` intermediates; final documents in the top-level category directories. `index.yaml` tracks every objective: slug, type, lifecycle status, last update, one-line digest.

---

## 3. State and contracts

### 3.1. `config.yaml` (global, per repo)

Defined by `schemas/bp-config.schema.yaml`. Holds: product identity and business domain, glossary, `rigor_level` **with operational semantics** (each level defines concrete depth: analysis budgets, number of alternatives, evidence bar), chat language (`es|en`), `engine_version`, detected capabilities (`rg`, `gh`, AST) with fallbacks, and `sdd_lite_integration` (detected paths). If `./sdd-lite/project-context.md` or its `config.yaml` exist, `bp-init` reads them and does not re-ask project identity.

### 3.2. `state.yaml` (one per objective)

Defined by `schemas/bp-state.schema.yaml`. One file per `objectives/{slug}/`, so a quick `code-consultation` never clobbers an open `requirements-refinement`. Holds: objective slug and type, lifecycle status (enum with documented valid transitions), current phase, typed `checkpoints[]` and `decisions[]` (mirroring sdd-lite shapes, including recommended options and recorded responses), `key_files[]` pointers, `artifacts{}` with digests, `next_action`, timestamps. Schema discipline: **no field enters the schema without a flow that writes it and a flow that consumes it.**

### 3.3. Result envelope (every skill returns it)

Defined once in `_shared/bp-flow-contract.md`:

- Required: `status` (`success | partial | blocked`), `executive_summary`, `artifacts` (must be empty for read-only workers), `next_action`, `open_risks`.
- Optional: `user_message`, `state_mutations`, `findings`, `decision_required` + `decision_options`, `context_resolution` (`injected | fallback | none`), `artifact_digests_used`, `recommended_next_step`.

Rules:
- **`state_mutations` are applied by the orchestrator only.** Skills never write `state.yaml`, `index.yaml`, or any state file. The orchestrator is the single writer of state.
- Every delegation envelope carries the literal **worker execution boundary**: workers execute one phase, never launch sub-agents, never orchestrate further steps.
- Workers receive pre-resolved context injected by the orchestrator (paths + short digests, never artifact bodies, never README). Reading contracts directly is a fallback, and `context_resolution` reports when it happened so the orchestrator re-resolves before the next delegation.

### 3.4. Persistence rules

- **Digest-first:** every artifact opens with a flat-field digest (status, date, key facts). Digests are the anchor for routing and resume; format is fixed in `_shared/bp-persistence-contract.md`.
- **Language:** persisted artifacts, keys, and structured values are always **English**; chat may be `es` or `en`. Changing chat language never changes artifact language (handoff compatibility with sdd-lite).
- **Budgets** (finalized in the persistence contract; targets): interview-notes 150–300 words, analysis 300–500, alternatives 300–500, RFC 400–800, bug report 300–600, audit 200–400, handoff seed 200–400. The four shared contracts together stay under ~1,500 words; each SKILL.md under ~150 lines.

### 3.5. Findings contract

`_shared/bp-findings-contract.md` defines the single severity model shared by all flows, `evidence_class: deterministic | inferential`, output classified as `fact / inference / unknown`, and the precision gate: when evidence is insufficient, the answer is `unknown` — silence over speculation. Bug triage and audits must not report smoke.

---

## 4. Skill catalog

Skills operate by capability, not by flow. All analysis skills are **read-only workers**: they write nothing; the orchestrator persists their results.

| Skill | Capability | Key constraints |
|---|---|---|
| `bp-init` | Install/update engine copy, detect AI setups and capabilities, create workspace, seed config and templates, copy skills into `.claude/`/`.agents/`, inject wrappers | Max ~2 questions; smart defaults; skills installed by **copy**; offers (confirmed) to write the read-only permission set into platform settings; never overwrites `bp-workspace/templates/`; never modifies `.gitignore` |
| `bp-context-mapper` | Shallow topology scan: file/function names, structural dependencies; indexes existing local workspace artifacts | Hard budget: ≤ 6 files read; escalates explicitly to `bp-analyzer` when insufficient |
| `bp-analyzer` | Deep bounded inspection of module logic, log files, syntax trees | Budget declared in its envelope; "logs" = repo files or user-pasted text, never execution; output classified per findings contract |
| `bp-diff-parser` | Git history pre-processor: isolates changed files and method signatures between commits | Allowlist: `git log/show/diff` (read-only); target frozen by SHA before analysis; PRs only if `gh` capability detected |
| `bp-strategist` | Feasibility modeling, trade-off comparison, high-level architecture alternatives | Consumes intermediates by digest; produces `alternatives.md` (2–3 options, risks, relative effort, marked recommendation); depth modulated by `rigor_level` |
| `bp-doc-exporter` | Fills a user-owned template from `bp-workspace/templates/` using the objective's intermediates; also flips digest statuses via its `update-status` mode when the orchestrator confirms a checkpoint | Stays within word budget; never invents sections; sets digest status (`draft`, then `approved` after user checkpoint; audits born `approved`) |
| `bp-handoff` | Translates an approved artifact into an sdd-lite inbox seed | Fires only after `handoff_gate` on an `approved` artifact; marks it `handed-off`; informs (never creates) if sdd-lite is absent |

---

## 5. Orchestrator (`BP-ORCHESTRATOR`)

A minimal event loop: read minimal persisted evidence (index, objective state, digests) → decide next step from the routing table → build a pre-resolved envelope → dispatch → process the result. It does not read broad docs at runtime.

### 5.1. Guardrails

- **Mutation block, by effect class:** any command that changes source code, the working tree, git history, or a remote is out — the class matters, not an enumerated list. The only permitted writes are the orchestrator's own writes inside `bp-workspace/` (and the handoff seed).
- **Post-worker verification:** a worker whose result reports created or updated files is an **incident** — stop, audit, distrust its output.
- **Delegation by cost, not by turn count:** inline execution for trivial lookups; delegate to a worker when the step needs multiple files, deep reading, or history processing (thresholds fixed in the orchestrator's delegation table). The old "one skill per inference turn" rule is dropped.
- **Consolidation by phase checkpoint** (replaces the 20-turn purge): at the close of each phase (interview closed, analysis closed, strategy closed) the orchestrator persists state + digests and suggests compacting; what survives is state, digests, and the next envelope — never chat memory. Resume must be explainable from persisted state alone.

### 5.2. Routing

One routing table per flow (F1/F2/F3), format `Situation | Next skill or action | Approval required | Notes`, including abort, flow-switch, and escalation rows. The table is the authority; a worker's `recommended_next_step` is a signal, not an override. A quantitative complexity rubric (measurable thresholds: affected files, modules, declared uncertainty) decides analysis depth and deep-interview suggestion — never "judge the blast radius".

**Escalation valve:** when discovery reveals the user actually wants a change implemented, the orchestrator closes the blueprint objective (optionally via handoff) and routes to sdd-lite. Blueprint never implements.

### 5.3. Interview protocols (D1)

- **Inline interview (default):** executed by the orchestrator itself. A completeness rubric per objective type defines what must be known before analysis starts; bounded questions per round; smart skip (if the user already provided the answer or said to proceed, record as implicitly approved and move on); closes by consolidating into `interview-notes.md` + `state.yaml`.
- **Deep interview (parallel session):** for complex cases (per the complexity rubric) the orchestrator *suggests* — or the user requests — a dedicated parallel conversation with a closed question loop. Its closing contract: it formalizes all conclusions into the objective's `state.yaml` (+ `interview-notes.md`). The main orchestrator resumes **only from persisted state**, never from the other session's chat.

### 5.4. Checkpoints

Typed, persisted in `state.yaml`, defined in `_shared/bp-user-interaction-contract.md`. Minimum set: `missing_context`, `scope_change`, `phase_validation`, `artifact_approval`, `handoff_gate`, `audit_persist_offer`, `deep_interview_suggestion`. Standard shape: short summary + concrete question + 2–4 options + one recommended + free-form allowed. Offers (audit persist, handoff) are made **once**, never block, and the response is recorded as a decision. A resolved checkpoint is never re-asked.

---

## 6. Flows

All three flows share the same skills; only routing differs. Every flow starts by creating (or resuming) an `objectives/{slug}/` entry.

### F1 — `bug-triage`

Diagnose without touching code. 1. Inline diagnostic interview (symptoms, reproducibility, suspected area). 2. `bp-context-mapper` locates the affected surface. 3. `bp-analyzer` validates hypotheses and isolates root cause (facts vs. inferences). 4. `bp-strategist` evaluates resolution alternatives and impact. 5. Optional close: `bp-doc-exporter` → `bugs/bug-{slug}.md`; optional `bp-handoff` if the user wants the fix implemented.

### F2 — `requirements-refinement`

New functionality and technical-debt refactors, unified. 1. Inline interview validates scope and business goal. 2. `bp-context-mapper` contrasts against current code and existing local workspace artifacts. 3. `bp-strategist` proposes architecture alternatives and risks. 4. `bp-doc-exporter` → `ideas/rfc-{slug}.md` after `artifact_approval`. 5. Optional `bp-handoff` after `handoff_gate`.

### F3 — `code-consultation`

Oracle mode for fast technical questions. 1. Ingest the question. 2. `bp-diff-parser` pre-processes history when past versions are involved. 3. `bp-analyzer` (or inline reading, per the delegation table) resolves the logic. 4. Answer inline in chat. 5. **Audit offer** (`audit_persist_offer`, once): persist the consultation as `audits/audit-{slug}.md` via `bp-doc-exporter`. There is no dedicated audit flow in the MVP.

---

## 7. Templates and deliverables

Engine seeds in `templates/artifacts/`; `bp-init` copies them once to `bp-workspace/templates/`, which is **user-owned** from then on (re-init never touches it). Every template opens with its digest block.

- Intermediates: `interview-notes.md`, `analysis.md`, `alternatives.md`.
- Finals: `rfc.md` (`## Decision Digest`), `bug-report.md` (`## Triage Digest`), `audit.md` (`## Audit Digest`).
- Handoff: `handoff-seed.md` — content aligned with sdd-lite's `proposal.md` template (problem and desired outcome, scope sketch, feasibility signal, open questions), so `sddl-proposal` can consume it without reinterpretation.

---

## 8. Handoff to sdd-lite (D3: inbox/seed)

One-directional transition to execution.

- **Trigger:** explicit user approval (`handoff_gate`) of an `approved` RFC or bug report.
- **Action:** `bp-handoff` writes `./sdd-lite/openspec/inbox/{slug}.md` from `handoff-seed.md`.
- **Consumption:** manual and outside blueprint's responsibility — the user points sdd-lite at the seed (e.g. "start a change from `openspec/inbox/{slug}.md`"). Blueprint never modifies sdd-lite in any way: no patches to its skills, no writes into `changes/`, no touching its ownership or schemas. The inbox file is the entire interface.
- **Close:** the source artifact is marked `handed-off`; the user is told the package is ready for the development orchestrator.
- **Fallback:** if `./sdd-lite/` is missing or uninitialized, inform the user and stop — never create it.

---

## 9. Enforcement (D7)

Read-only is enforced in three layers, not by prompt alone:

1. **Platform permissions in wrappers:** deny Edit/Write outside `bp-workspace/`, `./sdd-lite/openspec/inbox/`, and `bp-init`'s setup paths (`.bp-harness/`, skill copies, wrapper files, settings — so re-init/update keeps working); allowlist read-only git commands.
2. **Envelope boundary:** every worker envelope states read-only + no sub-agents.
3. **Post-worker verification:** the orchestrator's result processing treats any reported write by a worker as an incident (§5.1).

---

## 10. Multi-AI integration

Single platform-agnostic `BP-ORCHESTRATOR.md`; thin per-platform wrappers (`claude-orchestrator.md` for `CLAUDE.md`, `agents-orchestrator.md` for `AGENTS.md`) injected between idempotent markers `<!-- bp-harness:start -->` / `<!-- bp-harness:end -->`, with explicit preview and confirmation. Wrappers define:

- How to launch workers on that platform (native sub-agents vs. inline-sequential, with documented degradation: inline mode compresses context between steps — keep state, decisions, next envelope; drop artifact bodies).
- The read-only permission set (§9).
- **Cross-harness routing:** "I have a bug" → blueprint `bug-triage` when the user wants diagnosis/understanding; sdd-lite `bug-fix` when the user wants it fixed. When in doubt, triage first — its output hands off cleanly.

---

## 11. Relationship to sdd-lite (D9, D12)

- Contracts are **blueprint-owned** (`bp-*`) but mirror sdd-lite vocabulary (envelope shape, checkpoint types, severity model, English-artifacts rule). `_shared/sdd-lite-mapping.md` records the correspondence. Physical sharing (`sdd/_shared/`) is deferred until both stabilize.
- `bp-init` reads sdd-lite's bootstrap (project context, config) when present instead of re-asking.
- Division of labor: blueprint owns everything before the decision to build; sdd-lite owns everything after. The inbox is the only coupling point.
