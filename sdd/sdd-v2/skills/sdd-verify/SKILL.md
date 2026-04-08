# sdd-verify

You are the final verification phase for SDD v2.

## Goal

Validate the implemented change as a whole against its formalization and execution record, then produce an evidence-backed verdict that determines whether the change can move toward archive or must return for correction.

This phase is change-wide and evidence-heavy.
It is stronger and broader than `stage-qa`.

## Scope

This phase should:
- verify the full implemented change, not only the latest batch
- reconcile actual code and outputs against `proposal.md`, `tasks.md`, and available `spec.md` / `design.md`
- use project quality commands from `openspec/config.yaml`
- write `verify-report.md` with a command summary, compliance matrix, evidence log, open issues, and final verdict
- update `state.yaml` with operational verification status, evidence summary, and next recommended action

This phase should not:
- modify application code as part of normal verification
- rewrite upstream planning artifacts
- replace `stage-qa`
- archive the change

## When to use

Use this phase:
- after implementation work is complete for a non-`planner` flow
- before an implemented change can move to archive
- even if `stage-qa` already passed

This phase is mandatory when code changed.
For implementation flows that changed only documentation or configuration, this phase still produces a final verify verdict, but the command plan may be narrower.

## Reads

Read:
- `openspec/changes/{change-name}/proposal.md`
- `openspec/changes/{change-name}/tasks.md`
- `openspec/changes/{change-name}/spec.md` when present
- `openspec/changes/{change-name}/design.md` when present
- `openspec/changes/{change-name}/apply-progress.md` when present
- `openspec/changes/{change-name}/state.yaml`
- relevant changed files and current source tree reality
- project quality commands from `openspec/config.yaml`

## Writes

Write or refresh:
- `openspec/changes/{change-name}/verify-report.md`
- change `state.yaml`

This phase should not write code files.

## Preconditions

`sdd-verify` may proceed only when all are true:
- the active objective is not `planner`
- `tasks.md` exists
- implementation evidence exists for the active change
- the current change scope can be recovered from artifacts and code

Implementation evidence may come from:
- completed `sdd-apply` work in `apply-progress.md`
- changed files in the active scope
- other explicit implementation evidence already persisted for the change

If these conditions are not met, return `partial` or `blocked` instead of guessing.

## Output structure

Use `templates/artifacts/verify-report.md` as the baseline shape.

The report must include:
- verification summary and scope
- artifact review set
- final command plan and results from `config.yaml`
- compliance matrix against `spec.md` and `tasks.md`
- open issues with severity
- evidence log
- verdict and archive gate
- next-step recommendation

## Verification workflow

1. Recover the full change context
   Read the formalization artifacts, execution ledger, current code, and state.
2. Determine verification scope
   Confirm whether the change touched code, configuration, docs, or multiple layers.
3. Build the final command plan
   Start from `sdd.quality_commands` in `openspec/config.yaml`.
4. Review artifact compliance
   Compare the final state against the expected behavior, task completion, and material design constraints.
5. Run relevant checks
   Execute the chosen final verification commands when available and justified.
6. Build the compliance matrix
   Record whether each relevant requirement or target is satisfied, warning-level, failed, or not applicable.
7. Assign issue severity
   Separate blocking failures from non-blocking observations.
8. Decide the verdict
   Use the verdict model below, not intuition alone.
9. Write `verify-report.md`
   Leave enough evidence for later archive without requiring chat history.

## Command selection rules

Final verify must derive command usage from `openspec/config.yaml`.

Read these categories when present:
- `test`
- `build`
- `lint`
- `typecheck`

Rules:
- use configured commands as the canonical starting point
- if a relevant category is not configured, record `not_configured` instead of inventing a hidden canonical command
- for code-touching changes, the default final verify plan should attempt `test` when configured
- for code-touching changes, the default plan should also attempt at least one of `typecheck`, `build`, or `lint` when configured
- broaden beyond that minimum when the blast radius, stack, or risk level justifies it
- if a configured command is skipped, record why
- if a command fails because of an environment or tooling blocker, record that failure explicitly and let it affect the verdict
- if the repo exposes only broad project-wide commands, that is acceptable here as long as the report records the cost and outcome clearly

`stage-qa` may reuse narrower checks.
`sdd-verify` should be strong enough to support final closure.

## Compliance matrix rules

The compliance matrix is mandatory.

Build matrix rows from this source order:
1. `spec.md` acceptance criteria, invariants, and regression expectations when present
2. `tasks.md` validation notes and completion commitments
3. `design.md` constraints or risk notes only when they materially affect correctness

