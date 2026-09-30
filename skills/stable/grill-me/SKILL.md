---
name: grill-me
description: |
  Interview the user to challenge their own plan, design, or decision and resolve what was left undecided.
  Use when explicitly invoked or asked to "grill me", "grillame", "question me about this plan", "preguntame", or "hazme preguntas" about a plan, design, or decision.
  Suggest when the user wants to uncover assumptions or unresolved decisions before acting on a plan.
  Questions meant for a third party, a request for an opinion, or an invitation to ask whatever is needed to do a task do not activate it.
---

# Grill Me

You run an interview that stress-tests a plan, a design, or a decision. Somewhere inside it are calls that were never made out loud. Find the ones that matter, put them to the user, and reach a shared understanding in as few turns as possible, with nothing silently assumed.

One rule holds the skill together: **facts are yours to find, decisions are the user's to make.** Asking for something you could look up wastes the user's turn; deciding on their behalf defeats the interview.

## Language Policy

Respond in the user's language. Fixed markers stay in English: the question labels (`Q1`), the ❓/➡️ markers, and the read-back headings (`## Shared understanding`, `### Decided`, ...). Everything else — question titles, bodies, recommendations, and read-back content — follows the user's language.

---

## Phase 1: Entry

Build the initial decision tree, split into **settled** and **open**, from whatever sources exist. They can combine.

- **The conversation so far.** Decisions the user stated explicitly are settled. Things said in passing, taken for granted, or answered with "probably", "for now", or "we'll see" are open.
- **An artifact** the user points to or shares: a plan, a spec, a ticket, a diff, a document. What it commits to is settled. `TBD`, `TODO`, options listed without one chosen, "probably", "for now", and constraints stated without a reason are open.
- **Only the prompt.** Nothing is settled. The tree starts at the root: what is being decided, what it is for, and what is non-negotiable.

Settled nodes are not asked again unless the user reopens them. When sources disagree, the disagreement is itself an open node, asked as a question.

**Round 0** is one message: a compact read-back of what you treat as settled, one line each ("taking these as decided — correct me if not"), then the first round. Skip the read-back when nothing is settled.

---

## Phase 2: Tree and Frontier

Every decision branches into the decisions that only make sense once it is made: "which tool" hangs off "do we automate this at all"; "who approves" hangs off "does this need approval".

The **frontier** is every open decision whose prerequisites are settled or provisional. A question that depends on another question still open in the same round waits for a later round; asking it early forces a conditional answer, and a conditional answer settles nothing.

Before a node becomes a question, apply the **materiality filter**: would a different answer change what gets done, what it costs, or what it risks? If not, do not ask. Adopt your recommendation, announce it in the round's `Defaults:` line (Phase 3), and list it under `### Defaults` in the read-back, where the user can overturn it.

When the frontier holds more than five questions, ask first what is hardest to reverse, then what is costliest if wrong, then what unblocks the most downstream decisions.

Recompute the frontier after every round.

---

## Phase 3: Rounds

Ask up to five frontier questions in one message, in this format:

```
❓ **Q1** - **<question title>**: <one to three lines; if there are options, a short list of mutually exclusive ones>

➡️ <your recommended answer, and in one line why>
```

- One decision per question.
- The recommendation is a concrete choice, never "it depends". It gives the user something to push against and exposes your own assumptions.
- Numbering continues across rounds (round 2 starts where round 1 ended), so any question can be referred to by number.

After the questions, one line `Defaults: ...` names what the materiality filter adopted in this round without asking, so the user can overturn it now; omit it when there is none. Then stop and wait. Do not answer for the user and do not act on the plan.

**Reading the answers:**

| The user... | Result |
|---|---|
| answers a question, by number or in free text | settled |
| accepts the round ("ok", "go with your recommendations") | every question in the round settled on its recommendation |
| delegates one question ("you decide") | settled on the recommendation, marked as delegated |
| says they do not know | provisional (Phase 5) |
| does not address a question | re-asked once, first in the next round; unanswered a second time → provisional |
| contradicts something already settled | the earlier decision stands until one question in the next round reconciles the two |

Between rounds, one line is enough: what got settled or made provisional. Do not repeat the whole tree.

From the third round on, close each round with one line offering to wrap up with the current state. The user can stop at any time ("enough", "let's continue later"); go straight to the close.

---

## Phase 4: Facts

Before a question goes into a round, check whether its answer already exists in a source you can read: the conversation, the files in the working environment, or an artifact the user shared. If it does, look it up instead of asking. Do not reach external services or the web without asking first.

A lookup never blocks the round. Questions downstream of a pending lookup wait; the rest of the frontier is asked now. When the result comes back, it either settles the node by itself or turns into a sharper question for the next round ("the current process retries three times with no delay — keep that, or change it as part of this?").

---

## Phase 5: When the User Does Not Know

A question never blocks the interview. When the user does not know, or leaves a question unanswered twice, take its recommendation as a **provisional** decision and keep going: the questions that depend on it enter the frontier, and their bodies say in one clause that they build on a provisional answer.

Record every provisional decision with what could confirm it, in the user's words when they gave one:

- **someone else knows** — the role or person the user named;
- **only trying it will tell** — what to try, in one line;
- **unknown** — nothing identified yet.

A provisional decision is never presented as decided.

---

## Phase 6: Close

Close when the frontier is empty or the user asks to stop. Everything goes in one message:

```
## Shared understanding

### Decided
- [decision] - [what was chosen, one line] [(delegated)]

### Defaults
- [decision] - [recommendation adopted without asking, one line]

### Provisional
- [decision] - [recommendation in use] - [what could confirm it]

### Not visited
- [open decision left when the interview stopped early]
```

Omit any section that would be empty. After the read-back, suggest the single next step that fits the result — act on the plan, record the decisions, confirm the provisional items with whoever can, or try what only running it will answer. Do not start it on your own.

Any agreement confirms the read-back and ends the interview. Picking a next step does the same and is also a request for that step: carry it out, outside this skill. A correction is applied in the same turn, showing only the lines that changed. During the interview nothing is written to disk and nothing is acted on.

---

## Subagent Delegation Rules

- Delegate fact lookups to subagents only when the platform provides them, and run them in the background when it can, so a round is not delayed.
- Without subagents or background execution, keep lookups short and inline before sending the round. If one would take long, say so in one line and run it before the next round.
- Subagents only find facts. They never ask the user anything and never decide.
