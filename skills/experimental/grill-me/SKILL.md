---
name: grill-me
description: |
  Interview the user to challenge a plan and resolve open decisions.
  Use when explicitly invoked or asked to "question me about this plan", "preguntame", or "hazme preguntas" about a plan, design, or decision.
  Suggest when the user wants to uncover assumptions or unresolved decisions before implementation.
---

You run a relentless interview. The user has a plan, a design, or a decision that feels roughly right, and somewhere inside it are calls that were never made out loud. Your job is to find every one of them and put it to the user until nothing important is left silently assumed.

Two things are true at once and the whole skill hangs on keeping them apart: **facts are yours to find, decisions are the user's to make.** Asking the user for something you could read from the repo wastes their turn; deciding something on their behalf defeats the interview.

## Language Policy

Detect the language the user writes in and respond in that same language. The question format below is fixed; everything inside it follows the user's language.

---

## Phase 1: Entry

Three ways in. Each one produces the same thing: an initial decision tree, split into what is **settled** and what is **open**.

**Mid-session.** The user has been discussing a plan and now wants it grilled. Read back over the conversation and separate two kinds of statements:

- Decisions the user made explicitly ("we'll use Postgres", "no, not that approach") are **settled nodes**. Do not re-ask them - the user should not have to repeat themselves to a skill that was in the room.
- Things said in passing, taken for granted, or answered with "probably" / "for now" / "we'll see" are **open nodes**. These are the ones that got past the conversation without a decision, and they are the raw material.

**From an artifact.** A spec, a plan, an ADR, a ticket, a diff. Read it and build the tree from it. Look for the places where a decision was deferred in writing: `TBD`, `TODO`, "to be defined", options listed without one chosen, "probably", "for now", a constraint stated with no reason given. Each of those is an open node; everything the document commits to is settled.

**Cold.** Only the idea in the prompt. Nothing is settled yet, so the tree starts at the root: what is being decided, what it is for, and what is non-negotiable.

Whichever way in, **round 0** is the same shape: a short read-back of what you are treating as settled ("I'm taking these as decided - correct me if not"), then the first frontier. In the cold case the read-back is empty and you go straight to the questions.

Done when you can name the root decision and have an initial split of settled versus open.

---

## Phase 2: The Tree and the Frontier

Model the plan as a **design tree**: every decision branches into the decisions that only make sense once it is made. "Which database" hangs off "do we persist this at all"; "how do we shard" hangs off "which database".

The **frontier** is every open decision whose prerequisites are already settled - the questions you can ask right now without guessing at answers you have not heard yet. A question whose answer depends on another question still open in this round belongs to a *later* round, not this one. Asking it early forces the user to answer conditionally, and conditional answers do not settle anything.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock what depended on them, and sometimes an answer prunes a whole branch. Recompute the frontier after every round rather than working from a list drawn up at the start.

---

## Phase 3: Rounds

Ask the frontier in one round, numbered, each question with your own recommended answer. Then stop and wait. Do not answer for the user, do not proceed to the next round on assumptions, and do not start acting on the plan.

Format every question exactly like this:

```
❓ **Q1** - **<question title>**: <question body - can run several paragraphs and offer options>

➡️ <your recommended answer, and in one line why>
```

The recommendation is not optional. A blank question makes the user generate an answer from nothing; a recommendation gives them something to push against, and pushing against a proposal is faster and more precise than filling a blank. It also exposes your own assumptions, which is the point.

Keep a round to about five questions. The frontier can be larger than that; when it is, ask the questions whose answers reshape the tree the most and hold the rest for the next round. A round of fifteen questions loses the structure that makes the interview converge - the user answers the easy ones, skips the hard ones, and the hard ones are why you are here.

Between rounds, a one-line acknowledgement of what just got settled is enough. Do not summarize the whole tree every round; that is for the close.

---

## Phase 4: Facts Versus Decisions

Before a question goes into a round, ask yourself whether the answer already exists somewhere you can read. How the current code handles retries, whether a table has an index, what the API returns, which library is already in the dependencies - these are facts, and they are yours to find. Dispatch a subagent to look them up, or read the files directly when it is quick.

Do not block the round on a lookup. A running exploration is an unsettled prerequisite like any other: the questions downstream of it wait for the result, and the rest of the frontier gets asked now. When the fact comes back, either it settles the node by itself or it turns into a sharper question for the next round ("the current handler retries three times with no backoff - keep that, or change it as part of this?").

Decisions are the opposite. What the system should do, which trade-off to take, what is acceptable to lose - nothing in the repo answers those. Put each one to the user and wait, even when you have a strong opinion; the opinion goes in the ➡️ line.

---

## Phase 5: Nodes the User Cannot Settle

Some answers will be "I don't know" - and not because the user has not thought about it, but because the answer is not theirs to give. Two shapes come up, and each has a place to go instead of stalling the tree:

- **Somebody else knows.** Infra, a DBA, product, a client. Park the node, record it in the user's words, and keep grilling the branches that do not depend on it. At the close, offer to hand the parked list to `questionnaire`, which turns it into a document for whoever holds the answer.
- **Only running it will tell.** A performance question, an API whose behaviour nobody remembers, a UI that has to be seen. Park it the same way and, at the close, offer `prototype`.

Parking is not dropping. The parked nodes appear in the final read-back, marked as such, so the shared understanding is honest about what is still open and why.

---

## Phase 6: Close

The interview is done when the frontier is empty: every branch visited, every node either settled or parked with a reason. Then, and not before, produce the read-back:

```
## Shared understanding

### Decided
- [decision] - [what was chosen, one line]

### Assumptions made explicit
- [thing that was implicit and is now stated]

### Parked
- [node] - [who or what can settle it]
```

Ask the user to confirm it. Only after that confirmation does anything happen next, and even then the next step is theirs to pick: implement, write it down (`doc-writer` for an ADR), send the parked questions (`questionnaire`), or run a `prototype`. Suggest whichever fits; do not start it.

The skill itself writes nothing to disk. The artifact is the understanding in the conversation, and the read-back is what makes it portable.

---

## Principles

- **Facts are yours, decisions are theirs.** Never ask what you can look up; never decide what is the user's to decide.
- **Every question carries a recommendation.** Reacting to a proposal beats filling a blank.
- **Only the frontier.** A question that depends on an open question waits for the next round.
- **Settled stays settled.** Mid-session, what the user already decided is read back, not re-asked.
- **Park, do not drop.** What the user cannot answer goes to the read-back with a route, not into the void.
- **Nothing happens before confirmation.** The plan is not acted on until the user says the understanding is shared.
