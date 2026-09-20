---
id: report
required: [executive-summary, scope, what-changed, problems-encountered, current-state, open-work]
optional: [decisions, technical-debt, timeline]
closing: executive-summary
toc: auto
---

<!-- Work done over a bounded period: a sprint, a migration, a project, a handoff. Bounded in time
     and stale by design - it records what happened, not how the system currently works.
     The closing is the executive summary at the top; no summary section at the end. -->

# [Project or period] — Report

> [One line: what period this covers and where things ended up.]

## Table of Contents

<!-- Only when the finished document has 5 or more `##` sections. -->

## Executive Summary

<!-- What was done, how it went, and where it stands - for someone who reads only this section.
     Five to eight lines. It is the landing of the whole document, written first in reading order and
     last in writing order. -->

## Scope

<!-- The period covered, and what work is in and out of this report. A report without a boundary
     silently claims to cover everything that happened. -->

**Period:** [from - to] · **Covers:** [what] · **Does not cover:** [what]

## What Changed

<!-- The substantive changes, grouped by area rather than listed by commit. One row per change that a
     reader would care about; a commit log is not a report. -->

| Change | Area | Impact |
|---|---|---|

## Problems Encountered

<!-- What went wrong, what it cost, and how it was resolved or why it was not. A report where
     everything went smoothly is not a report - it is an announcement. If nothing went wrong, say so
     explicitly so the reader knows it was checked. -->

| Problem | Cost | Resolution |
|---|---|---|

## Current State

<!-- Where things stand right now: what is done, what is deployed, what is running.
     Distinguish "merged" from "released" from "in use" - they are not the same claim. -->

## Open Work

<!-- What is left, who it belongs to if a source says, and what blocks it. Unassigned work stays
     unassigned here rather than being attributed by inference. -->

| Item | Blocked by | Owner |
|---|---|---|

<!-- OPTIONAL SECTIONS - copy the exact heading only when at least one confirmed fact fills it.

## Decisions
     | Decision | Rationale | Consequence |
     Decisions taken during the period that outlive it. A decision that deserves its own argument
     deserves an ADR - link to it instead of relitigating it here.

## Technical Debt
     What was deliberately deferred, and what it will cost to pay back. Deliberate only - a bug found
     during the period is a Problem, not debt.

## Timeline
     Dates that matter: milestones, cutovers, incidents. Only when the sequence carries meaning the
     rest of the document does not.
-->
