# Validation

Run this in Phase 4, on the finished draft, before delivering. It is not proofreading. Its purpose is
to catch the sentence that arrived from plausibility rather than from a source — the one that reads
best in the document and is not true.

Order matters: grounding first, because a well-structured document full of unsourced claims is worse
than a rough one that is accurate.

Contents:
- [Pass 1: grounding](#pass-1-grounding)
- [Pass 2: coverage](#pass-2-coverage)
- [Pass 3: form](#pass-3-form)
- [What to do with what you find](#what-to-do-with-what-you-find)

## Pass 1: grounding

Do this against the **sources**, not against the draft. Checking a document against itself proves it
is consistent, which is exactly what a confidently wrong document already is.

1. Extract the claims a reader would act on — a responsibility, a dependency, a cardinality, a default
   value, a command, an error behavior, a limit.
2. For each one, go back to where it came from and confirm it says that.
3. Fix, qualify, or delete anything that does not survive.

Where unsupported claims come from, so you know where to look:

- **Template gravity** — the section existed, so it got filled. Check any section thinner than the
  rest, and any optional section that made it in.
- **Convention filling** — the usual default, the usual port, the usual retry count. Every specific
  number should be traceable to a source.
- **Inference promoted to fact** — a hedge in the notes ("probably batched") lost its hedge in the
  prose.
- **Session drift** — an idea discussed and rejected mid-session came back as the design.
- **Stale sources** — a README describing a state the code has left. When code and docs disagree, the
  code is evidence of what runs and the README is evidence of what someone intended. That is a
  conflict to state, not to resolve by preference.

Then the inverse: is anything from the context map's `UNKNOWNS` presented as settled, and is every
`CONFLICT` still visible in the document?

Finally, the marking rule: every inference sitting in a table cell, a diagram edge or cardinality, a
command, or a numeric value is marked as an inference.

## Pass 2: coverage

Mechanical — it checks the render rule was applied, not whether the document feels complete.

- Every `required` section of the template is present, either filled or carrying its
  `No establecido: …` line.
- Every rendered `optional` section has at least one confirmed fact behind it. If it does not, it came
  from template gravity — cut it.
- Every section that is in neither list has at least three confirmed facts behind it. (Skip this for a
  template declaring `content: free`.)
- Every section in the plan's `STRUCTURE` has a counterpart in the document, and vice versa.
- No confirmed Core fact from the context map is missing because of length. If the document outgrew
  itself, it gets split — it does not get trimmed.
- Open questions are stated as open rather than absent.

Missing is not the same as excluded. Excluded is a decision you can defend and mention at delivery;
missing means this pass found a gap.

## Pass 3: form

**Structure.**

- Heading levels nest without skipping (`##` → `###`, never `##` → `####`).
- The closing section the template declares in `closing` is present, and no second one was added.
- Table of contents present when the document has ≥5 `##` sections and the template does not set
  `toc: disabled`; entries match the headings exactly, in order.
- Internal links resolve; anchors match the slugs of the real, rendered headings.
- Code fences closed and language-tagged; tables with matching column counts in every row.
- No placeholder survived: `[...]`, `TODO`, `TBD`, `<name>`, an unfilled template line, or an HTML
  comment copied out of the template.

**Visuals.**

- Each one carries a relationship prose handles badly. If it restates a list, cut it.
- Nothing invented: every node, edge, cardinality and transition traces to a source.
- Inside the complexity budget: ≤10 nodes, one diagram per section, every decision edge labeled, every
  path terminated.
- Each diagram has a line of prose above it saying what to look at, and agrees with that prose.
- Mermaid syntax valid: balanced brackets, quoted labels with spaces or reserved words, participants
  declared before use, fence tagged `mermaid`.
- No table duplicates a diagram's content.

**Readability.**

- No wall of text where a list or table gives faster access, and no table where prose reads better.
- Acronyms and project-internal terms expanded on first use.
- One name per concept, matching what the code calls it.
- The same explanation does not appear in two sections — one of them is the real home.
- The first screen — title, one-line purpose, table of contents — tells a reader whether this is the
  document they need.

## What to do with what you find

| Finding | Action |
|---|---|
| claim contradicted by a source | fix it |
| claim no source supports | delete it, or state it as an open question |
| claim supported but softly | qualify it, and say what would confirm it |
| sources disagree | move it to the inconsistencies section |
| required section with no material | keep the heading, state the gap, mention it at delivery |
| rendered optional section with no confirmed fact | cut it |
| diagram containing an invented edge | remove the edge, or the diagram |
| document overflowing its subject | propose splitting, do not trim |

If the pass changes what the document *concludes* — not just how it is worded — say so at delivery
rather than shipping the corrected version silently. The user was working from the earlier version in
their head.
