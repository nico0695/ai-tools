---
template:
  id: generic
  name: Generic Technical Document
  description: Free-form technical document with a solid backbone. The fallback when no specialized type fits, and the base to adapt when a proposed type would leave most sections empty.
  audience: [any]
  use_when:
    - the material does not match a specialized document type
    - the user asked for "a document" without naming a shape
    - a proposed type would leave most of its sections unfillable
  required: [overview, content, summary]
  optional: [context, open-questions, references]
  visuals: [any, as the material demands]
  toc: optional
---

# [Title]

> [One or two lines: what this document covers and who it is for.]

## Table of Contents

- [Overview](#overview)
- [Context](#context)
- [Content section](#content-section)
- [Open Questions](#open-questions)
- [References](#references)
- [Summary](#summary)

## Overview

[What this is about and why it exists, in a paragraph. A reader who stops here should still have the
right idea.]

## Context

[What the reader needs to know before the substance: the situation, the constraints, what was already
true. Cut this section if the overview already carries it.]

## [Content section]

[The substance. Shape these sections around the material and the reader's task — this template has no
opinion about how many there are or what they are called. Use tables for homogeneous comparable
information and diagrams for non-linear relationships; skip both when prose is clearer.]

## Open Questions

[What the sources did not establish, and what would settle it. Delete the section only if there is
genuinely nothing open.]

| Question | Why it matters | Who could answer |
|---|---|---|

## References

[Sources this document was built from: files, PRs, specs, conversations. What a reader follows to
verify a claim.]

## Summary

[What this documents, what matters most in it, what is binding, and what the reader should now know.
A landing, not a replay.]
