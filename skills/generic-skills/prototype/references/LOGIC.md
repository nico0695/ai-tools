# Logic Prototype

A tiny interactive terminal app that lets the user drive a state model by hand. The right shape when the question is about **business logic, state transitions, or the shape of the data** — the kind of thing that reads fine on paper and only feels wrong once you push it through real cases.

If the question is about what something looks like, read `UI.md`. If it is about something that already runs, read `PROBE.md`.

## 1. Isolate the logic in a portable module

The part that answers the question goes behind a small, pure interface that could be lifted out and dropped into the real codebase later. The TUI around it is throwaway; this module is not.

| Shape | Use when |
|---|---|
| pure reducer `(state, action) => state` | actions are discrete events and state is a single value |
| explicit state machine | "which actions are even legal right now" is part of the question |
| a set of pure functions over a plain type | there is no implicit current state, just transformations |
| a module owning ongoing internal state | the logic genuinely has a lifecycle |

Pick the shape that fits the question, not the one easiest to wire to a terminal. Keep it pure — no I/O, no terminal code, no `console.log` used for control flow. The TUI imports it and calls in; nothing flows the other way. This is what makes the prototype outlive itself: once the question is answered, the validated module lifts into the real code on its own.

## 2. Build the thinnest TUI that exposes it

Redraw the whole frame on every action — clear the screen and reprint, never append. The user should be looking at one stable view, not a growing scrollback that hides what changed.

Each frame, in this order:

1. **Current state**, one field per line or formatted JSON, so two frames diff by eye. Bold for field names, dim for derived or incidental values. Raw ANSI is fine (`\x1b[1m`, `\x1b[2m`, `\x1b[0m`) — do not add a styling library for this.
2. **The last few actions**, most recent first. When the user says "wait, that should not be possible", the sequence that produced it is the finding; without it on screen they cannot quote it back.
3. **Keyboard shortcuts**: `[a] add item  [t] tick clock  [1] preset: mid-checkout  [q] quit`.

The whole frame fits on one screen. Loop: read one key, dispatch to a handler, re-render, repeat.

## 3. Seed the hard cases

The states named in the contract's `OPTIONS` are usually five actions deep. If the only way in is by hand, the user never gets there and the prototype answers nothing.

Give each interesting state a preset key that jumps straight to it — the state after a failed payment, the state with forty items, the state mid-retry. Presets set the module's state directly. They are the shortest path from "run it" to "the question".

## 4. One command, and you run it first

Add a script to whatever task runner the project already has (`package.json`, `Makefile`, `justfile`, `pyproject.toml`) so the user never has to remember a path. If there is no task runner, put the command at the top of the prototype's own file.

Run it yourself before handing it over: press a few keys, hit one preset, confirm the frame renders and quit works.

## 5. Hand it over and watch

Give the user the command and the preset keys. They drive it. The moments worth catching are "wait, that should not be possible" and "huh, I assumed X" — those are bugs in the *idea*, which is the entire point.

If they want another action to probe the same question, add it. If the new action belongs to a different question, say so and stop there.

## 6. Close it out

Return to Phase 7 of `../SKILL.md`. The logic-specific mapping: the validated reducer or machine lifts into the real module — that is the decision, absorbed. The TUI shell rides to the throwaway branch as the primary source.

## Anti-patterns

- **The module is portable, the shell is not.** A reducer that references prompts or escape codes cannot be lifted, and the lift was the whole payoff.
- **In-memory state, not the real database.** Real data makes the prototype slow to change, which is the one property it cannot afford.
- **One question, not a framework.** "What if we also wanted to support X later" is a different prototype.
- **Ship the module, not the shell.** The TUI was built to be driven by hand from a terminal; it has no place in the product.
