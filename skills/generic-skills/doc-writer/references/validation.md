# Validation

Run this in Phase 7, on the finished draft, before delivering. It is not proofreading. Its purpose is
to catch the sentence that arrived from plausibility rather than from a source — the one that reads
best in the document and is not true.

Order matters: grounding first, because a beautifully structured document full of unsourced claims is
worse than a rough one that is accurate.

Contents:
- [Pass 1: grounding](#pass-1-grounding-the-one-that-matters)
- [Pass 2: completeness](#pass-2-completeness)
- [Pass 3: structure](#pass-3-structure)
- [Pass 4: visuals](#pass-4-visuals)
- [Pass 5: readability](#pass-5-readability)
- [What to do with what you find](#what-to-do-with-what-you-find)

## Pass 1: grounding (the one that matters)

Do this against the **sources**, not against the draft. Checking a document against itself proves it
is consistent, which is exactly what a confidently wrong document already is.

1. Extract the claims a reader would act on — a component's responsibility, a dependency, a
   cardinality, a default value, a command, an error behavior, a limit.
2. For each one, go back to where it came from and confirm it says that.
3. Fix, qualify, or delete anything that does not survive.

Where unsupported claims come from, so you know where to look:

- **Template gravity** — the section existed, so it got filled. Check any section whose content is
  thinner than the rest.
- **Convention filling** — the usual default, the usual port, the usual retry count. Every specific
  number in the document should be traceable.
- **Inference promoted to fact** — a hedge in the notes ("probably batched") lost its hedge in the
  prose.
- **Session drift** — an idea discussed and rejected mid-session came back as the design.
- **Stale sources** — a README describing a state the code has left. When code and docs disagree, the
  code is evidence of what runs; the README is evidence of what someone intended. That is a conflict
  to state, not to resolve by preference.

Then check the inverse: is anything in the context map's `UNKNOWNS` presented as settled, and is
every `CONFLICT` still visible in the document?

## Pass 2: completeness

- Does the document achieve the goal from the plan?
- Can the stated audience act on it without the session context that produced it?
- Are the constraints and limitations that would change a reader's decision present?
- Are the decisions that shaped the subject recorded, with their costs?
- Are open questions stated as open, rather than absent?
- Does anything in the plan's `STRUCTURE` have no counterpart in the document?

Missing is not the same as excluded. Excluded is a decision you can defend and mention at delivery;
missing means the pass found a gap.

## Pass 3: structure

- Heading levels nest without skipping (`##` → `###`, never `##` → `####`).
- Table of contents matches the headings exactly, in order, per the template's `toc` setting.
- Internal links resolve; anchors match the slugs of real headings.
- Code fences are closed and language-tagged.
- Tables have matching column counts in every row.
- The closing summary is present and is a landing, not a replay of the document.
- No placeholder survived: `[...]`, `TODO`, `TBD`, `<name>`, an unfilled template line.
- No section is empty. An empty section means the material was not there — cut it, or state what is
  missing and why.

## Pass 4: visuals

- Each diagram carries a relationship that prose handles badly. If it restates a list, cut it.
- Nothing in it is invented — every node, edge, cardinality and transition traces to a source.
- Diagram and surrounding text agree, including after edits.
- Mermaid syntax is valid: balanced brackets, quoted labels with spaces or reserved words,
  participants declared before use.
- No table duplicates a diagram's content.
- Each diagram has a line of prose telling the reader what to look at.

## Pass 5: readability

- No wall of text where a list or table gives faster access.
- No table where prose reads better — check that the grid is not there for looks.
- Acronyms and project-internal terms expanded on first use.
- Repetition removed. The same explanation in two sections means one of them is the real home.
- The first screen — title, purpose, table of contents — tells a reader whether this is the document
  they need.
- Terminology consistent throughout: one name per concept, matching what the code calls it.

## What to do with what you find

| Finding | Action |
|---|---|
| claim contradicted by a source | fix it |
| claim no source supports | delete it, or state it as an open question |
| claim supported but softly | qualify it, and say what would confirm it |
| sources disagree | move it to the inconsistencies section |
| section empty because material is missing | cut the section and note the gap at delivery |
| diagram containing an invented edge | remove the edge, or the diagram |

If the pass changes what the document *concludes* — not just how it is worded — say so at delivery
rather than shipping the corrected version silently. The user was working from the earlier version
in their head.
