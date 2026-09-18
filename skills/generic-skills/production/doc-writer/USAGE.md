# doc-writer — usage

Turns what's already in front of you — the conversation, code, a diff, files you name — into a
grounded Markdown document. It asks about what's missing instead of guessing it.

## When to use it

- You explicitly want a Markdown document created, written, or captured before the context is lost.
- You already know the shape: an ADR, an investigation, a report, a system or module doc.
- You just say "document this" and let it work out the shape.

## When not to

- You want existing docs checked against the current code for drift — this skill writes, it doesn't
  audit.
- You want a diagram on its own — it only draws one inside a document it's already writing.

## How to invoke

By name (`doc-writer`) or naturally: "documentá esto", "creá documentación", "document this", "armá
un doc", "hacé un relevamiento", "write it up", or by naming a shape with a creation request
("creá un ADR de esto"). "Dejalo registrado" only suggests the skill unless it also asks to create
or write the document.

Add "auto" (`doc-writer auto`, "sin preguntarme") to skip the plan-approval gate. Interactive is the
default.

## What you'll be asked

| Gate | When |
|---|---|
| Which type | only if 2 or more types fit equally, or none fit |
| Plan approval | interactive mode, always — approve the outline before it writes |
| Destination | always, both modes — where the file, or the chat, ends up |

## The five document types

You never have to name the type — it's inferred from what you're asking for.

| Say this kind of thing | You get |
|---|---|
| "explain how the X module works" | `system` |
| "why did we choose X over Y" | `adr` |
| "what did I find out about X" | `investigation` |
| "what we shipped / did this sprint" | `report` |
| doesn't fit the above | `generic` |

## Minimal example

> "documentá cómo funciona el sistema de colas, con foco en qué pasa cuando falla un job"

```
DOCUMENT:    system — Sistema de colas
GOAL:        que alguien nuevo entienda el flujo y qué pasa ante un fallo
STRUCTURE:   Overview, How It Works, Main Flow, Errors and Edge Cases, Summary
VISUALS:     flowchart del flujo principal
```
> ¿Aprobás este plan, querés cambiar la estructura, o hay algo que falta?

Approve it, and it composes the document, re-checks every claim against the sources it read, and asks
where to save it.

---

For how templates work internally, the rule that decides which sections render, and why it's shaped
this way, see [README.md](./README.md).
