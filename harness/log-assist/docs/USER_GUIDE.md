# User guide

How to run an analysis with `log-assist`, what it writes, and what to do when something does not
work. The [`README`](../README.md) covers what the harness is; this is how to use it.

---

## 1. Setting up

Open the clone with Claude Code or Codex and ask it to run `loga-init`. It:

- finds a Python 3.11+ command (`python3`, `python` or `py -3`) by actually running it;
- asks two questions — your analysis language (`es` by default, or `en`) and which assistants to
  enable;
- writes `loga.config.toml`, creates `analyses/` and `inbox/`, and checks your `.gitignore`
  covers both;
- copies the skills where the host can list them;
- runs `loga_doctor` and reports each check.

It never launches a test agent or spends tokens proving anything works. It reports what it
verified — a CLI on `PATH`, an adapter that parses, a wrapper present — so you also know what it
did not.

Rerunning is safe: it revalidates and repairs drift, and never overwrites a working config.

**The harness is English; your analyses are not.** Skills, contracts, scripts and templates are
English. The conversation and the prose inside `SUMMARY.md`, `record/` and `reports/` follow
`language`. Section headings, TOML keys, ids like `F-01`, and status values stay English so the
scripts can parse them regardless of your setting — and log excerpts are always verbatim.

---

## 2. The flow

Seven steps. You are asked to confirm at each point marked ✋.

| Step | What happens | What gets written |
|---|---|---|
| **new** | You describe the incident. It proposes an id and looks for related past analyses ✋ | `analyses/<ref>-<slug>/`, `state.toml` |
| **intake** | It asks what no log can answer | `record/intake.md` |
| **import** | It triages `inbox/` and shows you where each file will go ✋ | files land in `logs/` |
| **inventory** | It scans the logs and proposes metadata ✋ | `record/inventory.md` |
| **analyze** | One question per round, answered with script evidence ✋ | `findings.md`, `hypotheses.md`, `comparison.md` |
| **report** | Optional challenge, then the report | `reports/<date>-<type>.md` |
| **close** | You decide when it ends ✋ | `status = closed` |

### new

Give it a reference — a Jira key, a ticket, a customer, an incident — and a short description.
The id is `<ref>-<slug>`: `DEX-1234-black-screen`. It searches previous analyses first, because
the same screen having had the same problem in March is the most useful thing you can learn in
the first minute.

### intake

This is the step people want to skip, and it is the one that pays. The harness has not opened a
log yet: **gate 1** forbids it. So everything asked here is something only you know.

> The logs know what the player **did**. Only you know what was **seen**, and what **changed**
> around it.

Expect questions about what was on the screen, who noticed and when, what was deployed or
swapped that week, and what you already tried. Not about error counts or restart times — those
come from scripts, and being asked for them would be a bug.

Your own hypothesis is welcome and gets recorded as `H-xx` with `source: user`. It carries the
same weight as any other open hypothesis: it competes on evidence, it is not privileged and not
dismissed. Anything you cannot answer is parked as an open question rather than guessed.

Questions come in blocks of at most five, each with why it matters. `saltear 3` skips one,
`frenar` ends the block.

### import

Drop your logs in `inbox/` at the repo root — loose files, or whole folders exactly as they were
downloaded. Nesting does not matter: it walks the tree.

It runs after the intake, not before, so that **the analysis id describes the problem**
(`DEX-1234-black-screen`) rather than a file name, and so that no log is read before you have
said what you are looking for. It then shows you a plan, one row per file, and moves nothing
until you approve it ✋.

Two things it will not do:

- **It never overwrites.** Two folders each holding a `20260220-0.log` is normal — the second
  gets prefixed with its source folder, and both survive.
- **It never deletes what it did not place.** Screenshots, `.zip` files (compressed logs are out
  of scope in v1 and are never unzipped) and anything that does not parse stay in `inbox/`, each
  with a reason. A non-empty inbox after an import is the signal that something needs your eyes.

Original file names are kept, because they are what your ticket refers to.

### inventory

`loga_scan` reads every file and reports what is actually there: screens, platform, player
version, date range, line count, parse rate, boots. Then it proposes metadata and asks you to
confirm it ✋.

Confirm this carefully — it anchors everything downstream. Two things it will not do on its own:

- **It never merges or splits screens by file name.** Identity comes from `Machine:` inside the
  content. A file ending in ` (1)` is a different screen, not a duplicate download.
- **It never calls a quiet period an outage.** A scheduled power policy and a dead player look
  identical from outside. It reports "no lines" and leaves the interpretation to the analysis.

