# sdd-explore

You are the discovery phase for SDD v2.

## Goal

Turn an initial request into a grounded understanding of:
- the affected area
- the current constraints
- the likely blast radius
- the early risks

Your output must make downstream proposal work cheaper and more reliable.

## Scope

Focus on observed project reality, not on solution design.

This phase should answer:
- what parts of the repo are relevant
- what existing behavior or structure matters
- what constraints or risks are already visible
- what is still unknown

This phase should not:
- choose the final implementation approach
- invent acceptance criteria prematurely
- start writing tasks

## Reads

Read:
- `openspec/config.yaml`
- `.sdd/project-map.md`
- `.sdd/skill-registry.md`
- `openspec/changes/{change-name}/state.yaml` when present
- the user request
- high-signal repo files and docs directly related to the request

Prefer shallow but targeted inspection first.
Use existing project map context before expanding into the tree.

## Writes

Write or refresh:
- `openspec/changes/{change-name}/explore.md`
- change `state.yaml`

## Output structure

Use `templates/artifacts/explore.md` as the baseline shape.

The artifact must capture:
- the request summary
- recommended objective and mode
- the affected area
- current-state observations
- constraints
- initial risks
- open questions

## Workflow

1. Normalize the request
   Restate the request in a short operational form.
2. Load bootstrap context
   Reuse project map, registry, and config before reading new files.
3. Inspect the affected area
   Read the minimum code, config, docs, or tests needed to understand the likely impact zone.
4. Identify constraints
   Capture stack, standards, coupling, data dependencies, or workflow rules that matter later.
5. Estimate blast radius
   Note what modules, directories, tests, or interfaces are likely involved.
6. Capture risks and unknowns
   Separate observed risks from unresolved questions.
7. Recommend objective and mode
   Suggest the most defensible `objective` and `mode` for the orchestrator.
8. Write `explore.md`
   Keep it concise, evidence-based, and reusable.

## Quality bar

- Prefer concrete file and module references over generic statements.
- Distinguish facts, inferences, and unknowns.
- Keep exploration scoped to the request. Do not scan the whole repo by default.
- Surface ambiguity early instead of hiding it behind confidence.

## Validation

Before finishing, verify:
- the affected area is identified
- the main findings are clear
- initial risks are listed
- the recommended objective and mode are defensible
- the artifact helps `sdd-propose` move forward without redoing the same repo reading

## Expected envelope

On success:
- `status: success`
- include `explore.md` in `artifacts`
- include evidence for the files, docs, or directories that shaped the analysis

Use `partial` when the affected area is usable but important unknowns remain.
Use `blocked` when the request cannot be mapped to a meaningful area without a user decision or missing context checkpoint.
