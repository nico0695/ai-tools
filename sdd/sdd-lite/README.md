# sdd-lite

Status: MVP ready for use.

`sdd-lite` is a separate package for a lighter SDD workflow.
It keeps the contract-first discipline of `sdd-v2` while reducing artifact volume, phase count, and operating cost for bounded changes.

This package is intentionally separate from `sdd-v2`.
It does not reuse a root-level `openspec/` directory and does not require runtime coexistence with `sdd-v2`.

## What It Is

Use `sdd-lite` when you want:

- explicit bootstrap before change work
- persisted source of truth instead of chat-memory dependence
- compact functional and technical formalization
- stage-by-stage execution with explicit approval before code work
- unified QA for stage review and final closeout
- a lighter lifecycle than `sdd-v2`

`sdd-lite` is meant for bounded work.
It is not a shortcut for large migrations, broad cross-cutting redesigns, or heavy governance workflows.

## When To Use It

Good fit:

- a local bug fix
- a bounded feature or enhancement
- a small or medium refactor
- a planner-only request that should stop after the plan
- a repo where you want resumable artifacts without the full weight of `sdd-v2`

Bad fit:

- migrations
- broad architectural redesign
- work that touches many subsystems with unclear blast radius
- requests with unresolved product or risk ambiguity that exceed lite governance
- workflows that need archive, PR, branch, or git-side-effect automation

When the work no longer fits lite safely, the correct outcome is:

- `macro-plan-first`, or
- `escalate-to-sdd-v2`

## Core Rules

- Bootstrap is mandatory before change routing.
- All runtime artifacts live under `./sdd-lite/`.
- `sdd-lite` never uses a root-level `openspec/`.
- Persisted files, contracts, schemas, templates, and generated Markdown stay in English.
- Chat interaction may be `es` or `en`.
- Every later stage requires explicit approval before it starts.
- `sddl-executor` must not perform hidden git side effects.
- `sddl-deep-explorer` is read-only.
- `sddl-qa-review` in `stage` mode never closes the change.
- Only `sddl-qa-review` in `final` mode may mark the change `completed`.
- Resume must be explainable from persisted state and artifacts, not from prior chat memory.

## Package Layout

```text
sdd/sdd-lite/
  README.md
  SDD_LITE_IDEA.md
  SDD_LITE_PLAN.md
  orchestrator/
    SDDL-ORCHESTRATOR.md
  skills/
    _shared/
      sddl-flow-contract.md
      sddl-persistence-contract.md
      sddl-user-interaction-contract.md
      sddl-project-standards-contract.md
    sddl-init/
      SKILL.md
    sddl-proposal-spec/
      SKILL.md
    sddl-design-plan/
      SKILL.md
    sddl-executor/
      SKILL.md
    sddl-deep-explorer/
      SKILL.md
    sddl-qa-review/
      SKILL.md
  templates/
    bootstrap/
      config.yaml
      project-context.md
      skill-catalog.md
    artifacts/
      proposal-spec.md
      design-plan.md
      execution-log.md
      qa-report.md
      macro-plan.md
  schemas/
    config.schema.yaml
    state.schema.yaml
```

## Runtime Layout

All runtime files live under `./sdd-lite/`:

```text
./sdd-lite/
  project-context.md
  skill-catalog.md
  openspec/
    config.yaml
    changes/
      {change-name}/
        state.yaml
        proposal-spec.md
        design-plan.md
        execution-log.md
        qa-report.md
        macro-plan.md            # only when explicitly needed and approved
```

## Current Package Status

The package currently has these completed stages:

- Stage 0: frozen runtime, language, interaction, naming, and closure decisions
- Stage 1: bootstrap surface, runtime scaffolding, and `sddl-init`
- Stage 2: shared lite contracts and schemas
- Stage 3: orchestration contract with routing, resume, gating rules, and on-demand `sddl-deep-explorer`
- Stage 4: compact formalization with `sddl-proposal-spec`, `sddl-design-plan`, and their artifact templates, including `macro-plan.md` for approved `macro-plan-first` flows
- Stage 5: controlled execution with `sddl-executor` and the resumable `execution-log.md` ledger
- Stage 6: unified QA review with `sddl-qa-review`, `stage` and `final` modes, and the reusable `qa-report.md` artifact
- Stage 7: hardening walkthroughs completed across bootstrap, resume, planner, oversized requests, contradiction-before-execution, and realistic staged-change flows

