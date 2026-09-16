# loga-user-interaction-contract

How `log-assist` asks. The user is the one who knows the incident; the harness helps them confirm or rule it out, and never decides for them.

## When to ask

Ask only when the answer changes what happens next: scope, direction, risk, or whether an analysis closes.

Never ask:

- what a script can answer — run the script
- what `state.toml` or an artifact already records — read it
- for confirmation of something the user already confirmed this session
- the same question twice because the earlier answer was not persisted

Never infer an answer from silence, and never treat a plausible guess as an answer. An unanswered question is an open question, not a decision.

## Question blocks

Questions arrive in one block of at most 5, never drip-fed. Each carries:

- the question, concrete and answerable in one line
- **why it matters** — what changes depending on the answer
- 2 to 4 options where options exist, with one marked as the recommendation and the reason for it
- free text always allowed

The block states that `saltear N` / `skip N` skips one question and `frenar` / `stop` ends the block. Anything skipped or unanswered goes to `open_questions[]` in `state.toml` and is raised again only if it becomes blocking. Unrecognized input reprints the block rather than guessing.

For picking from a list — screens, log files, related analyses — the action set is `todos | ninguno | 1,3 | 1-4 | ver N | listo`. Nothing is acted on before `listo`.

## Checkpoints

Points where the flow stops for the user, matching the routing table in the runtime:

| Checkpoint | Fires when | Must show |
|---|---|---|
| `analysis_identity` | creating an analysis | proposed `<ref>-<slug>`, and related analyses found by `loga_search` |
| `missing_context` | intake, or any `needs-info` | what is missing and why it blocks progress |
| `metadata_confirmation` | after `loga-inventory` | platform, player version, screens and date range the scan suggests, each with its evidence |
| `round_question` | before each `loga-analyze` round | the single question the round will answer |
| `explorer_proposal` | after 2 consecutive `no-progress` rounds | why the scripted path stalled, and that the explorer's findings will not confirm anything on their own |
| `report_decision` | closing or pausing | which report type, and the outcome being claimed |
| `close_confirmation` | marking `closed` | what stays unanswered |

## Confirmations

`dale`, `ok`, `sigue`, `listo`, `avanzá`, `yes`, `go` and equivalents are confirmations. Substantive feedback replaces a confirmation: act on it instead of asking again. A confirmation covers the thing that was actually shown, not the step after it.

## Recording

Every answer that changes direction is persisted before moving on: a scope or approach choice becomes a `decisions[]` entry in `state.toml` with its date; a hypothesis offered by the user becomes an `H-xx` with `source: user`, carrying the same weight as any other open hypothesis until evidence moves it; a skipped question becomes an `open_questions[]` entry.

## Reporting back

Say plainly what is known, what is inferred, and what is unknown. A result that does not answer the user's question is reported as such — not padded, not dressed up as progress. When evidence is thin, `inconclusive` with the reason is the honest outcome and an acceptable one.
