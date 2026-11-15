# Scoring

Scores summarize findings that already exist. Apply these steps in order, after Phase 5. Never
adjust a finding to reach a score.

## 1. Dimensions and status

| Dimension | Prefix | Owner lens |
|---|---|---|
| Architecture | `ARCH` | structure |
| Maintainability | `MAINT` | structure |
| Reliability | `REL` | quality |
| Engineering Quality | `ENG` | quality |
| Performance | `PERF` | quality |
| Frontend Quality | `FE` | quality |
| Security | `SEC` | risk |
| Operability & Documentation | `OPS` | risk |

Every dimension gets exactly one status:

| Status | When | Score |
|---|---|---|
| `evaluated` | the owner lens inspected it within budget and had the evidence it needs | yes |
| `partially_evaluated` | inspected, but a key source was missing (a check that exists and could not run, a part of the code outside budget, static analysis only where measurement exists) | yes, band capped at 7.5–8.4 |
| `not_evaluated` | no sufficient evidence could be obtained | no; state the reason |
| `not_applicable` | does not apply to this project type | no; out of the weights |

A check "exists" when a script or an installed tool can run it. A config with nothing that runs it
(e.g. `checkJs` with no `tsc` and no script) is evidence for a finding, not a missing source, so it
does not make the dimension partial. Checks skipped only because `depth` is `quick` do not make a
dimension partial either: they lower its confidence one level instead. Apply these status rules after
merging the workers' statuses; where they disagree with a worker, the rule wins.

Fixed applicability rules:

- **Frontend Quality** applies to `frontend`, `fullstack` and `static`; `not_applicable` otherwise.
- **Performance**: `evaluated` only with a measured artifact (bundle stats, a Lighthouse or benchmark
  report in the repo, performance tests that ran). Static analysis alone with at least one finding of
  confidence `high` → `partially_evaluated`. Static analysis alone without such a finding →
  `not_evaluated` ("no runtime or bundle measurements available").
- **Security**: when the dependency audit produced no result (not run, no lockfile, no network, bun),
  Security is at most `partially_evaluated`, with that reason. Two exceptions: a package that
  declares no dependencies has nothing to audit, and an audit skipped only because `depth` is `quick`
  lowers confidence instead (see above); neither makes Security partial.
- **Operability** for `library`, `static` and `backend (cli)`: only documentation and configuration
  count; logging, health checks and shutdown are not expected.

## 2. Band per dimension

Count only findings with confidence `high` or `medium`; a finding with confidence `medium` counts one
severity level lower (a `high` with confidence `medium` counts as `medium`). Confidence `low` findings
never move a band. First match wins.

