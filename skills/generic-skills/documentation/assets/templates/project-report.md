---
template:
  id: project-report
  name: Project Report
  description: Consolidates work over a period - what changed, what was decided, where it stands and what is left. Bounded in time and stale by design.
  audience: [team, leads, stakeholders, whoever continues the work]
  use_when:
    - closing a sprint, milestone, migration or project
    - handing work over to another person or team
    - a long session produced changes and decisions worth capturing before context is lost
  required: [executive-summary, scope, major-changes, current-state, summary]
  optional: [timeline, architecture-changes, features, technical-decisions, problems, testing, technical-debt, open-work]
  visuals: [timeline, flow]
  toc: required
---

# [Project / Period] — Report

> [One or two lines: what this covers and the period it covers.]

## Table of Contents

- [Executive Summary](#executive-summary)
- [Scope](#scope)
- [Timeline](#timeline)
- [Major Changes](#major-changes)
- [Architecture Changes](#architecture-changes)
- [Features](#features)
- [Technical Decisions](#technical-decisions)
- [Problems Encountered](#problems-encountered)
- [Testing and Validation](#testing-and-validation)
- [Current State](#current-state)
- [Technical Debt](#technical-debt)
- [Open Work](#open-work)
- [Summary](#summary)

## Executive Summary

[What was done and where it stands, for someone who reads nothing else. Three or four sentences, no
jargon they would have to look up.]

## Scope

**In scope:** [what this covers]

**Out of scope:** [what was deliberately not part of it, and where it lives]

## Timeline

| Date / Period | Milestone |
|---|---|

## Major Changes

| Change | Area | Impact |
|---|---|---|

[Expand below only the changes whose consequences are not obvious from the table.]

## Architecture Changes

[Structural changes: new components, moved boundaries, removed pieces. What someone with the old
mental model would now get wrong.]

## Features

| Feature | Status | Notes |
|---|---|---|

## Technical Decisions

| Decision | Rationale | Consequence |
|---|---|---|

[A decision that will be questioned later deserves its own ADR, linked from here.]

## Problems Encountered

[What went wrong, what it cost, and how it was resolved — including the problems that are still
unresolved. A report where everything went smoothly is a summary of the plan, not of the work, and it
is the section that saves the next person the most time.]

## Testing and Validation

[What was verified and how, plus what was not. The gaps are the part a reader needs.]

## Current State

[Where things stand as of this report: what is done, deployed, in review, blocked. Date it — this
section is the first to go stale.]

## Technical Debt

| Item | Why it was accepted | Cost of leaving it |
|---|---|---|

## Open Work

| Item | Why it is open | Who / when |
|---|---|---|

## Summary

[What was accomplished, what is binding on future work, and what the next person should pick up
first.]
