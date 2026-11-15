# Report

The report is read by someone deciding what to do about a codebase, in a few minutes. Each section
answers one question and nothing is said twice. Headings and labels below are structure; render them
in the user's language. Paths, identifiers and commands stay untranslated, and so do the severity
words in finding headings (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and finding ids; the Effort and
Confidence labels and values are translated.

## Template

````
## Tech Audit — <repository name, or the target path relative to the repository root>
<type> · depth <depth> · focus <focus> · tolerance <change_tolerance> · ref <short sha | none> <(dirty)>
<include / exclude / max_runtime, only when set>

### Executive Summary
**Score:** <x.x>/10 — <verdict>  <· partial — excludes …>
**Confidence:** <High | Medium | Low>

<one or two sentences: the state of the project in plain words>

Main risks:
- <up to 4 items, each pointing at a finding id; omit the list when there are no findings>

<one line: "No critical findings." or "<n> critical: <ids>.">

### Scorecard
| Area | Score | Confidence | Main signal |
|---|---:|---|---|
| <dimension> | <x.x or —> | <High/Medium/Low or —> | <one short phrase; for — the reason> |

### Prioritized Findings
#### <SEVERITY> · <ID> · <title>
**Evidence:** `<path:line>`, `<command → result>`
<observed, one or two sentences> *<inferred, one sentence, marked as interpretation>*
**Impact:** <one sentence> · **Action:** <one sentence>
Effort: <Low/Medium/High> · Confidence: <High/Medium/Low>

<only when findings overflow the cap: n more not shown: x medium, y low.>

### Strengths
- <up to 6 demonstrable strengths, each with where it shows>

### Recommended Actions
**Now**
- <action> (<ids>) · <brief reason> · <effort>
**Next**
- …
**Later**
- …

### Analysis Limits
- <short items>

<one line offering to save this report to a file at a path the user chooses>
````

## Rules

**Header and summary**

- The summary is at most 12 lines. Never open with reassurance a finding below contradicts.
- Main risks name causes, not dimensions ("billing and orders import each other", not "architecture").
- Mention a type disagreement or `unknown` type in the header line.

**Scorecard**

- One row per applicable dimension, in the order of `scoring.md` §1. `not_applicable` rows are left out.
- `not_evaluated` rows show `—` in Score and Confidence and the reason in Main signal.
- `partially_evaluated` rows start Main signal with "partial: <missing source>", so every status is
  visible.
- No text under the table.

**Findings**

- Grouped by severity, `critical` → `low`, in the Phase 5 priority order; at most the depth's cap
  (8 / 12 / 15). Repetitive findings are grouped into one entry with its locations listed.
- Overflow collapses into the single "n more not shown" line with counts by severity.
- Observed and inferred stay visibly separate; an inference is never phrased as a measurement.
- No findings at all: keep the heading with one line saying what was inspected and that nothing met
  the bar. An empty heading reads like a pass that failed.

**Strengths**

- Only what is demonstrated, with where it shows. No generic praise. When nothing is demonstrable,
  keep the heading with one line saying so rather than inventing one.

All six headings are always present, in order; an empty section gets a one-line body. The only
extra section is *Evolution risks*, in `deep` (below).

**Recommended Actions**

- Each action references finding ids and does not repeat their explanation.
- Place by full priority, not severity alone: a `medium` in the central flow can be *Now*.
- Omit an empty horizon (Now, Next or Later) inside the section.

**Analysis Limits** — always present, short. Include whichever apply:

- checks that exist and were not executed, with the reason (build, e2e, integration, rejected scripts,
  missing `node_modules`, timeouts, `max_runtime` cuts);
- the no-write comparison result, and that writes into ignored cache paths cannot be ruled out when
  commands ran;
- `not_evaluated` dimensions are already in the scorecard; do not repeat them here;
- metrics that were unavailable (coverage, bundle size, cycles when no tool ran);
- security was a static, non-exhaustive review; and whether the dependency audit ran;
- runtime behavior and production infrastructure were not inspected;
- the share of the code read in detail ("<n> of <m> source files").

**Deep only**: an *Evolution risks* section, after Recommended Actions, only when it says something
the findings do not (a risk that emerges from several findings together, or from the trajectory
visible in history). Otherwise omit it.

**Never include**: time-horizon risk lists, a repeated conclusion, the full metric dump, an
explanation of the scoring method, or the list of every file inspected. The phrase "the project is
secure" never appears; say what was and was not found within this audit's scope.
