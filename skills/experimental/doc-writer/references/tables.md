# Tables

Read this when the material is homogeneous and comparable. A table is a claim that every row has the
same shape — when that is true it is the densest form available, and when it is false it forces the
writer to pad cells and the reader to scan an inconsistent grid.

Contents:
- [When a table is the right form](#when-a-table-is-the-right-form)
- [Patterns](#patterns)
- [Writing rules](#writing-rules)

## When a table is the right form

| Material | Form |
|---|---|
| several items sharing the same attributes | table |
| options compared on fixed criteria | table |
| one item with many attributes | definition list or prose |
| items whose explanations run to a paragraph | headed subsections |
| a sequence where order carries meaning | numbered list |
| two rows | prose — the table costs more than it saves |

The test: could a reader answer a question by scanning one column? If yes, table. If they have to
read every cell in full, the grid is adding structure without adding access.

## Patterns

Start from the closest pattern and adapt the columns to what the sources actually establish. Drop a
column you cannot fill for most rows — a column of "unknown" says nothing a note under the table
would not say better.

**Components / responsibilities** — the backbone of an architecture or overview document.

| Component | Responsibility | Depends on |
|---|---|---|
| `orders-api` | accepts and validates order requests | `catalog`, Postgres |

**API endpoints** — the index above the per-endpoint detail, not a replacement for it.

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `POST` | `/orders` | create an order | Bearer |

**Configuration** — mark what is required, and give the real default, not a plausible one.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_POOL_SIZE` | no | `10` | max concurrent DB connections |

**Risks** — the mitigation column is what makes it actionable; without it this is a worry list.

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|

**Decisions** — one row per decision, and the consequence stated even when it is favorable.

| Decision | Rationale | Consequence |
|---|---|---|

**States** — pairs naturally with a state diagram: the diagram shows the shape, the table carries the
meaning.

| State | Meaning | Next states |
|---|---|---|

**Comparison** — criteria as rows when there are more criteria than options, options as rows when
there are more options. Keep cells to a few words; a comparison table that needs sentences is a
section per option.

| Criterion | Option A | Option B |
|---|---|---|

**Errors** — what the caller sees and what they should do about it.

| Code | Meaning | Caller action |
|---|---|---|

**Inventory / coverage** — what exists and what state it is in, for reports and audits.

| Item | Status | Notes |
|---|---|---|

## Writing rules

- **Header row says what the column contains**, not a generic label. `Purpose` beats `Description`
  when the column holds purposes.
- **One fact per cell.** A cell with a semicolon list is a missing column or a missing row.
- **Consistent grain.** Do not mix a module and a function in the same `Component` column; the reader
  infers they are peers.
- **Code style for identifiers** — paths, variables, endpoints, types — so they survive scanning.
- **Empty means unknown, and say which kind.** Use `—` for not applicable and a note under the table
  for not established. A blank cell is ambiguous between the two.
- **Sort deliberately** — by importance, by call order, by lifecycle. Source-file order is a default,
  not a decision.
- **Do not duplicate a diagram.** If a table lists exactly the edges a diagram draws, keep whichever
  answers the reader's question faster and cut the other.
- **Long tables get an intro line** saying what to look for. Twenty rows with no framing is a data
  dump.
