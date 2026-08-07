---
template:
  id: runbook
  name: Runbook
  description: Operational procedure for executing, verifying, recovering or troubleshooting something - written for someone under time pressure who needs the next command.
  audience: [on-call, operators, whoever runs this at 3am]
  use_when:
    - documenting a deploy, migration, recovery or maintenance procedure
    - an incident response needs to be repeatable
    - a manual operation is handed to people who did not build it
  required: [purpose, prerequisites, procedure, verification, rollback]
  optional: [quick-reference, troubleshooting, escalation, summary]
  visuals: [flow - only when the procedure branches]
  toc: required
---

# Runbook: [Operation]

> [One line: what this procedure does and when to run it.]

## Table of Contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Quick Reference](#quick-reference)
- [Procedure](#procedure)
- [Verification](#verification)
- [Rollback](#rollback)
- [Troubleshooting](#troubleshooting)
- [Escalation](#escalation)

## Purpose

**Run this when:** [the trigger condition]

**Do not run this when:** [the conditions that make it the wrong procedure]

**Expected duration:** [rough time] · **Impact:** [what users see while it runs]

## Prerequisites

- [ ] [access, credentials, tooling, approvals]
- [ ] [state the system must be in before starting]

## Quick Reference

[The commands for someone who has done this before and needs the sequence, not the explanation.]

```bash
# 1. ...
# 2. ...
```

## Procedure

Every command here must come from a source — a script, a previous run, a verified session. A command
reconstructed from memory or convention gets executed against production by someone who has no way to
know it was a guess. If a step is unverified, mark it and say what would confirm it.

### Step 1 — [action]

```bash
[exact command]
```

**Expected:** [what the output looks like when it worked]

**If it does not:** [what to do, or which section to jump to]

### Step 2 — [action]

[Repeat. One action per step, in order, no branching inside a step.]

## Verification

[How to know it actually worked, from outside the procedure — a check, a metric, a request. "The
command exited 0" is not verification.]

```bash
[verification command]
```

**Success looks like:** [the observable result]

## Rollback

[How to undo it, and until what point undoing is still possible. Write this before the procedure is
ever run, not after the first time it is needed.]

```bash
[rollback command]
```

**Point of no return:** [the step after which rollback is not possible, and what to do instead]

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|

## Escalation

[Who to contact, in what order, and what to have ready when contacting them.]
