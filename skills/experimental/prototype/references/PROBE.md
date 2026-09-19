# Probe Prototype

A one-shot script that answers whether something which **already runs** behaves the way everyone assumes. The question is factual rather than exploratory, so the artifact is a script you run once that prints a verdict — not something to drive by hand.

If the question is about a state model that does not exist yet, read `LOGIC.md`. If it is about what something looks like, read `UI.md`.

## Two sub-shapes

**Against your own code — a change spike.** "If I change X, what breaks?" Make the smallest version of the change that produces a signal, written to be thrown away, then run whatever surfaces the damage: the typecheck, the one test that covers it, the one endpoint that exercises it. You are not implementing the change, you are measuring its blast radius.

**Against the outside.** An API, a dataset, a library, a service. The docs say one thing; the question is what it actually does — response shape, null fields, pagination behaviour, rate limits, timezone handling, what an error really looks like.

## 1. Write the assumptions down first

A probe run only means something against a stated expectation. Before writing the script, list each assumption as a line you could be wrong about:

```
A1  the webhook payload includes payment_id
A2  amounts come back as integer cents, not decimal strings
A3  a refunded payment still appears in the list endpoint
```

Assumptions nobody wrote down are the ones a probe silently confirms by never checking them.

## 2. Blast radius

**Read-only against anything real.** GET, SELECT, list, describe. Nothing that writes, deletes, or enqueues.

If the question is inherently about a write — "does creating one of these actually cascade?" — that is not yours to decide. Stop and put it to the user with the radius spelled out:

> "Answering this needs a real write: [exact operation] against [exact target], which touches [what]."
> - **Scratch target**: [the throwaway account, database or namespace, if one exists]
> - **Real target**: only with your explicit go-ahead
> - **Skip it**: I answer the read-only part and mark the rest inconclusive

Use whatever credentials the project already uses and add none. No secret, token or connection string reaches the output, the script body, or any file that could be committed.

## 3. Make the run its own verdict

One line per assumption, so the terminal output pastes straight into the record with no interpretation:

```
A1  payment_id in webhook payload   EXPECTED present   OBSERVED absent    FALSE
A2  amounts as integer cents        EXPECTED cents     OBSERVED "12.30"   FALSE
A3  refunds appear in list          EXPECTED present   OBSERVED present   TRUE
```

Print the raw evidence under each false line — the actual response, the actual error, the actual row. A summary of a surprise is not evidence of it, and the surprise is the reason you ran this.

## 4. Run it, and read what it says

For a change spike, capture what broke: the failing typecheck output, the failing test names, the stack. That list **is the answer**.

**Do not fix what the probe breaks.** The breakage is the finding. Fixing it turns a five-minute measurement into an implementation nobody approved, and destroys the number you were after — what this change actually costs.

**Do not revert it either.** Leave the working tree as the evidence and tell the user exactly what is in it, so they decide whether to keep the spike, fold it, or throw it out.

## 5. Close it out

Return to Phase 7 of `../SKILL.md`. The probe's own output is most of the verdict record — paste it in. What needs adding is what changes because of it: which assumption was wrong, and what that costs downstream. An assumption falsified and not written down gets assumed again next month.

## Anti-patterns

- **The breakage is the finding, not the task.** A spike that ends in a green build measured nothing.
- **Scratch targets, not production.** A probe that mutates a real system is not a probe.
- **Verdict, not implementation.** A probe ends when the assumptions are marked true or false.
- **Raw evidence, not a summary.** "The API behaved unexpectedly" is not a result anyone can act on.