There is no further implementation stage in the MVP plan.

## Core Skills

| Skill | Role | Primary writes |
|---|---|---|
| `sddl-init` | bootstrap the repo for lite usage | `project-context.md`, `skill-catalog.md`, `openspec/config.yaml` |
| `sddl-proposal-spec` | compact functional formalization | `proposal-spec.md`, `state.yaml` |
| `sddl-design-plan` | technical design plus staged execution plan | `design-plan.md`, `state.yaml`, `macro-plan.md` when approved |
| `sddl-executor` | execute one approved stage at a time | repo files in approved scope, `execution-log.md`, `state.yaml` |
| `sddl-deep-explorer` | bounded read-only analysis | no persistent artifact by default |
| `sddl-qa-review` | stage review and final closeout | `qa-report.md`, `state.yaml` |

## Orchestrator Responsibilities

The orchestrator is the entry point.

It is responsible for:

- bootstrap preflight
- context loading
- route selection
- resume behavior
- stage handoff safety
- approval gating
- stop conditions

It is not responsible for:

- replacing `sddl-init`
- absorbing stage logic
- writing stage-owned artifacts
- assuming chat memory is trustworthy when persisted evidence exists

## Objectives And Routes

### Objectives

- `new-feature`
- `bug-fix`
- `planner`
- `refactor-rework`

### Routes

- `continue-lite`
- `macro-plan-first`
- `escalate-to-sdd-v2`

## Standard Flow

Normal flow:

```text
preflight
  -> sddl-init when bootstrap is missing or incomplete
  -> complexity assessment
  -> sddl-proposal-spec
  -> sddl-design-plan
  -> sddl-executor (one approved stage at a time)
  -> sddl-qa-review (stage) when useful
  -> sddl-executor / sddl-qa-review (stage) as needed
  -> sddl-qa-review (final)
```

Key points:

- `proposal-spec.md` owns scope and acceptance targets
- `design-plan.md` owns the execution plan
- `execution-log.md` owns implementation traceability
- `qa-report.md` owns review findings and final closeout evidence

## Alternative Flows

### Planner Flow

Use `planner` when the work should stop at formalization:

```text
preflight
  -> complexity assessment
  -> sddl-proposal-spec
  -> sddl-design-plan
  -> stop(planned)
```

In this flow:

- execution does not start
- QA does not auto-run
- `lifecycle_status` stops at `planned`

### Macro-Plan-First Flow

Use this when the work still belongs in lite, but direct execution would be unsafe:

```text
preflight
  -> complexity assessment = macro-plan-first
  -> sddl-proposal-spec
  -> macro_plan_review checkpoint
  -> sddl-design-plan
  -> stop(planned)
```

In this flow:

- `macro-plan.md` exists only after explicit approval
- the result is planning-only
- later execution needs a fresh approval cycle and may require reassessment

### Escalation Flow

Use `escalate-to-sdd-v2` when:

- the blast radius is too broad
- the request behaves like a migration or large redesign
- safety requires a richer lifecycle than lite provides

In this flow:

- lite routing stops
- the escalation reason is preserved in `state.yaml`
- lite must not pretend the work can continue safely inside `sdd-lite`

## Change Artifacts

| Artifact | Owner | Purpose |
|---|---|---|
| `project-context.md` | `sddl-init` | reusable project facts |
| `skill-catalog.md` | `sddl-init` internal helper | canonical lite skill catalog |
| `config.yaml` | `sddl-init` | runtime paths, stack, quality commands, bootstrap metadata |
| `state.yaml` | orchestrator plus active stage | operational memory for route, lifecycle, checkpoints, decisions, next action |
| `proposal-spec.md` | `sddl-proposal-spec` | functional scope, expected behavior, acceptance targets, risks |
| `design-plan.md` | `sddl-design-plan` | technical approach and staged plan |
| `execution-log.md` | `sddl-executor` | implementation history and stage-by-stage resume anchor |
| `qa-report.md` | `sddl-qa-review` | findings, evidence, verdict, next action |
| `macro-plan.md` | `sddl-design-plan` | approved decomposition for macro-plan-first work |

