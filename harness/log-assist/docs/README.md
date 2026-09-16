# Documentation map

Four kinds of document live here, and mixing them up is the main way to be misled. **Authoritative**
binds the code. **Reference** is verified material you consult. **History** records how the thing
came to be and no longer decides anything.

| Document | Kind | What it is |
|---|---|---|
| [`../README.md`](../README.md) | authoritative | What the harness is, and the quickstart |
| [`USER_GUIDE.md`](USER_GUIDE.md) | authoritative | How to run an analysis, read what it writes, and fix what breaks |
| [`architecture.md`](architecture.md) | authoritative | How it works inside, why, and where to change things |
| [`log-format.md`](log-format.md) | authoritative | The Dex Player log format. Binds the parser |
| [`scripts-idea/`](scripts-idea/) | reference | 99 patterns and 10 multi-line flows from a 178k-line corpus. The only source covering webOS |
| [`plan/log-assist-plan.md`](plan/log-assist-plan.md) | history | The implementation plan: scope, stages, acceptance |
| [`plan/STATUS.md`](plan/STATUS.md) | current state | What is done, every decision taken while building, and the manual tests still pending |
| [`plan/temp/`](plan/temp/) | history | Working notes: the decision log, the corpus reports, the script design |
| [`idea/`](idea/) | history | Pre-planning. Superseded by the plan wherever they disagree |

The skills, contracts and templates are documentation too, and they are the authoritative kind:
`skills/<name>/SKILL.md` is what a step actually does, `skills/_shared/` holds the rules every
skill obeys, and `templates/` defines the shape of every artifact.

## Where to start

| If you want to | Read |
|---|---|
| Use it | `../README.md`, then `USER_GUIDE.md` |
| Understand or change it | `architecture.md`, then the specific `SKILL.md` or script |
| Touch the parser or a corpus rule | `log-format.md` first, `scripts-idea/` for breadth |
| Know what is done and what is pending | `plan/STATUS.md` |

## Two things that mislead

**`idea/` and `scripts-idea/` look authoritative and are not, in different ways.** `idea/` is
pre-planning: it explores options the plan later decided differently. `scripts-idea/` is verified,
but on **one corpus** — its figures are measurements of those logs, not universal thresholds.
Where the two disagree about the log format, `log-format.md` wins, and it says why.

**Language split.** The harness itself is English, so that it reads the same for every assistant
and every user. `plan/`, `idea/` and `scripts-idea/` are Spanish: they are working documents
between the people who built it. The language of an analysis is yours to configure.
