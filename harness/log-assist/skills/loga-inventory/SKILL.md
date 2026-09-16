---
name: loga-inventory
description: >
  Take stock of the logs in an analysis: which files, which screens, which platform and
  version, what period they actually cover, and whether they parse. Use at step 3, once the
  intake is done and logs/ is not empty, and again whenever new logs arrive.
---

# loga-inventory

## Goal

Turn `analyses/<id>/logs/` into a factual inventory and a metadata proposal the user can
confirm. This is the first step allowed to open a log. Nothing here interprets the incident:
the inventory says what evidence exists, not what it means.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. `state.toml` and `SUMMARY.md` belong to the
orchestrator: the metadata here is a **proposal**, and the orchestrator is the one who asks the
user to confirm it.

## Scope

**Should**: report what the scan measured, with a citation or an envelope figure behind every
cell · group files by screen · say plainly what the logs do not cover.

**Should not**: diagnose · name a cause · propose hypotheses · rank files by importance ·
call a quiet period an outage.

## Reads / Writes / Scripts

- **Reads**: `record/intake.md` digest (for the incident window), `logs/`
- **Writes**: `record/inventory.md` — and nothing else
- **Scripts**: `loga_scan` (primary) · `loga_summary` (volume and noise) · `loga_sessions`
  (boots per screen). Invocation and output format: `skills/loga-scripts/SKILL.md`.

## Workflow

1. `loga_scan --analysis <id>` — files, aliases, screen, platform, player version, range,
   line count, `parse_rate`, boots. This also writes `record/runs/manifest.json`, which fixes
   the `F1…` aliases every later step will cite.
2. Group the files **by screen**. Identity comes from `Machine:` in the content. Two files are
   the same screen when they share a strong identity signal, never because their names look
   alike: a file ending in `(1)` is a different screen, not a duplicate, and neither file name
   nor line count ever merges or splits a screen.
3. `loga_summary` per screen for volume, level mix and noise share; `loga_sessions` for boots
   and uptime. Report the figures, not conclusions drawn from them.
4. Compare what the files cover against the incident window in the intake digest. State the
   coverage gap in both directions: days requested with no logs, and logs outside the window.
5. Read `parse_rate`. Below 100 %, say how many lines did not parse and what they look like —
   a low rate makes every later count provisional and the report must carry that.
6. Collect what will bite later into Notes: clock jumps, truncated files, a screen with a
   single file, a platform mix inside one analysis.
7. Fill `Suggested metadata`, one evidence citation per field. A field the logs cannot settle
   is left empty and named in the digest — never filled with a plausible value.
8. Write `record/inventory.md` and return.

## Artifact shape

`templates/record/inventory.md`. Rerun rewrites the file rather than appending: the inventory
describes the current contents of `logs/`, so an old row that no longer matches a file is wrong,
not history.

## Validation

- Every cell comes from a script result — from the envelope, or from a line that can be cited.
- Screens are grouped by content identity; no merge or split is justified by a file name.
- `parse_rate` is reported for every file, including when it is 100 %.
- A period with no lines is described as "no lines", not as downtime. A scheduled power policy
  and a dead player look identical from outside, and the inventory does not choose between them.
- Every suggested metadata field carries its evidence, or is empty.
- The digest matches the body.

## Expected output

The five result fields. `status: ok` when the scan covered every file; `partial` when some file
failed to parse or a metadata field could not be settled, with both in the digest; `blocked`
when `logs/` is empty or nothing parses. `round_result` is `progress` when the inventory
changed what is known about coverage or identity.
