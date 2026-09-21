---
name: bp-init
description: |
  Installer and updater for blueprint-harness in a target repo. Copies the
  engine to .bp-harness/, creates bp-workspace/, seeds config and templates,
  copies bp-* skills into detected AI setups, injects wrappers, and offers the
  read-only permission set. Bootstrap-only: it never creates objectives and
  never modifies .gitignore.
  Triggers on: "bp init", "install blueprint", "instalar blueprint", re-init/update requests.
---

# bp-init

You are the installer for `blueprint-harness`. Source package: the directory this skill was installed from (contains `VERSION`, `orchestrator/`, `skills/`, `schemas/`, `templates/`).

## Owned writes (nothing else, ever)

`.bp-harness/` (engine copy) · `bp-workspace/config.yaml` · `bp-workspace/templates/` (first seed only) · workspace directories · skill copies under `.claude/skills/` and `.agents/skills/` · wrapper blocks in `CLAUDE.md`/`AGENTS.md` (confirmed) · platform permission settings (confirmed). **Never** `.gitignore`, never source code, never `bp-workspace/` content beyond config and the first template seed. Whether the user commits any of this is their responsibility — mention it once in the final summary, take no action.

## Workflow

1. **Preflight.** If `.bp-harness/VERSION` exists (it is the authority over `config.yaml.engine.version` when they disagree), compare with the package `VERSION`:
   - equal → report "already installed, up to date"; offer only to repair missing pieces. A repair run with nothing missing is a **no-op**: do not re-probe capabilities, do not rewrite anything.
   - different → **offer the update** in one line; on yes, **update mode**: re-copy the engine (step 3), refresh skill copies (step 5) and wrapper blocks (step 6, without re-asking — consent is recorded in `ai_setups`), and update `config.yaml` `engine.*` plus the refreshed `ai_setups` timestamps. Never touch the rest of `bp-workspace/`. `bp-workspace/templates/` is user-owned: never overwritten, in any mode.
2. **Context reuse.** If `./sdd-lite/project-context.md` or `./sdd-lite/openspec/config.yaml` exist, read project identity (name, stack, domain hints) from them and do not re-ask. Record `sdd_lite_integration` (present, runtime_root, inbox_path). With no context source, default `product.name` to the repo directory name and `domain` to `"not established (edit bp-workspace/config.yaml)"` — never ask.
3. **Engine copy.** Copy **only** `orchestrator/`, `skills/` (incl. `_shared/`), `schemas/`, `templates/`, and `VERSION` to `.bp-harness/`, replacing any prior copy. Never spec or planning docs.
4. **Capability detection.** Probe availability of `rg`, `gh` (authenticated), and AST tooling, with `checked_at`; hold for the config build in step 8. Absence is fine — every consumer has a documented fallback.
5. **AI setups.** Detect: `CLAUDE.md` or `.claude/` → `claude_code`; `AGENTS.md` or `.agents/` → `agents`. More than one detected → ask **one** question: which to configure (`all` recommended). **None detected → skip steps 5–7**, install engine + workspace only, and say so in the summary. For each configured setup, **copy** every `.bp-harness/skills/bp-*/` directory (including `_shared/`) into `.claude/skills/` / `.agents/skills/`. Copies are refreshed on every update. Hold `ai_setups` for step 8.
6. **Wrapper injection.** For each configured setup, read `templates/wrappers/claude-orchestrator.md` or `agents-orchestrator.md`, resolve `<generated_at>` and `<version>` (from the package `VERSION`), show the block, ask `[y/n]`, and inject between `<!-- bp-harness:start -->` / `<!-- bp-harness:end -->` markers in `CLAUDE.md` / `AGENTS.md`. **Re-run detection matches the marker prefix `<!-- bp-harness:start`** (attributes may follow): replace the existing block (no re-ask in update mode); append only when no marker prefix is found; create the file if absent. If declined, print the block for manual pasting.
7. **Permission offer (confirmed).** Only when at least one setup is configured. Show the recommended read-only permission set from the wrapper's "Read-only enforcement" section and offer to write it into the platform's settings (e.g. `.claude/settings.json` permissions). If declined, it stays documented in the wrapper — say so and move on. Never write settings without an explicit yes.
8. **Workspace.** Create `bp-workspace/` with `objectives/`, `ideas/`, `bugs/`, `audits/`; seed `config.yaml` from `templates/bootstrap/config.yaml` (validated against `schemas/bp-config.schema.yaml`, timestamps and detections filled); seed `bp-workspace/templates/` from `templates/artifacts/` **only if the directory does not exist**; create an empty `index.yaml` (`objectives: []`).
9. **Summary.** Report: engine version installed/updated, AI setups configured, skills copied, wrappers injected, permissions written or documented, capabilities detected, and the one-line note that versioning `.bp-harness/`, `bp-workspace/`, and the skill copies is the user's choice.

## Question budget

Maximum 2: (a) which AI setups, only when more than one is detected; (b) the permission offer, only when a setup is configured. Wrapper `[y/n]` confirmations are real asks but do not count against the budget. Everything else uses smart defaults.

## Validation

Before finishing, verify: `.bp-harness/VERSION` readable · `config.yaml` validates against the schema · every copied skill directory contains its `SKILL.md` · wrapper markers appear exactly once per injected file · `bp-workspace/templates/` untouched when it pre-existed · `.gitignore` untouched.

## Expected output

A result envelope per `bp-flow-contract.md` with `artifacts` listing every path written. On clean success: `next_action: "installation complete — nothing pending"` (prose), `open_risks: []` (list declined offers, e.g. unenforced permissions, as risks). Use `partial` when a step was declined or skipped (say which). Use `blocked` when the source package is unreadable or a target file cannot be written.
