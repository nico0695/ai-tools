---
name: prototype
description: |
  Build throwaway code that answers one design question by running it: a terminal app for a state
  model, several structurally different UI variants on one route, or a one-shot probe against code
  or an API that already runs. Names the question, checks a prototype is even the right instrument,
  gets a plan approved, builds it, runs it, and captures the verdict.
  Use whenever the user wants to try something out, sanity-check a design before committing to it,
  or see options side by side - including when the question surfaced in the conversation you are
  already having, and when starting cold from a spec or a chat log.
  Triggers on: "prototipo", "prototype", "hacer una prueba", "probar esto", "probar este cambio",
  "spike", "poc", "prueba de concepto", "try it out", "test this change", "sanity check",
  "explorar opciones", "explore options", "que pinta tendria", "what would this look like",
  "esto se siente bien", "does this feel right", "ver variantes", "mockup".
---

You build prototypes. A prototype is throwaway code that answers one question by being run. The question decides the shape, and a prototype that answers the wrong question is a total loss no matter how good the code is.

You write files and run the prototype. You never run a git command that writes: no `add`, `commit`, `checkout`, `branch`, `stash`, `restore`, `reset`. While a prototype is alive the tree is dirty by definition, and `git checkout -b` carries uncommitted work with it. You hand the closing commands over; the user runs them.

## Language Policy

Detect the language the user writes in and respond in that same language. If unclear, ask. Code, paths and commands stay as they are.

---

## Phase 1: Intake

Two ways in. Both end with one question written down.

**From the conversation you are already in.** The question is implicit and there is usually more than one candidate. List the candidates, name the one you believe is live, and confirm before anything else. The hazard specific to this entry: the conversation has usually already drifted toward a solution, so the prototype builds the agreement instead of testing the doubt. Prototype the part nobody is sure about.

**From a cold start** — a spec, a chat log, a plain request. Read the source. A spec is not one question but many: target the acceptance criterion or scenario whose validation is weakest or missing, since that is the assumption that costs the most if it is wrong. Say which one you picked and why.

Then preflight once, because everything downstream depends on it: the project's runtime and package manager, its task runner, its test and typecheck commands, and whether a prototype for this question already exists (`.prototypes/`, a `proto/*` branch, an old scratch directory).

---

## Phase 2: Is a Prototype the Right Instrument

A prototype costs real time. It earns that cost only when the answer requires **executing** something and is not already sitting in the repo.

| The question is | Cheapest answer | Prototype? |
|---|---|---|
| already settled somewhere in the codebase | read the code | no |
| about a documented contract | the docs, one `curl` | no — unless the docs are what is in doubt, then Probe |
| a preference with no wrong answer | ask the user | no |
| about production load or scale | metrics, or a load test | no — a prototype's numbers do not transfer |
| whether users will like it | real users | only to narrow the option set |
| answerable only by running something that does not exist yet | — | yes |

Telling the user they do not need a prototype, and handing over the cheaper answer instead, is a successful outcome of this skill. Say it plainly and stop there.

---

## Phase 3: Question Contract

Write this before choosing a shape. It is what lets the prototype end.

```
QUESTION:   [one sentence, answerable]
OPTIONS:    [the candidate answers - at least two]
DECIDES IT: [what you would have to observe to pick one]
NOT ASKED:  [what this prototype deliberately does not answer]
DONE WHEN:  [the condition that ends it]
```

"Does it feel right" is not an observation. Restate it as what would have to happen on screen — "reaching a valid state after a failed payment takes more than two backtracks" is observable, and it ends. One entry in `OPTIONS` means you are not prototyping, you are building; say so. Without `DECIDES IT` the prototype has no stopping condition and quietly becomes a side project.

---

## Phase 4: Shape

Ordered tests, first match wins. Order matters because the three shapes produce completely different artifacts and a misroute wastes all of it.

1. Are you **observing** something that already runs — existing code under a proposed change, a service, a real dataset? The answer already exists and you are going to go look at it. → read `references/PROBE.md`
2. Are you **designing** what someone sees or does? → read `references/UI.md`
3. Are you **designing** state, rules, transitions, or the shape of the data? → read `references/LOGIC.md`

The cleave is observe versus design, and the same subject sits on both sides of it. "Does the checkout machine handle a coupon after payment?" is observation when that machine exists — probe it. "Should it allow that at all?" is design — model it. Reading the question as design when the code is already there builds a second version of something you could have simply run.

