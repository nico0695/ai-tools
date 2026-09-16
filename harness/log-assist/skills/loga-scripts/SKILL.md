---
name: loga-scripts
description: >
  Reference for calling the log-assist query scripts: how to invoke one, how to read its
  envelope and exit code, and which script answers which symptom. Loaded by workers; it is
  reference material, not a step.
---

# loga-scripts

Every fact in an analysis comes from one of these scripts. They exist so that no one has to put
a log in a context window, and so that any claim can be reproduced by running the same command
again.

## Invocation

```
<python_cmd> scripts/<name>.py --analysis <id> [flags]
```

`python_cmd` comes from `loga.config.toml` and arrives in the handoff — `python3`, `python` or
`py -3`. Run from the clone root. Instead of `--analysis`, `--path <file-or-dir>` points at logs
outside an analysis folder.

**No shell pipes, ever.** Every filter is a flag, so the same command runs unchanged in bash and
in PowerShell. If a filter you want does not exist as a flag, it is not available — say so
rather than building it with `grep` or `findstr`.

## Common flags

| Flag | What it does |
|---|---|
| `--analysis <id>` / `--path <p>` | what to read. One or the other |
| `--file F<n>` | restrict to one file by its alias |
| `--limit` / `--offset` | page through rows |
| `--max-chars` | output ceiling, default 8000, maximum 40000 |
| `--format md \| json` | markdown for reading, json for exact values |
| `--save <path>` | also write the full output under `record/runs/` |

## Reading the output

The **first stdout line is a JSON envelope**, then markdown:

```json
{"script": "...", "ok": true, "returned": 12, "total": 118,
 "truncated": true, "warnings": [], "next": ["..."]}
```

Read it before the markdown. `returned` versus `total` is the difference between a page and an
answer: while `truncated` is `true`, the number you have is a floor, and reporting it as a total
is a false claim. `next` says how to ask for the rest. `warnings` carries what the script could
not do — an unparsed file, a signal too irregular to measure — and a warning that does not reach
the artifact was suppressed, not handled.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| `0` | ok | use it |
| `1` | internal error | a defect in the harness. Report the exact command; do not work around it |
| `2` | bad arguments | fix the call |
| `3` | bad input | check the path or the alias before blaming the log |
| `4` | partial | usable; `warnings` says what is missing, and the artifact must carry it |
| `5` | verification failed | the citation gate. Only `loga_verify_citations` returns it |

## Which script answers what

| The question | Script |
|---|---|
| what files and screens are here, do they parse | `loga_scan` |
| what is in this log at all, what is noise | `loga_summary` |
| where does this text or pattern appear | `loga_grep` |
| what happened around this citation or timestamp | `loga_window` |
| did it restart, how often, was it scheduled | `loga_sessions` |
| is it running out of memory, is it slow | `loga_resources` |
| did it stop reporting, when, for how long | `loga_gaps` |
| is this a bug we already know | `loga_check` |
| do these screens behave the same | `loga_compare` |
| who is the master, is the sync group well formed | `loga_cluster` |

Known signatures for `loga_check --all`: `BLACK-SCREEN-JSON`, `BLACK-SCREEN-IO`, `REBOOT-LOOP`,
`SYNC-SPLIT-BRAIN`, `SYNC-NO-GROUP`, `SYNC-NO-MASTER`, `HEARTBEAT-OUTAGE`, `MISSING-CONTENT`.
A `miss` means the condition was evaluated and did not hold; `insufficient_data` means the logs
could not evaluate it. They are not the same answer and are never reported as one.

For the live list with each script's flags: `loga_index`, and `loga_index --detail <name>`.

## What the scripts already handle

They encode the corpus traps so that no skill has to remember them: the 53-`=` boot banner
counted once, stack-trace frames folded rather than counted as errors, the epoch window at cold
boot, clock corrections told apart from real gaps, screen identity taken from content and never
from a file name, and periodic baselines **measured** per screen instead of assumed — webOS
ticks every 300 s where Tizen ticks every 60 s, so a fixed threshold would be wrong on one of
them. `docs/log-format.md` is the normative reference behind all of it.

What they do not do is decide. A script reports what it measured; whether that answers the
question is the skill's judgment, and whether it explains the incident is the report's.
