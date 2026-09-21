# blueprint-harness

Read-only agentic harness for the **discovery phase** of a product: formalize requirements into RFCs, triage bugs (diagnose, never fix), answer code/history questions, and audit changes — with an optional one-way handoff seed into `sdd-lite` for implementation.

Sibling of `sdd-lite`, deliberately smaller: thin orchestrator, single source per rule, hard budgets (worker launch stack ~1.000–1.200 tokens), workers that never write, and one writer per artifact.

- Design reference: `blueprint-spec.md` (v1, frozen). At runtime the engine files are normative.
- How it works: `docs/` — engine mechanics, the three flows with diagrams, skills/templates and customization.
- Planning history: `planning/` (analysis, macro plan, tracker).

## Package layout

```
orchestrator/BP-ORCHESTRATOR.md   # event loop, routing tables, interview protocols
skills/bp-*/SKILL.md              # 7 skills (init, context-mapper, analyzer, diff-parser,
                                  #   strategist, doc-exporter, handoff)
skills/_shared/                   # 4 contracts + sdd-lite mapping
schemas/                          # bp-config, bp-state (JSON Schema in YAML)
templates/                        # artifacts, wrappers, bootstrap seed
docs/                             # how it works: mechanics, flows, customization
VERSION
```

## Install (manual)

From your AI CLI (e.g. Claude Code) **inside the target repo**:

1. Tell the agent:
   > Read `<this-package-path>/skills/bp-init/SKILL.md` and execute it, using `<this-package-path>` as the source package.
2. `bp-init` will: copy the engine to `.bp-harness/`, create `bp-workspace/` (config, templates, index), copy the `bp-*` skills into `.claude/skills/` / `.agents/skills/` (detected setups), inject the wrapper block into `CLAUDE.md`/`AGENTS.md` (with preview + confirmation), and **offer** to write the read-only permission set into your platform settings.
3. It asks at most 2 questions and **never touches `.gitignore`** — whether you commit `.bp-harness/`, `bp-workspace/`, or the skill copies is your choice (recommended: don't).

**Update**: re-run the same instruction. Same version → no-op. Newer package version → offers an update that re-copies the engine and refreshes skill copies/wrappers, always preserving `bp-workspace/` (your templates included).

**Uninstall**: delete `.bp-harness/`, `bp-workspace/`, the `bp-*` copies under `.claude/skills/` / `.agents/skills/`, and the `<!-- bp-harness:start -->…<!-- bp-harness:end -->` block from `CLAUDE.md`/`AGENTS.md`.

## Use

Once installed, talk to your agent normally:

- **F1 `bug-triage`** — "why does login return 500?" → inline interview → surface mapping → deep analysis (facts vs inferences with `file:line` proof) → resolution alternatives → optional `bugs/bug-{slug}.md`.
- **F2 `requirements-refinement`** — "I want to add caching to queries" → interview → mapping (contrasts your past local RFCs) → architecture alternatives → `ideas/rfc-{slug}.md` → optional handoff seed to `./sdd-lite/openspec/inbox/`.
- **F3 `code-consultation`** — "what changed in auth since v2?" → history pre-processing (frozen SHAs) → inline answer → one-time offer to persist as `audits/audit-{slug}.md`.

Session mode is asked once: `interactive` (pause per phase) or `auto` (chain, stopping only at required checkpoints). Depth is set by `rigor_level` in `bp-workspace/config.yaml` (`light`/`standard`/`deep`) and a quantitative complexity rubric. Everything resumes from `bp-workspace/` state — never from chat memory.

Hard rules: blueprint never modifies source code, git state, or sdd-lite; workers write nothing; only `bp-doc-exporter` writes finals; persisted artifacts are English.

## Field-testing checklist (first real use)

The engine was validated statically (cross-consistency audit) and per-piece (worker/exporter/init/handoff dry-runs). The full live loop is validated by your first real usage — check these off as you go:

- [ ] F1 end-to-end on a real bug: interview feels short (≤ 2 rounds), analyzer respects its file budget, bug report is honest about facts vs inferences.
- [ ] F2 end-to-end: RFC leaves `draft` only after your `artifact_approval`; handoff seed appears in `./sdd-lite/openspec/inbox/` and sdd-lite can start a change from it when you point it there.
- [ ] F3: trivial question answered inline without spawning workers; audit offer appears exactly once.
- [ ] Resume: close the session mid-F2, open a new one, ask to continue — it must resume from `state.yaml`/digests alone.
- [ ] Concurrency: run an F3 while an F2 objective is open — the F2 state must be untouched.
- [ ] Update: re-run bp-init after bumping the package VERSION — workspace and your edited templates must survive.
- [ ] Incident handling: if any worker ever reports written files, the orchestrator must stop and flag it — report this if you see it.

File an issue (or just tell the agent) for anything that deviates — the tracker in `planning/blueprint-tracker.md` has the full decision history.
