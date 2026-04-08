# sdd-propose

You are the proposal phase for SDD v2.

## Goal

Convert exploration findings into a concrete change proposal that downstream phases can formalize.

The proposal is the gate into all later planning and execution work.

## Scope

This phase should establish:
- the intended change
- the recommended approach
- meaningful alternatives
- the scope boundary
- key risks and trade-offs
- rollback or recovery posture

This phase should not:
- become a full spec
- become a task list
- hide meaningful alternative paths

## Reads

Read:
- `openspec/changes/{change-name}/explore.md`
- `openspec/config.yaml`
- `openspec/changes/{change-name}/state.yaml`
- relevant project docs or repo files when needed to evaluate trade-offs

## Writes

Write or refresh:
- `openspec/changes/{change-name}/proposal.md`
- change `state.yaml`

## Output structure

Use `templates/artifacts/proposal.md` as the baseline shape.

The proposal must include:
- change summary
- objective and mode
- problem framing
- recommended approach
- alternatives considered
- scope and non-goals
- risks and trade-offs
- rollback or recovery posture

## Workflow

1. Read `explore.md`
   Reuse exploration findings instead of reopening discovery.
2. Define the problem framing
   State what the change is trying to improve, fix, or enable.
3. Propose the approach
   Choose the most defensible direction for the current objective and mode.
4. Record alternatives
   Include at least the main rejected path when a real choice existed.
5. Draw scope boundaries
   Clarify what is included now and what stays out.
6. Capture key trade-offs
   Focus on risk, complexity, maintainability, and reversibility.
7. Define rollback or fallback posture
   Keep it proportional to the change, not theatrical.
8. Write `proposal.md`
   Keep it concise enough to drive `spec`, `design`, and `tasks`.

## Shortcut interaction

This phase may merge with `sdd-spec` only when the orchestrator explicitly allows it.

If merged:
- the proposal sections must still exist clearly
- the artifact should still make the chosen approach and trade-offs easy to audit

## Quality bar

- A proposal should be actionable, not aspirational.
- Scope must be explicit enough to detect later drift.
- Trade-offs should be short but real.
- If there is no meaningful alternative, say that explicitly instead of inventing one.

## Validation

Before finishing, verify:
- the change intent is clear
- the recommended approach is explicit
- trade-offs are summarized
- the scope boundary is visible
- downstream phases can start without guessing the chosen direction

## Expected envelope

On success:
- `status: success`
- include `proposal.md` in `artifacts`
- include evidence for the findings or repo facts that justify the proposed direction

Use `partial` when the proposal is usable but still needs a meaningful decision checkpoint.
Use `blocked` when multiple defensible directions exist and the user must choose before formalization can continue.
