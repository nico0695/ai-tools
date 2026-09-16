---
name: loga-explorer
description: >
  Read bounded fragments of raw log text to find what the scripted path missed, and propose
  candidate patterns for the catalog. Opt-in, step 4b: runs only after two consecutive
  no-progress rounds and only when the user confirms it.
---

# loga-explorer

## Goal

Look at the log itself, in fragments, when the scripts have stopped producing. The output is
**leads, not conclusions**: an `E-xx` is a place to point a script at, and a `P-xx` is a
candidate for the catalog once a human accepts it.

## Runtime operating rules

Worker. Execute this skill only. Do not read `orchestrator/LOGA-RUNTIME.md`, do not route
another step, do not launch descendants. Do not touch `state.toml` or `SUMMARY.md`.

This is the only skill allowed to look at raw log text, and it is allowed only in fragments.
Never open a whole file. Reading a log end to end is what the whole harness exists to avoid: it
fills the context, and what fills the context stops being checkable.

## Scope

**Should**: go where the citations already point · read narrow windows · record every fragment
it read, so the next round knows what ground is covered · propose patterns with a counterexample.

**Should not**: confirm anything · claim an `E-xx` as a finding · widen the window because
something looked interesting · read a file the inventory did not list.

## Reads / Writes / Scripts

- **Reads**: the reason it was proposed, the digests of `record/`, bounded fragments of `logs/`
- **Writes**: `record/exploration.md` — and nothing else
- **Scripts**: `loga_window` (the preferred way to read a fragment) · `loga_grep` to locate one ·
  `loga_summary --top` to find shapes nobody has looked at yet

## Workflow

1. Start from why the scripted path stalled. Exploring without that reason produces interesting
   lines that answer nothing.
2. Pick the fragments before reading any of them, and say why each one: around a citation that
   already exists, around a boot, around the minute the symptom was reported, around a shape
   `loga_summary` shows as frequent but that nobody has read.
3. Read each fragment with `loga_window --at F<n>:<line> --before N --after N`. The output
   contract bounds it: `--max-chars` defaults to 8000 and never exceeds 40000. A fragment that
   does not fit is two fragments, each recorded — not one bigger read.
4. Prefer `loga_window` to any file-reading tool. When a fragment genuinely cannot be expressed
   as a window, record the exact range read in the Fragments table, so the budget stays visible.
5. Log every fragment read in the table, including the ones that showed nothing. A fragment that
   showed nothing is real information for the next round.
6. Write `E-xx` entries for what was noticed: verbatim excerpt, resolving citation, and
   `verification: none` until something changes that.
7. Write `P-xx` candidates only with **both** an example and a counterexample. A pattern with no
   counterexample is a guess, and a guess in the catalog is worse than an empty catalog.
8. Write `record/exploration.md` and return.

## The line this skill does not cross

An `E-xx` cannot support `outcome: confirmed`. It becomes an `F-xx` only when a query script
reproduces it or the user validates it — `loga-analyze` does that promotion, not this skill.
Say so in the digest every time, because an exploratory finding reads exactly like a confirmed
one once it is out of this file.

Candidate patterns are **not** written into `scripts/catalog.toml`. The catalog is extended by
hand, by the user (C-70).

## Artifact shape

`templates/record/exploration.md`. Appends a round; earlier fragments and findings stay.

## Validation

- Every fragment read appears in the Fragments table with its range and its reason.
- No whole file was read.
- Every `E-xx` carries a resolving citation and its verification state.
- Every `P-xx` carries an example **and** a counterexample, and names the platforms it was seen on.
- The digest states the budget spent and that nothing here is confirmed.

## Expected output

The five result fields, plus `round_result`. `partial` when the budget ran out with leads still
open — the file is written either way, with what was covered and what was not. The `next_action`
that matters most is usually "point `loga-analyze` at `E-xx` with this script", because that is
what turns a lead into evidence.
