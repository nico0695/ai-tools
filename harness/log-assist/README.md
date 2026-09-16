# log-assist

An AI-assisted harness for analyzing Dex Player logs from digital signage screens.

You point it at a folder of logs and hold a conversation. It runs deterministic Python scripts
against the logs, keeps a written record of what was found, and produces a report where every
claim carries a `file:line` citation you can check yourself.

It works the same in Claude Code and in Codex.

## What it does

- Takes logs from one screen or several and helps you confirm or rule out what happened.
- Queries them through scripts, so **no log is ever loaded whole into a context window**. A
  24-file, 335k-line corpus is answered in seconds, not summarized from memory.
- Keeps one folder per analysis: the logs, a readable record of each step, metadata tied to a
  ticket, and the reports.
- Recognizes known problems from a catalog you extend by hand — black screens, reboot loops,
  sync split-brain, heartbeat outages.

## What it does not do

- It does not act. Nothing is restarted, reconfigured or updated; no ticket is touched. It
  produces text that a human acts on.
- It does not assert without evidence. A claim with no resolving citation does not reach a report.
- It does not replace your judgment. It helps you confirm or discard — you decide.

## Requirements

Python 3.11 or newer. Standard library only: nothing to install, no virtualenv, no lock file.
Runs on macOS, Linux and Windows.

## Quickstart

```
1. Clone this repo and open it with Claude Code or Codex.
2. Ask it to run loga-init. It detects Python, asks for your language and which
   assistants to enable, and validates the setup.
3. Drop your logs into inbox/ — loose files or whole folders, nested however they
   came. They stay there until an analysis is ready for them.
4. Ask for a new analysis: "analicemos DEX-1234, la pantalla del local queda en negro".
   It asks what happened, then imports from inbox/ and shows you where each file went.
5. Answer its questions and let it work. It will show you a report when the evidence
   supports one — or tell you honestly that it does not.
```

Full walkthrough: [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md).

## What an analysis leaves behind

```
analyses/DEX-1234-black-screen/
  logs/                     the log files you provided
  SUMMARY.md                the only file a human needs to read
  state.toml                status, rounds, decisions, open questions
  record/                   intake, inventory, findings, hypotheses, comparison…
  reports/20260913-findings.md
```

`analyses/` and `inbox/` are gitignored and never leave your machine: production logs carry
customer names.

## Two rules that are never bent

1. **No log is queried before a minimal intake** — the symptom, what was expected instead, and
   logs actually present. Analysis without a stated problem finds whatever it feels like finding.
2. **No report is emitted while a citation fails to resolve.** `loga_verify_citations` checks
   that every cited line exists *and* that the quoted excerpt matches it. A citation pointing at
   a real line with rewritten text is the one error a reader cannot catch, so the check exists
   for exactly that.

## Repo map

| Path | What it holds |
|---|---|
| `orchestrator/LOGA-RUNTIME.md` | how the session routes steps, gates and delegation |
| `skills/` | the 9 skills, plus the 3 shared contracts in `skills/_shared/` |
| `scripts/` | 16 Python scripts and `catalog.toml`, the known-bug signatures |
| `templates/` | the shape of every artifact an analysis writes |
| `inbox/` | where you drop logs on their way into an analysis |
| `docs/USER_GUIDE.md` | how to use all of it |
| `docs/architecture.md` | how it works inside, why, and where to change things |
| `docs/log-format.md` | the normative reference for the log format, with its evidence |
| `docs/README.md` | the map of every document: what is authoritative, reference, or history |

Run `loga_index` for the live list of scripts and what each one answers, and `loga_doctor` when
something stops working.

## The log format

`docs/log-format.md` is the parser's source of truth, and it separates what is **invariant**
(verified across two independent corpora, 335,515 lines) from what is **platform-scoped** and
what is merely **measured in one corpus**. That distinction is load-bearing: webOS emits a
heartbeat every 300 s and Tizen every 60 s, so any script carrying a fixed threshold would be
wrong on one of them. The scripts measure each screen's own cadence instead of assuming one.

## Status

The harness is complete and the scripts are verified against two real corpora and a synthetic
fixture. Not yet verified: the end-to-end conversational flow over real cases, execution on
Windows, and the Codex adapter. `docs/plan/STATUS.md` tracks exactly what is done and what is
pending.
