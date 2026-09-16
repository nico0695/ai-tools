# Exploration

<!-- Owner: loga-explorer, worker, opt-in. The only skill that reads raw log
     text, and only in bounded fragments — never a whole file.
     Nothing here is confirmed: an E-xx cannot support `outcome: confirmed`
     until a script reproduces it or the user validates it. -->

## Digest

- fragments read:
- exploratory findings:
- candidate patterns:
- budget:

## Fragments read

| Round | Alias | Range | Why this fragment |
|---|---|---|---|
| R3 | F1 | `logs/<file>:1200-1340` | |

## Exploratory findings

### E-01 [R3] <one line: what was noticed>

- evidence: `logs/<file>:<line>` — "<verbatim excerpt>"
- verification: `none` | `script loga_<name> reproduces it` | `user confirmed`
- becomes: F-xx once verified

## Candidate patterns

<!-- Input for extending scripts/catalog.toml by hand. A pattern without a
     counterexample is a guess. -->

### P-01 [R3] <short name>

- shape: regex `<...>` | sequence `<a>` then `<b>` within `<n>`s | absence of `<x>` every `<n>`s
- example: `logs/<file>:<line>` — "<verbatim>"
- counterexample: `logs/<file>:<line>` — "<verbatim>"
- platforms: `<tizen | webos | both>`
