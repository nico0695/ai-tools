---
name: sddl-eval
description: >-
  Guide the user through choosing and running the appropriate sdd-lite evaluation
  level. Use when the user asks how to test, review, validate, benchmark, or compare
  an installed sdd-lite but has not selected level 1, 2, 3, init, or reporting.
---

# sddl-eval

Act as a small navigator, not a second orchestration runtime.

## Route

1. Establish whether a `sdd-lite-evals` workspace already exists for this project.
2. If not, direct the user to `sddl-eval-init`.
3. Select exactly one next skill:
   - structural or installation confidence → `sddl-eval-level-1`
   - trigger, wrapper, routing, worker, or resume behavior → `sddl-eval-level-2`
   - real proposal-to-QA behavior → `sddl-eval-level-3`
   - history or baseline comparison → `sddl-eval-report`
4. Explain expected model calls and mutations before handing off.

Do not read all level skills, provider references, or prior runs merely to explain
the menu. Never launch model-backed child sessions from this navigator.

## Response

Return the recommended skill, why it matches, expected cost class (`none`,
`moderate`, or `high`), and the information the user should have ready.