### analyze

Rounds. Each round answers **one question**, which you confirm before it runs ✋. That constraint
is deliberate: a round that tries to answer everything produces a wall of output that nobody
verifies.

A round ends as `progress` or `no-progress`, and `no-progress` is reported honestly. After two in
a row, the harness proposes `loga-explorer` — the only part allowed to read raw log text, in
bounded fragments, on your explicit approval. Its findings are `E-xx` and **cannot confirm
anything** until a script reproduces them or you validate them.

### report

Two types. `findings` when there is a conclusion; `status` when there is not — and a status
report is a real deliverable, not a failure: "here is what we know, here is exactly what is
missing" is often what unblocks a ticket.

Before either reaches you, **gate 2**: `loga_verify_citations` must exit `0`. If a citation does
not resolve, the report is not emitted — the claim gets fixed or removed, never the citation.

You can also ask for `loga-challenger` first. It attacks the conclusion: coverage gaps,
correlation read as cause, whether the evidence would look the same on a healthy screen. A
challenge that finds nothing still says so, and that sentence is what makes the report worth
trusting.

---

## 3. A worked example

Every command below runs against the synthetic fixture in this repo, so you can reproduce it
exactly. The outputs are real; the conversation around them is described, not transcribed.

**The scenario**: a screen reportedly "lost contact" for part of the day.

### Start with what is there

```
python3 scripts/loga_scan.py --path scripts/fixtures/sample.log
```

```
{"script": "loga_scan", "ok": true, "returned": 1, "total": 1, "truncated": false, "warnings": [], "next": [...]}
# Scan

- 1 file(s), **1 distinct screen(s)**, 1 sync group(s)

| Alias | Screen | Platform | Player | First | Last | Lines | parse_rate | Boots |
|---|---|---|---|---|---|---|---|---|
| `F1` | DEMO STORE 01 | tizen | 6.4.2408.2600 | 2026-01-15 03:45:00.00 | 2026-01-15 14:33:00.14 | 472 | 1.0 | 2 |
```

`F1` is now the alias for that file, and every later citation uses it. `parse_rate` of `1.0`
means every line matched the known format — below that, every count downstream is provisional.

### Ask whether it is something already known

```
python3 scripts/loga_check.py --path scripts/fixtures/sample.log --all
```

```
- 1 hit · 4 miss · 3 insufficient_data

## `HEARTBEAT-OUTAGE` — hit
*the screen lost contact with the server* · severity `critical`

- `sample.log:171 … sample.log:269 (15 consecutive)`
```

Three verdicts, and the difference matters. `hit` means the signature matched. `miss` means the
condition **was evaluated** and did not hold. `insufficient_data` means the logs could not
evaluate it at all — no line even matched the first step. Reporting the third as "no problem
found" would be a false negative dressed as a result.

### Get the evidence

```
python3 scripts/loga_grep.py --path scripts/fixtures/sample.log --regex "Heartbeat Sync failed" --limit 3
```

```
{"script": "loga_grep", ... "returned": 3, "total": 15, "truncated": false, ...}

| Citation | Level | Component | Excerpt |
|---|---|---|---|
| `sample.log:171` | ERROR | `Server Manager` | [Server Manager] Heartbeat Sync failed. Status: Error: Network Error |
| `sample.log:178` | ERROR | `Server Manager` | [Server Manager] Heartbeat Sync failed. Status: Error: Network Error |
| `sample.log:185` | ERROR | `Server Manager` | [Server Manager] Heartbeat Sync failed. Status: Error: Network Error |
```

`returned: 3` of `total: 15` — you asked for three. That distinction is the whole point of
reading the envelope first.

### Ask how long it actually lasted

```
python3 scripts/loga_gaps.py --path scripts/fixtures/sample.log
```

```
## Baselines used

| Screen | Signal | Median cadence | Gap threshold | Occurrences |
|---|---|---|---|---|
| `F1` | heartbeat | 60 s | 180 s | 34 |
```

**The threshold was measured, not assumed.** This screen's heartbeat ticks every 60 s, so a gap
counts above 180 s. On webOS the same script would measure 300 s and adjust. This is why no
script in the harness carries a hardcoded number.

One subtlety worth knowing: the signal is the *successful* heartbeat, not the attempt. During an
outage the player keeps trying every 60 seconds, so the attempts show no gap at all — the silence
is only visible in what came back.

### Read around a citation

```
python3 scripts/loga_window.py --path scripts/fixtures/sample.log --at F1:171 --before 3 --after 3
```

