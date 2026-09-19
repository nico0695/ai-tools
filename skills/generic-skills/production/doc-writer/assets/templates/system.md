---
id: system
required: [overview, how-it-works, main-flow, summary]
optional: [scope, key-concepts, data, interfaces, configuration, errors-and-edge-cases, dependencies, deployment, limitations]
closing: summary
toc: auto
---

<!-- Explains something that already exists: a system, a module, a section, or one capability.
     This is the default for "how does X work" documents. -->

# [What is being documented]

> [One line: what it is and what problem it solves.]

## Table of Contents

<!-- Only when the finished document has 5 or more `##` sections. Entries must match real headings. -->

## Overview

<!-- What it is, what problem it solves, and for whom. Two or three paragraphs at most.
     A reader who stops here should know whether this document is the one they need. -->

## How It Works

<!-- The behavior and the pieces: what each one does and what it is responsible for.
     Use the table when there are 3 or more pieces; use prose when there are fewer.
     Consistent grain - do not mix a module and a function in the same column. -->

| Piece | Responsibility | Depends on |
|---|---|---|

## Main Flow

<!-- The main path, end to end. A diagram when it branches; a numbered list when it is 3 linear steps.
     Every diagram gets one line of prose above it saying what to look at. -->

## Summary

<!-- What this documents, what matters most in it, and what is binding. A landing, not a replay. -->

<!-- OPTIONAL SECTIONS - copy the exact heading only when at least one confirmed fact fills it.

## Scope
     What it covers and what it deliberately does not. Worth including when the boundary is easy to
     get wrong.

## Key Concepts
     Domain terms the reader needs before the rest makes sense. Definition list or table.

## Data
     Entities, fields and relations the subject handles. Cardinality only when a source establishes
     it - a foreign key proves a relation exists, not that it is 1..N.

## Interfaces
     What it exposes and what it consumes: endpoints, events, commands, function signatures.

## Configuration
     | Variable | Required | Default | Effect |
     Real defaults only. A plausible default is worse than an absent one.

## Errors and Edge Cases
     | Condition | Result | What the caller does |

## Dependencies
     What it needs to run, and what breaks when each one is unavailable.

## Deployment
     Where it runs, how it gets there, what it needs from the environment.

## Limitations
     What it does not handle, and what would have to change for it to. Include known technical debt
     when a source establishes it.
-->
