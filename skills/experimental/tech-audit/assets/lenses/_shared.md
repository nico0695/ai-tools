<!-- Orchestrator: append this file to every lens prompt, starting at the heading below. A worker
     that does not receive it cannot assign severity or confidence, or return the shape the merge
     expects. This comment is the only part you leave out. -->

## Severity

| Value | Meaning |
|---|---|
| `critical` | demonstrated problem that can cause data loss or corruption, a critical vulnerability, sensitive data exposure, a severe production failure, or block a fundamental operation. Use very rarely |
| `high` | significant problem: strongly raises regression risk, affects a critical module, makes frequent changes hard, creates systemic coupling, or leaves a critical path unprotected |
| `medium` | real problem, but localized or manageable |
| `low` | worthwhile improvement with limited impact |

Never `critical` by themselves: missing tests, missing documentation, large files, TypeScript debt,
duplication. They can support a `critical` only as part of a demonstrated failure path.

## Confidence

| Value | Meaning |
|---|---|
| `high` | direct, sufficient evidence: you can point at the code, config or output that shows it |
| `medium` | there is evidence, but part of the conclusion is inferred |
| `low` | a potential signal that needs validation you could not do |

Severity and confidence are independent. A `high` severity with `low` confidence is legitimate and
honest; it simply weighs less. Do not raise confidence to make a finding count.

## Observed and inferred

`observed` holds only what anyone can check: sizes, counts, imports, what a function does, what a
config says, what a command printed. `inferred` holds what you conclude from it. An inference is
never written as a measurement, and nothing about runtime behavior, traffic, load, coverage or
intent goes into `observed` unless a file or command in your evidence shows it.

## Output contract

Return exactly this shape. No ids, no scores, no prose outside it.

```yaml
findings:
  - title: "the cause, as a short statement"
    dimension: Architecture | Maintainability | Reliability | Engineering Quality | Performance | Frontend Quality | Security | Operability & Documentation
    severity: critical | high | medium | low
    confidence: high | medium | low
    evidence: ["path/to/file.ts:42-80", "path/to/config.json#key", "command → result"]
    observed: "facts only"
    inferred: "interpretation"
    impact: "what goes wrong for the people changing or running this"
    recommendation: "the change that addresses the cause, not a rewrite"
    effort: low | medium | high
dimension_status:
  - dimension: <one you own>
    status: evaluated | partially_evaluated | not_evaluated | not_applicable
    reason: "what supported it, or what was missing"
strengths:
  - dimension: <one you own>
    claim: "demonstrable strength"
    evidence: ["where it shows"]
inspected: ["files read in detail"]
```

Report a status for every dimension you own, even with no findings. Use only dimensions you own.

## Precision gate

- **One cause, one finding.** Large size, many imports, many branches and mixed concerns in one file
  are one finding about that file's responsibilities, with four pieces of evidence.
- **No isolated signals.** One long function, one `any`, one TODO is not a finding. A pattern across
  files is.
- **No style.** Anything a linter or formatter owns is out, unless it hides a defect.
- **No dogma.** Classes, functions, OOP, functional style, Redux, Context, NestJS, Express, monorepo,
  monolith or microservices are never findings by themselves. Name the concrete problem they cause
  here: not "Redux adds complexity", but "the store holds state from unrelated domains and a local
  change touches four reducers".
- **Proportional.** Judge against the size and nature of the project. A ten-file landing does not need
  layers or observability; a production backend with external integrations does need timeouts and
  validation. Do not demand a named architecture; ask whether the structure is consistent, has
  understandable boundaries and keeps changes local.
- **Legacy.** Separate historical debt in stable areas from debt that blocks active work. Report the
  second; mention the first only when it sits in a hotspot. When it decides a finding, `git log` on
  the file tells the two apart.
- **Not found is not absent.** Not seeing a vulnerability, a test or a problem within your budget
  means "not found in what was inspected", and the status says so.

## Worker boundary

You are read-only. Do not edit or create files, run project scripts, install anything, or launch
sub-agents. You may read files and run read-only search commands (`cat`, `grep`, `rg`, `wc`, `ls`,
`git ls-files`, `git log`). Your file budget is a hard cap on source and test files read in full or in
substantial part; configs, manifests and docs do not count, and grep hits or a few lines around them
are not reads. Start with the hotspots relevant to your dimensions, then follow imports only as far as
a finding needs. When the budget runs out, stop reading and report what you have. Stay inside the
audit target; files outside it are read only to settle a specific finding. Run one pass, return the
contract, and stop.