Each row should capture:
- `check_id`
- `source`
- `requirement_or_target`
- `evidence`
- `status`
- `notes`

Recommended status values:
- `passed`
- `warning`
- `failed`
- `not_applicable`

Rules:
- do not let an expected requirement disappear from the matrix just because evidence is weak
- use `warning` for non-blocking gaps or residual uncertainty
- use `failed` when a material requirement is unmet or the evidence is too weak for a trustworthy closeout
- use `not_applicable` only when the requirement truly does not apply to the implemented scope

## Evidence expectations

Evidence is mandatory for this phase.

The final report should include evidence from these categories when applicable:
- reviewed artifacts
- code or file inspection
- executed quality commands
- observed behavior or outputs
- carry-forward findings from `apply-progress.md` or `stage-qa`

Evidence should be short, auditable, and enough to support archive later without reopening the whole investigation.

Command evidence should record:
- command category
- configured command string
- execution result
- short outcome summary

Artifact and file evidence should reference:
- the artifact or file path
- the relevant section, task, or behavior being validated
- the short conclusion drawn from that evidence

Passing `stage-qa` may contribute evidence, but it is never sufficient by itself.
`sdd-verify` must add a change-wide synthesis.

## Issue severity model

Use these severities in `verify-report.md`:
- `low`
- `medium`
- `high`

Interpretation:
- `high`: blocks closeout confidence; usually forces verdict `fail`
- `medium`: does not necessarily block correctness, but should normally prevent silent archive
- `low`: notable but minor observation that does not materially weaken closeout confidence

## Verdict model

Use these stable verdict ids:
- `pass`
- `pass_with_warnings`
- `fail`

Use these archive-gate states:
- `ready`
- `closeout_review_required`
- `blocked`

Verdict rules:

### `pass`

Use when:
- all applicable compliance rows are satisfied
- executed commands did not produce a blocking signal
- no unresolved issue meaningfully weakens closeout confidence
- evidence is sufficient for archive

Archive gate:
- `ready`

Typical lifecycle result:
- `verified`

### `pass_with_warnings`

Use when:
- the change is broadly compliant
- no blocking failure exists
- one or more non-blocking warnings, residual risks, or review-worthy observations remain

Archive gate:
- `closeout_review_required`

Typical lifecycle result:
- `verified_pending_archive`

This verdict should normally recommend a `closeout_review` checkpoint before archive.

### `fail`

Use when one or more of these are true:
- a material requirement failed
- a critical verification command failed
- evidence is too weak for trustworthy closeout
- unresolved high-severity issues remain

Archive gate:
- `blocked`

Typical lifecycle result:
- `blocked`

## State update rules

`state.yaml` should stay operational.

During and after `sdd-verify`, update:
- `lifecycle_status`
- `current_phase`
- `phases.sdd-verify`
- `open_risks` when warnings or failures expose real risk
- `evidence` only as a short verification summary
- `next_recommended_phase`

Do not copy the whole compliance matrix or full evidence log into `state.yaml`.
That detail belongs in `verify-report.md`.

Recommended routing after verdict:
- `pass` -> recommend `sdd-archive`
- `pass_with_warnings` -> recommend closeout review, then `sdd-archive`
- `fail` -> recommend `sdd-apply` or the upstream phase that can correct the finding

## Distinction from `stage-qa`

`stage-qa` is:
- batch-scoped
- selective
- fast
- meant for early warning

`sdd-verify` is:
- change-wide
- evidence-heavy
- stronger than incremental QA
- the final quality gate before archive

Passing `stage-qa` does not satisfy final verification.
Skipping `stage-qa` does not remove the need for `sdd-verify`.

## Validation

Before finishing, verify:
- the full change scope was reviewed, not only the last batch
- the final command plan came from `config.yaml`
- the compliance matrix covers the relevant `spec.md` and `tasks.md` targets
- evidence is enough to support the verdict without relying on chat memory
- the result does not imply that archive already happened

## Expected envelope

On success:
- `status: success`
- include `verify-report.md` in `artifacts`
- include evidence for the reviewed artifacts and executed commands
- include the final verdict and next recommended action

Important:
- a `fail` verdict may still return `status: success` when the verification phase completed and produced a trustworthy report
- the workflow is then blocked from archive by the verdict, not by an incomplete verify phase

Use `partial` when:
- meaningful verification work was completed but the final report is still missing required evidence
- one or more planned checks could not be completed and no reliable final verdict is possible yet

Use `blocked` when:
- the objective is `planner`
- required implementation evidence is missing
- prerequisites or tooling failures prevent a credible final verification attempt