That is how context gets read: a window around a citation, never a whole file.

### What the analysis would then write

An `F-xx` in `findings.md` with the citation and a verbatim excerpt, an `H-xx` naming what would
confirm and what would refute it, and — if it holds up — a findings report whose every row
resolves under `loga_verify_citations`.

---

## 4. Reading what it writes

**`SUMMARY.md`** is the one file to read. It shows only what currently stands.

**`record/*.md`** each open with a `## Digest` of 3-6 bullets. The orchestrator reads only those
digests, which is how the conversation stays small while the record stays complete.

**`## Discarded`** at the bottom of each record file is worth more than it looks: it holds what
was ruled out, with the round it died in and why. The "ruled out" section of a report is built
from exactly those lines, and for a recurring incident it is often the most useful part —
knowing that the obvious cause was already checked and eliminated saves the next person a day.

**Entry ids** — `F-xx` findings, `H-xx` hypotheses, `E-xx` exploratory, `P-xx` candidate
patterns — are assigned once and never reused, even after a discard, so a reference in an old
ticket still means what it meant.

**`state.toml`** is operational memory: status, rounds, decisions, open questions. You can read
it; you should not need to.

---

## 5. Scripts in practice

```
python3 scripts/<name>.py --analysis <id> [flags]
```

`--path <file-or-dir>` works instead of `--analysis` for logs outside an analysis folder. Run
from the clone root. `loga_index` lists all 16; `loga_index --detail <name>` explains one.

**Never pipe.** Every filter is a flag, so the same command works in bash and PowerShell. If the
flag does not exist, the filter is not available.

### The envelope

The first line of stdout is JSON, then markdown:

```json
{"script": "loga_summary", "ok": true, "returned": 5, "total": 93,
 "truncated": false, "warnings": [], "next": ["..."]}
```

`returned` vs `total` is a page versus an answer. While `truncated` is `true`, the number you
have is a floor. `warnings` carries what the script could not do, and a warning that never
reaches the artifact was suppressed rather than handled.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | ok |
| `1` | internal error — a defect in the harness; report the command |
| `2` | bad arguments |
| `3` | bad input (missing path, unknown alias) |
| `4` | partial — usable, `warnings` says what is missing |
| `5` | verification failed — the citation gate |

### Extending the catalog

`scripts/catalog.toml` holds the known-bug signatures, and it is edited **by hand** — that is
deliberate, not a missing feature. A signature needs an example and a counterexample, and both
get verified when the file loads. A pattern without a counterexample is a guess, and a guess in
the catalog produces confident wrong answers forever.

When `loga-explorer` proposes a `P-xx` candidate, it writes it to `record/exploration.md` for you
to review. It never edits the catalog itself.

---

## 6. When something goes wrong

**Start with `loga_doctor`.** It checks Python, config, templates, contracts, wrappers,
permissions, skill copies, the runtime and both adapters, and says which are `ok`, `partial` or
`missing`.

| Symptom | Likely cause |
|---|---|
| "skill copies: partial — not copied" | `loga-init` has not run, or was interrupted |
| "skill copies: drifted" | a skill was edited after the copies were made — rerun `loga-init` |
| "config: missing" | no `loga.config.toml` — run `loga-init` |
| A script exits `3` | wrong path, or an alias from a different analysis |
| A script exits `1` | a real defect. Report the exact command rather than working around it |
| Counts disagree with your own `grep` | expected: a nested status overrides the line level, so the harness counts by effective level. The scripts say so when the two differ |

**If the assistant starts reading log files directly**, something is wrong. Only
`loga-explorer` may read raw text, only in fragments, and only after you approve it. Everything
else goes through scripts.

---

## 7. Limits

Worth knowing before you trust an answer:

- **Timestamps carry no timezone.** Comparing clocks across screens is an assumption, and the
  harness labels it as one rather than resolving it.
- **A cold boot writes epoch-dated lines.** `1969-12-31` lines are normal Tizen startup, before
  NTP lands. They are excluded from durations, not treated as corruption.
- **Absence of logs is not absence of a problem**, and a quiet period is not an outage.
- **The catalog only knows what someone taught it.** A `miss` on all signatures means none of
  the *known* problems matched.
- **An exploratory finding is not a confirmed one.** `E-xx` entries stay unconfirmed until a
  script reproduces them or you validate them.
- **Not yet verified**: the end-to-end conversational flow over real cases, execution on
  Windows, and the Codex adapter. See `docs/plan/STATUS.md`.
