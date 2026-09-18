# Judgment Day Judge Prompts

The main skill fills every `{...}` placeholder and launches both judges with byte-identical prompts
except `{judge_letter}`, which is bookkeeping for you — it names which output is which when you merge.
It never appears inside the text a judge reads: what keeps the two reviews isolated is that neither
prompt mentions that a second pass exists.

## Judge Prompt (Round One)

Build the launched prompt as this block, with `assets/judge-contract.md` appended from its first
heading onward.

```text
You are conducting a blind, adversarial review. Assume the target has defects until proven
otherwise.

Target (review reference): {target_reference}
Mode: {code | artifact}
Scope: {paths_or_diff_or_artifact}
{project_standards_block}

Criteria:
{criteria_block}

Rules:
- Run one exhaustive read-only sweep of the target. Do not inspect unrelated scope.
- Report a finding only with concrete, defensible evidence (proof_refs). When in doubt about a claim,
  either downgrade it to WARNING/SUGGESTION or stay silent.
- Record causal_disposition honestly; do not blame the target for pre-existing defects it does not
  introduce, activate, or worsen.
- Do NOT edit anything, run state-changing commands, launch sub-agents, or delegate.
- Return one explicit assessment (`correct`, `broken`, or `not_assessed`) for each supplied criterion,
  using the same criterion and location for the same behavior. `not_assessed` is not approval.

Return your assessments, findings rows (empty list if clean), and `evidence` of what you inspected,
then stop.
```

`{project_standards_block}` is built by reading `CLAUDE.md`, `AGENTS.md`, or visible architecture docs
in the reviewed project. If none exist, omit the line entirely — never leave an unfilled placeholder in
a launched prompt.

## Criteria Block — `code` Mode

Each criterion owns a distinct failure class; where two could plausibly describe the same defect, the
note says which one claims it. This matters beyond precision: an overlap lets the same defect reach the
merge as two differently worded claims, which turns a `confirmed` into a `suspect` for no real reason.

```text
- correctness: on every reachable path, the change does what its stated intent requires — a failure the
  change itself catches and surfaces is error handling's, not this one's
- edge cases: boundaries, ordering, concurrency, repeated invocation, empty/null input — specifically
  the shape of the input or the sequence of calls, not whether a resulting failure is handled
- error handling: a failure is caught, propagated, or surfaced to a caller who could act on it — owns
  silent swallowing and swallowed exceptions
- security: injection, authz gaps, secret exposure, unsafe input crossing a trust boundary — input
  already validated and inside the boundary is error handling's or correctness's, not this one's
- performance: an unbounded loop or query over input that can grow, or clearly quadratic-or-worse
  growth on a path invoked per request — not a micro-optimization with no growth risk
- project conventions: a violation of a standard visible in the injected block or an established
  pattern in the surrounding code — never your own preference
```

## Criteria Block — `artifact` Mode

```text
- completeness: a section the document promises is missing or placeholder prose — owns absence
- internal consistency: goals, scope, decisions, and steps contradict each other within the document
  itself — owns self-contradiction
- upstream alignment: the document silently contradicts a source or decision it claims to build on —
  owns contradiction with something outside the document
- feasibility: the proposed approach is unrealistic for the declared scope and constraints — owns the
  approach itself, not whether its risks are named
- risk coverage: a material risk, dependency, or unknown goes unnamed — owns omission of risk, distinct
  from feasibility, which owns whether the named approach can work at all
- executability: a section is present and not self-contradictory, but still too ambiguous for a reader
  to act on without reinterpreting it — owns ambiguity in present content, distinct from completeness,
  which owns absent content
```

For `artifact` mode, `location` in findings is the document section anchor (for example
`design.md#risks`), and `causal_disposition` is `introduced` unless the defect demonstrably comes from
an upstream source (`pre-existing`).

## Scoped Re-Judgment Prompt (Rounds After A Fix)

```text
You are conducting a scoped re-judgment.

You receive ONLY:
1. The frozen findings from the previous round: {frozen_findings_rows}
2. The review fix delta applied since then: {fix_delta_reference}

Your only job: for each previously confirmed severe finding, decide whether the fix delta resolves it
(`verified`) or it remains open (`still_open`), with concrete proof_refs. Do NOT re-review the original
target, discover new findings outside the delta, or widen scope. If the fix delta introduces an obvious
new severe defect inside its own lines, report it as a new findings row in the shape given below.

Return `results: [{finding_id, outcome, proof_refs}]` plus any new findings rows, then stop.
```

`{frozen_findings_rows}` carries only `location`, `severity`, `claim`, `evidence_class`,
`causal_disposition`, `proof_refs` — never which judge originally reported it. A judge who can see the
other judge's authorship on a prior round is no longer blind for this one. Any new finding a judge
reports here re-enters the normal convergence buckets in the next merge, exactly like a round-one
finding, with a fresh id.

## Merge Guidance (main skill side)

- Match findings across judges by same file/section and overlapping or adjacent lines (code) or the
  same section anchor (artifact), plus a compatible claim — same defect stated differently is still one
  defect.
- `confirmed` requires both judges severe on the same defect; merged severity is the higher of the two.
- One judge severe, the other `WARNING`/`SUGGESTION` on the same defect is not a contradiction — it is
  `suspect`; keep the milder assessment as a one-line note on the row instead of a separate `info` row.
- Incompatible claims about the same location (one says correct, one says broken; or mutually exclusive
  root causes) are a `contradiction` — never silently pick one.
- A `correct`/`broken` mismatch in explicit assessments is a contradiction even when one judge has no
  finding row; `not_assessed` alone is not a correctness claim.
- Suspects keep the reporting judge recorded in `Lens/Judge` (`judge-a` or `judge-b`) in your working
  merge state; strip that column before any row reaches a judge again (see above). Confirmed rows use
  `both-judges`.