| # | Test | Band | Default |
|---|---|---|---|
| 1 | ≥ 1 critical | 0.0–3.9 | 2.0 |
| 2 | ≥ 2 high | 4.0–5.4 | 4.7 |
| 3 | 1 high | 5.5–6.4 | 6.0 |
| 4 | ≥ 3 medium | 6.5–7.4 | 7.0 |
| 5 | 1–2 medium, or `partially_evaluated` with nothing above | 7.5–8.4 | 8.0 |
| 6 | only low or none, and at least one demonstrated strength tagged with this dimension (counted before the report's display cap) | 8.5–10.0 | 9.2 |
| — | only low or none, no demonstrated strength | 7.5–8.4 | 8.0 |

A strength is a positive practice present in the code or setup (a test suite around a flow, a typed
contract, a CI gate, atomic writes), never the absence of a problem ("no TODOs", "no `any`").

Start at the default. The score takes one of three values: the default, default − 0.4, or default +
0.4, clamped to the band. Move only with a one-line reason, which becomes the scorecard's *Main
signal*: down when the counted findings sit in central flows or are systemic, up when they are
isolated and the dimension also shows strengths. When neither or both apply, stay at the default.

**Per-dimension confidence**, first match:

| Dimensions | High | Medium | Low |
|---|---|---|---|
| Reliability (check: tests), Engineering Quality (lint or typecheck), Security (dependency audit, or no dependencies) | evaluated, and its check ran | evaluated without its check, or partial with it | partial without it |
| the others | evaluated | partial | — |

`quick` lowers each one level (High → Medium → Low). `not_evaluated` shows `—`.

## 3. Weights

Base weights, in %:

| Dimension | fullstack / backend / unknown | frontend | library | static |
|---|---:|---:|---:|---:|
| Architecture | 20 | 15 | 20 | 10 |
| Maintainability | 15 | 15 | 15 | 15 |
| Reliability | 15 | 15 | 20 | 10 |
| Security | 15 | 10 | 10 | 10 |
| Performance | 10 | 10 | 5 | 20 |
| Engineering Quality | 15 | 15 | 20 | 15 |
| Operability & Documentation | 10 | 5 | 10 | 10 |
| Frontend Quality | — | 15 | — | 10 |

For `fullstack`, Frontend Quality joins at 10 and the other weights keep their values; renormalization
in step 4 absorbs it.

**Focus** multiplies three dimensions by 1.5:

| Focus | ×1.5 | Read first (within each lens's budget) |
|---|---|---|
| `general` | — | — |
| `maintainability` | Architecture, Maintainability, Reliability | responsibilities, coupling, duplication, change radius, tests around hotspots |
| `scalability` | Architecture, Performance, Reliability | boundaries between domains, state ownership, persistence and data access, contention points, resilience |
| `release` | Reliability, Engineering Quality, Security | check results, CI gates, error paths, configuration, regression risk |
| `technical-debt` | Maintainability, Architecture, Engineering Quality | hotspots, legacy patterns, cycles, debt markers, incomplete migrations, TS debt |

## 4. Global score

1. Take the weights for the project type, apply focus, drop `not_applicable` dimensions.
2. Drop `not_evaluated` dimensions; their weight is redistributed by step 3. Record them for the
   "partial" label.
3. Global = Σ(score × weight) / Σ(weight), over the remaining dimensions. Round to one decimal, half up.
4. **Critical ceiling**: if any finding is a confirmed `critical` (Phase 5, step 3), global = min(global, 5.9).
5. If any applicable dimension is `not_evaluated`, label the score "partial — excludes <dimensions>".

Worked example: backend, `focus: release`, Performance `not_evaluated`, no critical.

| Dimension | Weight after focus | Band test | Score |
|---|---:|---|---:|
| Architecture | 20 | 2 high | 4.7 |
| Maintainability | 15 | 1 high | 6.0 |
| Reliability | 22.5 | 1 high | 6.0 |
| Security | 22.5 | 1 medium | 8.0 |
| Engineering Quality | 22.5 | 3 medium | 7.0 |
| Operability & Documentation | 10 | low only, no strength | 8.0 |
| Performance | — | `not_evaluated` | — |

(20×4.7 + 15×6.0 + 22.5×6.0 + 22.5×8.0 + 22.5×7.0 + 10×8.0) / 112.5 = 736.5 / 112.5 = 6.546… → **6.5**,
"partial — excludes Performance". Verdict: Acceptable.

Same repository with one confirmed critical in Operability & Docs: that dimension drops to band 1
(2.0), the weighted result is 676.5 / 112.5 = 6.01 → 6.0, and the ceiling makes it **5.9**. Verdict:
Fragile.

## 5. Verdict

| Global | Verdict |
|---|---|
| 9.0–10.0 | Excellent — ready to evolve and scale |
| 8.0–8.9 | Solid — low technical risk |
| 7.0–7.9 | Good — manageable technical debt |
| 6.0–6.9 | Acceptable — relevant risks should be addressed |
| 5.0–5.9 | Fragile — improvement plan recommended before significant expansion |
| < 5.0 | High risk — significant structural or reliability issues |

Render the label in the user's language.

## 6. Global confidence

How much support the verdict has, not how good the project is. First match wins. A dimension's
share is its weight after focus divided by the sum of all applicable weights after focus (before
dropping `not_evaluated` ones).

| # | Test | Confidence |
|---|---|---|
| 1 | `not_evaluated` dimensions add up to a share ≥ 30%, or no check was executed and no tool configuration (TS/JS config, lint, test runner, CI) was found | Low |
| 2 | at least two of {lint, typecheck, tests} executed with a result, and no dimension with a share ≥ 15% is `not_evaluated` | High |
| — | anything else | Medium |

`quick` executes no checks, so it tops out at Medium. That is intended: a triage carries less support.
A worker that exceeded its file budget does not change the confidence; it is recorded in Analysis
Limits.
