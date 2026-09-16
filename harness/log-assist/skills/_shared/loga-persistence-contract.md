# loga-persistence-contract

Where `log-assist` stores durable data, who owns each file, and how writes stay contained. Shapes live in `templates/`; this contract states the rules that the templates cannot express.

## Layout

```text
analyses/<ref>-<slug>/
  logs/                      # flat, or logs/<screen>/ with exactly one level
  SUMMARY.md                 # the only file a human needs to read
  state.toml                 # metadata, status, rounds (machine-facing)
  record/
    intake.md
    inventory.md
    findings.md
    hypotheses.md
    comparison.md            # only when 2 or more screens are in scope
    exploration.md           # only when loga-explorer ran
    challenge.md             # only when loga-challenger ran
    runs/
      manifest.json          # file aliases and screen identity, cached by loga_scan
      <script>-<n>.md        # full outputs kept with --save
  reports/
    <YYYYMMDD>-findings.md   # only when there is a conclusion
    <YYYYMMDD>-status.md     # when the analysis pauses without one
```

Nothing is persisted outside `analyses/<id>/`, except `loga.config.toml` in the clone root and the skill copies `loga-init` writes to `.claude/skills/` and `.agents/skills/`. All three are gitignored: analyses never leave the machine.

## Analysis id

`<ref>-<slug>`, where `ref` is the Jira key when there is one and otherwise any reference the user picks (another ticket, a customer, an incident), and `slug` is a short lowercase kebab-case description.

```text
^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$
```

- `ref` keeps its original casing, so `DEX-1234` stays uppercase; `slug` is always lowercase.
- No spaces, no slashes, no dates in the id.
- Examples: `DEX-1234-black-screen`, `ACME-INC42-playlist-stuck`.

`id` in `state.toml` and the folder name are always the same string.

## Ownership

| File | Owner | Rerun behavior |
|---|---|---|
| `state.toml` | orchestrator only | updated before and after each step |
| `SUMMARY.md` | orchestrator only | rewritten after each step, current entries only |
| `record/intake.md` | `loga-intake` | appends a round, never discards the user's words |
| `record/inventory.md` | `loga-inventory` | rewritten when logs change |
| `record/findings.md`, `record/hypotheses.md`, `record/comparison.md` | `loga-analyze` | appends a round; curates in place |
| `record/exploration.md` | `loga-explorer` | appends a round |
| `record/challenge.md` | `loga-challenger` | appends a round |
| `record/runs/` | any query script, via `--save` | append-only |
| `reports/*.md` | `loga-report` | one new dated file per emission; never edited afterward |

Rules:

- A worker writes only the files it owns. A worker writing anything else is an incident: discard its result and say so.
- The orchestrator never writes inside `record/` or `reports/`.
- A downstream step may cite an upstream artifact but never silently redefines what the user already confirmed.
- Dates are ISO strings (`"2026-09-13"`), including in `state.toml` and in report file names (`YYYYMMDD` there).

## Digest

Every `.md` under `record/`, plus each report, opens with `## Digest`: 3 to 6 bullets covering what currently stands, what was discarded, what the last round produced, and any blocker. **The orchestrator reads only the digest.** A digest that lies about the body is worse than no digest; it is rewritten whenever the body changes.

## Entries and curation

Findings are `F-xx`, hypotheses `H-xx`, exploratory findings `E-xx`, candidate patterns `P-xx`. Ids are assigned once and never reused, even after a discard. Each entry carries the round that produced it, as in `F-07 [R3]`. Required fields per entry type are in the matching template.

Curation, on revalidating and discarding an entry: remove it from the live body and leave one line under `## Discarded` with its id, the round transition, and the reason with its citation. Nothing valuable is lost — the "ruled out" section of a report is built from exactly those lines — and the live body stays readable. `SUMMARY.md` shows only what currently stands.

## Budgets

Runtime targets, not limits enforced by a script:

| File | Target |
|---|---|
| each `record/*.md` | 200 to 600 words |
| each report | under 800 words |
| `SUMMARY.md` | about one screen |
| a digest | far shorter than its body |

Risks, blockers and the next action go near the top. The same narrative is not repeated in `state.toml` and in an artifact: `state.toml` is operational memory, not a transcript.

## Write invariant

Every step leaves its file written, including when it ended `partial` or `blocked` — with the blocker in the digest. Resume reads from disk; work that exists only in the conversation is work that is lost.
