# blueprint-harness — User Guide

A practical guide to installing and using `blueprint-harness` day to day. For the design rationale see `blueprint-spec.md`; for a quick overview see `README.md`; for the internal mechanics with flow diagrams see `docs/`.

---

## Table of Contents

1. [What is blueprint-harness?](#1-what-is-blueprint-harness)
2. [When to use it (and when not to)](#2-when-to-use-it-and-when-not-to)
3. [Key concepts](#3-key-concepts)
4. [Setup (`bp-init`)](#4-setup-bp-init)
5. [The `config.yaml` file](#5-the-configyaml-file)
6. [Runtime file layout](#6-runtime-file-layout)
7. [The 7 skills](#7-the-7-skills)
8. [The three flows](#8-the-three-flows)
9. [How read-only is enforced](#9-how-read-only-is-enforced)
10. [Usage examples](#10-usage-examples)
11. [What NOT to do](#11-what-not-to-do)
12. [Handoff to sdd-lite](#12-handoff-to-sdd-lite)

---

## 1. What is blueprint-harness?

`blueprint-harness` is an agentic workflow for the **discovery phase** of software work: the thinking that happens *before* anyone decides to write code. It turns loose conversations into durable, structured artifacts:

- an idea becomes a reviewed **RFC** with evaluated alternatives,
- a bug report becomes a **triage document** with an evidence-backed root cause,
- a technical question becomes an answer — optionally persisted as an **audit**.

What it is **not**: an implementation tool. Blueprint never writes or modifies source code, never runs tests, never touches git state. When you decide something should actually be built, it produces a handoff seed for `sdd-lite` (or for whatever process you use) and stops there.

It runs inside your AI CLI (Claude Code, or any AGENTS.md-compatible agent). A thin orchestrator conducts the session; small read-only workers do the heavy reading; everything durable lives in a local `bp-workspace/` folder.

## 2. When to use it (and when not to)

### Use `blueprint-harness` when

- You want to **formalize an idea**: "I want to add caching to the product queries — help me write this up properly."
- You need a **bug diagnosed**, not fixed: "logins are failing with 500 since the last deploy — what's going on?"
- You have a **code or history question** worth a careful answer: "what changed in the auth module between v2 and v3?"
- You want an **architecture decision documented** with alternatives and risks before committing to it.

### Do NOT activate it for

- Actually implementing anything — that is `sdd-lite`'s job (or yours).
- Trivial questions the agent can answer from one file — the orchestrator answers those inline without ceremony.
- Editing documents you already wrote — blueprint generates its own artifacts from evidence, it is not a text editor.

### The bug routing rule

"I have a bug" is ambiguous between the two harnesses. The rule: **blueprint `bug-triage`** when you want understanding or a documented diagnosis; **sdd-lite `bug-fix`** when you want it fixed. When in doubt, triage first — its output hands off cleanly into a fix.

## 3. Key concepts

| Concept | Meaning |
|---|---|
| **Objective** | One unit of work (a bug to triage, an idea to refine, a question). Each gets its own folder `bp-workspace/objectives/{slug}/` with its own state — so a quick question never disturbs an open RFC. |
| **Workspace** | `bp-workspace/` — local, per-user, per-machine. Not meant for version control (your choice, though). Final documents you want to share, you export manually. |
| **Digest** | The small header block every artifact starts with (status, date, one-line summary). It is how the system resumes work without re-reading everything. |
| **Rigor** | `light` / `standard` / `deep` in `config.yaml` — how much evidence is required and how much analysis is allowed. |
| **Complexity rubric** | A 3-question score (surface, open questions, cross-cutting concerns) evaluated after the first interview round. It sets analysis depth and may suggest a deep interview. |
| **Checkpoint** | A structured question the orchestrator asks you (approve this RFC? persist this audit?). Answered checkpoints are recorded and never re-asked. |
| **Worker** | A fresh sub-agent that executes one phase (mapping, analysis, strategy…) with a hard budget, and returns a structured result. Analysis workers write nothing. |
| **Envelope** | The compact instruction package a worker receives, and the structured result it returns. You will not see them unless you ask. |

## 4. Setup (`bp-init`)

### Install

From your AI CLI, inside the target repo:

> Read `<package-path>/skills/bp-init/SKILL.md` and execute it, using `<package-path>` as the source package.

What it does:

1. Copies the engine to `.bp-harness/` (versioned via a `VERSION` file).
2. Creates `bp-workspace/` — config, empty index, artifact folders, and your own editable copies of the templates.
3. Detects your AI setups (`CLAUDE.md`/`.claude/` → Claude Code; `AGENTS.md`/`.agents/` → agents) and **copies** the `bp-*` skills into them.
4. Shows the wrapper block and, with your `[y/n]`, injects it into `CLAUDE.md`/`AGENTS.md` between idempotent markers.
5. **Offers** to write the read-only permission set into your platform settings (e.g. `.claude/settings.json`). Declining is fine — the set stays documented in the wrapper for manual application.
6. If `./sdd-lite/` exists, reuses its project identity instead of asking.

It asks **at most 2 questions** (which AI setups, only if several are detected; the permission offer). It **never touches `.gitignore`** — whether you commit `.bp-harness/`, `bp-workspace/`, or the skill copies is entirely your call (recommended: don't).

### Update

Re-run the same instruction. Same version → reports "up to date" and changes nothing. Newer package → offers an update that re-copies the engine and refreshes skill copies and wrapper blocks. `bp-workspace/` is always preserved, including any template you edited.

### Uninstall

Delete `.bp-harness/`, `bp-workspace/`, the `bp-*` folders under `.claude/skills/` / `.agents/skills/`, and the `<!-- bp-harness:start -->…<!-- bp-harness:end -->` block from `CLAUDE.md`/`AGENTS.md`.

## 5. The `config.yaml` file

Lives at `bp-workspace/config.yaml`, validated against `schemas/bp-config.schema.yaml`. The fields you may actually want to touch:

- **`product`** — name, business domain, optional glossary of domain terms the harness should use consistently. Seeded from sdd-lite when present; otherwise defaulted (edit it — better identity means better interviews).
- **`rigor_level`** — the depth dial:

| Level | Analysis budget | Alternatives | Root-cause bar | Deep interview |
|---|---|---|---|---|
| `light` | 1 pass, ≤ 4 files | max 2 | inferences allowed (labeled) | never suggested |
| `standard` (default) | 1–2 passes, ≤ 8 files | 2–3 | inference labeled, fact preferred | suggested when complexity is high |
| `deep` | ≤ 3 passes, ≤ 15 files | 3 + discarded | only deterministic evidence asserts | suggested proactively |

- **`conventions.chat_language`** — `es` or `en` for conversation. Persisted artifacts are **always English** (this keeps handoffs compatible and is not configurable).
- **`capabilities`** — what `bp-init` detected (`rg`, `gh`, AST tooling). Everything degrades gracefully when absent; `gh` is only ever used for PR metadata and never assumed.

## 6. Runtime file layout

```
bp-workspace/
├── config.yaml                 # settings (above)
├── index.yaml                  # one-line entry per objective — the resume anchor
├── objectives/{slug}/          # per-objective state + working notes
│   ├── state.yaml              #   phases, checkpoints, decisions, pointers
│   ├── interview-notes.md      #   what you told it (150–300 words)
│   ├── analysis.md             #   facts / inferences / unknowns (300–500)
│   └── alternatives.md         #   options + recommendation (300–500)
├── ideas/rfc-{slug}.md         # final RFCs (400–800 words)
├── bugs/bug-{slug}.md          # final bug reports (300–600)
├── audits/audit-{slug}.md      # persisted consultations (200–400)
└── templates/                  # YOUR editable export templates (never overwritten)
```

Every artifact opens with a digest. Finals carry a lifecycle status in it:

```
draft  →  approved  →  handed-off
                   ↘  superseded
```

`draft → approved` happens only when you approve the artifact at a checkpoint; `handed-off` only after a successful handoff. Audits skip `draft` — accepting the persist offer *is* the approval.

Word budgets are hard caps, not suggestions: they force the system to say less, better. If a document feels thin, raise `rigor_level` rather than expecting longer output.

## 7. The 7 skills

You never invoke these directly — the orchestrator routes to them. Knowing what each does helps you read the phase summaries:

| Skill | What it does for you | Writes |
|---|---|---|
| `bp-init` | Installs and updates the harness | setup files only |
| `bp-context-mapper` | Finds *where* in the repo your topic lives (≤ 6 files read) and checks your past local artifacts for overlaps | nothing |
| `bp-analyzer` | Reads the actual logic and returns findings labeled `fact` / `inference` / `unknown`, each with `file:line` proof | nothing |
| `bp-diff-parser` | Answers "what changed" questions from git history, frozen to exact SHAs, without dumping diffs | nothing |
| `bp-strategist` | Turns evidence into 2–3 architecture-level alternatives with risks, effort, and one recommendation | nothing |
| `bp-doc-exporter` | Fills your template with the accumulated evidence and writes the final document; also flips digest statuses after your approvals | finals only |
| `bp-handoff` | Writes the sdd-lite inbox seed from an approved artifact | the seed only |

The honesty rules are the point: a claim without proof is downgraded to inference; insufficient evidence becomes `unknown`, never a guess; style opinions are out of scope.

## 8. The three flows

At the start of a session the orchestrator asks once: **`interactive`** (pause after each phase for your OK — default) or **`auto`** (chain phases, stopping only at real decisions). Required checkpoints — approving an artifact, gating a handoff, resolving missing context — are never skipped in either mode.

### F1 — Bug triage

1. **Interview** (in chat, short): symptom, expected behavior, suspected area, reproducibility. Max 2 rounds; if you already gave the facts, it skips ahead.
2. **Mapping**: a worker locates the affected surface.
3. **Analysis**: a worker validates hypotheses against the real code and logs (log *files* or text you paste — nothing is executed).
4. **Strategy**: resolution alternatives with impact.
5. **Optional export**: with your approval, `bugs/bug-{slug}.md` — and optionally a handoff if you want it fixed.

### F2 — Requirements refinement

Same skeleton, different questions: business goal, affected flows, scope boundaries, constraints. Mapping also contrasts your **past local RFCs** so a new proposal doesn't contradict an old decision. Ends in `ideas/rfc-{slug}.md` after your `artifact_approval`, and optionally the handoff gate.

### F3 — Code consultation

The lightweight path. Trivial questions (≤ 3 files, no history) are answered inline with no workers at all. History questions go through the diff-parser first (frozen SHAs). After the answer you get a **one-time** offer to persist it as an audit — decline and it never asks again for that objective.

### The deep interview

When the complexity rubric scores your topic as complex (or you ask for it), the orchestrator suggests a **dedicated parallel session** for a longer interview. That session formalizes its conclusions into the objective's state and closes; your main session resumes from the recorded state, never from the other chat. Useful when the idea needs an hour of back-and-forth that would drown the working session.

### Resuming

Everything resumes from `bp-workspace/` — `index.yaml`, then the objective's `state.yaml`, then digests. Kill a session mid-flow, open a new one, say "continue with {slug}" — it picks up at the first unresolved item. Chat memory is never required.

## 9. How read-only is enforced

Three independent layers:

1. **Platform permissions** (strongest): the set `bp-init` offers — deny file writes outside `bp-workspace/`, the sdd-lite inbox, and the harness's own setup paths; allow only `git log/show/diff/status/blame`; deny every state-changing git command. Apply it and the guarantee is mechanical.
2. **Envelope boundary**: every worker is instructed read-only (or owned-paths-only) and forbidden from spawning sub-agents.
3. **Post-worker verification**: the orchestrator checks what every worker reports having written. An analysis worker that wrote *anything* is treated as an incident — the session stops and its output is distrusted.

There are **no git mutations, with no exceptions** — blueprint never stages, commits, tags, or pushes. If you see it attempt one, that is a bug: stop and report it.

## 10. Usage examples

### Example 1 — Diagnose a production bug

> **You:** Google login is returning 500 since Friday's deploy. Help me figure out why — don't fix anything yet.
> **Agent:** *(asks 2–3 interview questions: exact endpoint, expected behavior, any logs)*
> **You:** *(paste the stack trace)*
> **Agent:** *(maps the auth surface, analyzes)* Root cause hypothesis: null payload from `verifyIdToken` dereferenced without guard at `google.strategy.ts:54` (fact, log-confirmed); the deploy removed the `audience` option (fact); the linkage is inferential. Two resolution options… Export the bug report?
> **You:** yes
> **Agent:** *(writes `bugs/bug-google-login-500.md` as draft → you approve → approved)*

### Example 2 — RFC with handoff

> **You:** I want to formalize adding a cache layer to product queries.
> **Agent:** *(interview: goal, scale expectations, scope)* → *(maps repo + finds your old `rfc-read-replicas.md`, flags an overlap)* → *(presents alternatives A/B with the trade-off)*
> **You:** A. Approve it and send it to development.
> **Agent:** *(exports `ideas/rfc-query-cache-layer.md`, you approve, handoff gate)* Seed written to `sdd-lite/openspec/inbox/query-cache-layer.md`. Point sdd-lite at it to start the change.

### Example 3 — History question, kept

> **You:** What changed in the review skills over the last 10 commits?
> **Agent:** *(diff-parser, frozen at `5f8d83a`)* Summary: a full review subsystem was added in one commit… Want this persisted as an audit?
> **You:** yes → `audits/audit-review-skills-evolution.md` (born approved).

### Example 4 — Resume after a break

> **You (new session):** Continue with query-cache-layer.
> **Agent:** *(reads index + state)* RFC is `approved`, handoff gate unresolved. You were deciding whether to send it to development. Proceed?

## 11. What NOT to do

- **Don't ask it to fix things.** "Fix this bug" belongs to sdd-lite or to you; blueprint will offer the escalation valve instead of complying.
- **Don't fight the budgets.** If analysis stopped at 8 files, that's `standard` rigor working. Raise the rigor, don't ask it to "keep reading".
- **Don't expect shared memory.** The workspace is local to your machine. A teammate's blueprint knows nothing about yours; share final documents by exporting them wherever your team keeps docs.
- **Don't edit `state.yaml` or `index.yaml` by hand.** The orchestrator is their only writer; hand edits break resume. Your editable surface is `bp-workspace/templates/` and `config.yaml`.
- **Don't treat inferences as facts.** The labels exist so you can tell them apart; a `deep`-rigor run will refuse to assert what it can't prove.
- **Don't skip the interview by dumping a spec.** You can — smart skip will absorb it — but answer the follow-ups: they exist to catch what the spec didn't say.

## 12. Handoff to sdd-lite

The only coupling point between the two harnesses, and it is deliberately passive:

1. You approve an RFC or bug report (`artifact_approval` → status `approved`).
2. You confirm the **handoff gate**.
3. `bp-handoff` writes a self-contained seed — problem, scope sketch, feasibility signal, open questions — to `./sdd-lite/openspec/inbox/{slug}.md`, and the source artifact becomes `handed-off`.
4. **Consumption is manual and yours**: tell sdd-lite to start a change from that inbox file. Blueprint never modifies sdd-lite — no state files, no `changes/` writes, no skill patches.

If sdd-lite isn't installed in the repo, the handoff blocks with a clear message and writes nothing. The transition is one-way: once development starts, changes to scope happen in sdd-lite's artifacts, not by re-editing the RFC (open a new objective if discovery genuinely reopens).
