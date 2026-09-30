# grill-me — usage

An interview that stress-tests your plan, design, or decision until you and the agent share the same
understanding of it. It asks only what matters, proposes an answer for every question, looks facts up
itself, and never stalls on a question you cannot answer.

## When to use it

- You have a plan that feels roughly right and want the decisions hidden inside it made out loud
  before acting on it.
- You have a spec, ticket, or document with `TBD`s, "probably"s, and options nobody picked, and want
  them resolved.
- You have been discussing a plan in the session and want it challenged without repeating what you
  already decided.

## When not to

- You want questions prepared for someone else to answer. This skill interviews you about your own
  plan.
- You want a quick opinion ("does this make sense?"). That is an answer, not an interview.
- You want the agent to ask whatever it needs to do a task. That is ordinary clarification.
- You want the decisions written to a file. The interview writes nothing; its result is a read-back in
  the chat, which you can then ask to have recorded.

## How to invoke

Explicit invocation, or asking to be grilled or questioned about a plan, design, or decision:
"grill me", "grillame", "question me about this plan", "preguntame sobre este diseño", "hazme
preguntas sobre este plan". It suggests itself — without starting — when you want to uncover
assumptions or open decisions before acting.

## What you'll be asked

If the plan was already discussed in the session or comes from a document, the first message lists
what is taken as decided, one line each, so you can correct it; none of it is asked again. Facts the
agent can read — in the conversation, your files, or a document you shared — are looked up, not asked.

Then come rounds of at most five numbered questions, each with a recommended answer (➡️) and a
one-line reason. Each round only asks what can be decided now; questions that depend on an open answer
wait for the next round. Answering is cheap:

- answer by number or in free text;
- "ok" or "go with your recommendations" accepts the whole round;
- "you decide" delegates one question to its recommendation;
- "I don't know" is accepted: the recommendation becomes provisional and the interview keeps going;
- a question you skip is asked once more, then treated as "I don't know";
- "enough" ends the interview at any point.

Low-impact decisions are not asked at all: the recommendation is adopted, named in a `Defaults:` line
at the end of the round, and listed again in the final read-back — you can overturn it at either
point. From the third round on, every round offers to wrap up.

Questions and answers come in your language; the fixed markers (`Q1`, ❓/➡️) and the read-back
headings stay in English.

## Minimal example

> "Grill me on this: I want to move our weekly team meeting to async written updates."

```
❓ **Q1** - **Main goal**: Which problem should the change fix first?
   - a) meetings take too much of everyone's time
   - b) people in other time zones cannot attend
   - c) updates are not recorded anywhere

➡️ b) — it is the only one that more notes or a shorter meeting cannot fix.

❓ **Q2** - **What stays synchronous**: Is anything still decided live?

➡️ Keep a short monthly call for decisions; async is for status, not for debate.

Defaults: update format - three fixed headings (done, next, blocked)
```

> "Q1: b. Q2: not sure, the team leads decide that."

After the last round, a single message closes the interview:

```
## Shared understanding

### Decided
- Main goal - include people in other time zones

### Defaults
- Update format - three fixed headings (done, next, blocked)

### Provisional
- Live decisions - a monthly call - the team leads can confirm

Suggested next step: confirm the provisional item with the team leads.
```

Any "ok" confirms it and ends the interview; picking the next step also asks the agent to do it.
Nothing is written to disk during the interview.

---

For how the frontier, the materiality filter, and provisional decisions work, and why it is shaped
this way, see [README.md](./README.md).
