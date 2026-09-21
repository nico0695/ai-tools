# Evaluation Contract

## Verdicts

- `PASS`: every required observable assertion passed and there are no critical findings.
- `WARN`: the run completed but has a non-blocking finding, comparability concern, or unobservable assertion.
- `FAIL`: an observable sdd-lite contract was violated.
- `BLOCKED`: the fixture, provider, or installation cannot support a trustworthy run.

Never convert missing evidence into a pass. Record it as `not_observable` and use
`WARN`, or `BLOCKED` when the missing evidence prevents the test objective.

## Isolation

The parent evaluation skill may read this package. A child session must not see:

- `sddl-eval*` skills
- evaluator prompts or prior analyst conclusions
- another provider's outputs
- prior CLI conversation history

The child may see the selected case prompt, the existing project wrappers,
installed sdd-lite, and the fixture state required by the case.

## Evidence

Prefer deterministic evidence in this order:

1. parsed config/state/schema results
2. filesystem manifests and diffs
3. structured CLI events
4. final assistant output
5. analyst inference, clearly marked

Every finding needs a stable id, severity, assertion or contract reference, and a
path or event excerpt. Do not store hidden reasoning. Store normal tool events and
final output only.

## Main-flow boundary

The default end-to-end flow includes proposal, spec, design, plan, executor,
stage/final QA, and every mandatory approval. It excludes optional 4R review,
Judgment Day, delivery, and archive. If sdd-lite offers an optional review, decline
it explicitly and continue with mandatory QA.

## Human approval

Planning and implementation must be separate child processes. After planning:

1. validate `state.yaml`, plan ownership, and absence of source changes
2. show the human a concise summary and artifact paths
3. record approval with timestamp and target stage
4. launch a new child process that resumes from persisted evidence

Repeat for every later approval gate. An approval written before the relevant
artifact exists is invalid.

## Comparison

Compare only against the baseline named by the campaign. Report model, CLI,
project hash, sdd-lite hash, case hash, and provider differences. A comparison may
still be useful when these differ, but it must be labeled `confounded`.