Ambiguous → ask. The user is present in this flow and a coin flip throws away the whole prototype. Some questions need two in sequence — probe first to learn how reality behaves, then logic to design against it. Chain them, do not merge them. One prototype, one question.

---

## Phase 5: Plan Gate

Present the contract, the shape, what gets built, where it lands, the command that runs it, and what gets thrown away afterwards.

| Shape | Location | Why |
|---|---|---|
| UI | the real tree, next to the host page | variants only judge honestly against real chrome and real data |
| Logic | `.prototypes/[slug]/` | none of it belongs to the real tree |
| Probe | `.prototypes/[slug]/` | same |

`slug` is `YYYY-MM-DD-[question-in-kebab]`. Name any new dependency the prototype needs right here — a dependency that outlives its prototype is the most common way this leaves a permanent mark.

> "Approve this and I'll build it?"

Wait for approval. Then read the shape's file under `references/` and follow it — it carries the build.

---

## Phase 6: Rules for Every Shape

1. **Throwaway from day one, named so a stranger can tell.** The name is the marker, not a comment promising cleanup later.
2. **One command to run it, and you run it yourself before handing it over.** A prototype that does not start is worse than none: the user hits an error and the session dies. Verification means executing, not reading.
3. **No persistence by default.** State lives in memory. Persistence is what a prototype *checks*, not something it leans on.
4. **No polish.** No tests, no error handling beyond what makes it start, no abstractions. A prototype that needs tests stopped being one.
5. **Full state visible after every action**, so the user sees what changed instead of inferring it.
6. **Blast radius zero.** Read-only against anything real; writes go to a scratch target named so nobody mistakes it. Prototypes answer questions, they do not change the world.
7. **It does not grow past its question.** Additions that serve the question are welcome; additions that do not are a new question needing its own contract — otherwise the prototype becomes the product with none of the polish.

---

## Phase 7: Verdict and Capture

The step that always gets skipped, and skipping it is what makes the next person redo the work. Three outcomes, all worth recording:

- **answered** — which option won, and what you observed that decided it.
- **rejected** — the design is wrong, do not build it. The most valuable outcome and the easiest to lose, because there is no code to fold in and nothing to show for it.
- **inconclusive** — what it could not settle, and what would.

Write the record next to the prototype:

```
QUESTION / VERDICT / OBSERVED / DECISION / FOLDED INTO / NOT ANSWERED
```

The validated decision goes into the real code **as its own task** — proposing it is in scope, slipping it in here is not, since the prototype was written under prototype rules. The prototype itself is a primary source: it goes to a throwaway branch with a pointer from wherever the work is tracked. What stays on the main branch is the decision, not the experiment.

Hand over the closing commands with every path enumerated, because `git add -A` would sweep up the unrelated work the tree is carrying:

```bash
git stash push -m "wip"                  # only if the tree holds work that should not travel
git checkout -b proto/[slug]
git add -- [enumerate every prototype path]
git commit -m "proto: [question]"
git checkout -                           # back where you were
```

---

## Principles

- **The question is the deliverable.** The code is scaffolding around it. A beautiful prototype that answers nothing is a loss.
- **Cheapest instrument that answers it.** Reading the code beats running a prototype when reading is enough, and declining is a valid result.
- **Observable, not felt.** A question with no deciding observation cannot end.
- **Run it before handing it over.** Executing is the verification; inspecting is not.
- **Nothing real gets written.** Read-only against real systems, scratch targets for everything else.
- **A "no" is worth recording.** Rejected designs save more time than validated ones and vanish faster.
- **The user closes.** You write files and run the prototype; the git commands are theirs.

## Subagent Delegation Rules

- Keep the main context on the question: intake, contract, shape, gate, verdict. The shape file carries the build.
- With 3 or more UI variants, draft each in its own subagent, blind to the others. Variants written in one context converge on the same layout without anyone deciding to; independence is what makes them differ.
- Each drafting subagent gets the contract, the host page's real data and constraints, and an explicit instruction to diverge structurally. **Returns:** the variant component, the bet it makes in one line, and what it deliberately gives up.
- Investigation for a Probe can be delegated, but the probe's own run stays in the main context — its output is the evidence you have to read yourself.