## Resume Model

`state.yaml` is the operational resume anchor.

Resume order is:

1. unresolved checkpoint
2. missing or stale owning artifact
3. next approved stage
4. planned or blocked stop state

The package should be able to resume from:

- pending approvals
- blocked contradictions
- macro-plan checkpoints
- planner stops
- partial execution progress
- final review states

## User Interaction Model

`sdd-lite` is intentionally interactive, but not chatty.

Rules:

- ask only when the answer changes scope, risk, route, recovery, or the next stage
- do not ask for facts already recoverable from persisted artifacts or repo reality
- require explicit approval before each later stage
- avoid micro-confirmations for obvious local choices

Checkpoint types include:

- `language_selection`
- `missing_context`
- `scope_change`
- `risk_review`
- `stage_approval`
- `macro_plan_review`
- `escalation_review`
- `final_review`

## Safety Rules

- `sddl-executor` must stop on contradiction, scope drift, or blast-radius expansion
- `sddl-executor` must not auto-run later stages
- `sddl-qa-review` must not edit code
- `stage` QA must not pretend to be final closeout
- `final` QA may close the change only on a clean `pass`
- stale bootstrap may not be ignored before risky code-touching execution
- persisted content stays English even when chat is Spanish

## How To Use `sdd-lite`

Recommended operating pattern:

1. Bootstrap the repo
   Run `sddl-init` once in the repo, or rerun it when bootstrap becomes stale.
2. Enter through the orchestrator
   Treat the orchestrator as the normal entry point for new work and resume.
3. Let the orchestrator choose the route
   Do not force execution before route and scope are explicit.
4. Formalize the change
   Use `sddl-proposal-spec` and `sddl-design-plan` before implementation.
5. Approve execution stage by stage
   `sddl-executor` should run only one approved stage at a time.
6. Review proportionally
   Use `sddl-qa-review` in `stage` mode when a stage deserves structured review and in `final` mode at closeout.
7. Resume from artifacts, not from memory
   When interrupted, recover the next safe move from `state.yaml` and the owning artifacts.

## How It Should Not Be Used

Do not use `sdd-lite` like this:

- jumping directly into `sddl-executor` without proposal and design artifacts
- treating `stage` QA as if it were final completion
- using `macro-plan-first` as implicit approval to implement
- forcing oversized work to stay in lite after the orchestrator recommends escalation
- writing runtime artifacts outside `./sdd-lite/`
- letting git side effects happen implicitly

## Relationship To `sdd-v2`

`sdd-lite` keeps the backbone of `sdd-v2`, but compresses the lifecycle:

| `sdd-v2` tendency | `sdd-lite` equivalent |
|---|---|
| more phases and artifacts | fewer phases and artifacts |
| separate stage QA and final verify | one `sddl-qa-review` skill with `stage` and `final` modes |
| heavier lifecycle for serious or broad work | bounded lifecycle for local or decomposable work |
| stronger full-process governance | faster flow with explicit escalation when safety drops |

Use `sdd-lite` first for bounded work.
Escalate to `sdd-v2` when the lite route is no longer safe.

## Hardening Conclusion

Stage 7 walkthroughs passed for:

- bootstrap from thin context
- resume from persisted state
- `planner` terminal behavior
- oversized request handling
- contradiction-before-execution handling
- realistic staged code changes
- realistic low-risk non-code changes

The package is ready to use as an MVP.

## Remaining Non-Blocking Gaps

- there is no worked example change directory under `./sdd-lite/openspec/changes/`
- there is no automated consistency check across contracts, templates, and schemas
- host-specific wrappers and usage examples are still lighter than the ones in `sdd-v2`

These are follow-up improvements, not missing core flow behavior.
