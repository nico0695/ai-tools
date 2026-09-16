---
name: loga-init
description: >
  Set up this clone of log-assist: detect Python, ask for language and which assistants to
  enable, write loga.config.toml, copy the skills where the host can find them, and validate
  the result. Run once per clone, and again whenever loga_doctor reports drift.
---

# loga-init

## Goal

Leave the clone in a state where an analysis can start, and say plainly what is `ok` and what is
not. Idempotent: a rerun revalidates and repairs, it never duplicates anything and never
overwrites a working config with defaults.

## Runtime operating rules

Main session. This is the one skill that writes outside `analyses/`: `loga.config.toml` in the
clone root, the `inbox/` directory, and the skill copies under `.claude/skills/` and
`.agents/skills/`. Nothing else, anywhere.

Static validation only. Do not launch a worker, do not run a test analysis, do not spend tokens
proving the assistants work — `loga_doctor` checks presence and parseability, and that is the
whole check by design.

## Scope

**Should**: detect rather than ask what can be detected · ask only language and which
assistants · copy the skills byte for byte · report each check honestly.

**Should not**: write a config for an assistant the user did not enable · guess a Python
command that was not verified · repair by deleting something the user wrote · claim `ok` for a
check that came back `partial`.

## Reads / Writes / Scripts

- **Reads**: `loga.config.example.toml`, `.gitignore`, `skills/`, the existing
  `loga.config.toml` when there is one
- **Writes**: `loga.config.toml`, `.claude/skills/<name>/SKILL.md`, `.agents/skills/<name>/SKILL.md`,
  and the `analyses/` and `inbox/` directories
- **Scripts**: `loga_doctor` (step 6)

## Workflow

1. **Detect the current state.** Run `loga_doctor` first. A complete `loga.config.toml` means
   this is a rerun: revalidate, repair what drifted, and skip the questions whose answers are
   already in the config — confirm them in the closing summary instead of re-asking.
2. **Find Python.** Try `python3 --version`, then `python --version`, then `py -3 --version`,
   and keep the first that reports 3.11 or higher. Record the command, not the version, in
   `python_cmd`. If none qualifies, stop here and say so with the versions found: nothing else
   in the harness works without it. (These are the only calls the permission allowlist does not
   already cover, so the host may ask to approve them.)
3. **Ask.** One block, two questions: the analysis language (`es` default, `en`), and which
   assistants to enable (Claude, Codex, or both). Nothing else is asked — everything else is
   detected or fixed by the contracts.
4. **Create and check.** Create `analyses/` and `inbox/` if they are missing. Verify
   `.gitignore` covers `analyses/`, `inbox/`, `loga.config.toml`, `.claude/skills/` and
   `.agents/skills/`. If this clone sits inside another repository, check that repository's
   `.gitignore` too and report what is not covered — both folders hold customer log content
   and must never be committed.
5. **Write `loga.config.toml`.** Copy `loga.config.example.toml` and replace values:
   `version` from the example, `language` and `python_cmd` as resolved, `validated_at` as
   today's ISO date, and one `[ai_setups.<name>]` block per enabled assistant with its `status`
   from step 6. Keep the comments — they are what makes the file editable later. An existing
   config is updated field by field, never replaced wholesale.
6. **Copy the skills.** Every `skills/loga-*/SKILL.md` goes to `.claude/skills/<name>/SKILL.md`
   and `.agents/skills/<name>/SKILL.md`. Copy the file **byte for byte**: `loga_doctor` compares
   the copies against the source with an exact comparison, so a reflowed line or a normalized
   quote reads as drift. The canonical copy stays `skills/`; these exist so the host can list
   and preload them. `skills/_shared/` is not copied — skills reference it by path from the
   clone root.
7. **Validate.** Run `loga_doctor` again and read every row: Python, config, templates,
   contracts, wrappers, permissions, skill copies, the runtime, both adapters, `analyses/`.
   `missing` or `partial` on a row is reported as such, with what it blocks.
8. **Close.** A short summary, one line per check, plus two or three lines of usage with
   concrete examples — how to start an analysis, that logs go in `inbox/`, and that `loga_doctor`
   is what to run when something stops working.

## Reporting the assistants

For each enabled assistant, report what was actually verified: the CLI on `PATH` and its
version, the adapter present and parseable, the wrapper present. `status = "ok"` means all
three; `partial` means some; `missing` means none. Never report that an assistant "works" —
nothing here ran one. Say what was checked, so the user knows what was not.

## Validation

- `python_cmd` was verified by running it, not assumed from the platform.
- `loga.config.toml` parses as TOML and has `version`, `language`, `python_cmd`, `validated_at`,
  and a block per enabled assistant.
- All 9 skills exist in both copy destinations and are byte-identical to their source.
- `analyses/` and `inbox/` exist and are ignored by every `.gitignore` above it.
- The closing summary matches the last `loga_doctor` output row for row. A check reported as
  `ok` that doctor calls `missing` is worse than no summary.

## Expected output

The five result fields. `status: ok` when every check passes; `partial` when the clone is usable
but something is missing — an assistant not installed, a `.gitignore` that needs a line — with
each one named and its consequence stated; `blocked` when there is no Python 3.11 or higher.
`next_action` is what the user does next: start an analysis, or fix the one thing that blocks it.
