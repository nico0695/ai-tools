---
name: standard-code-review
description: |
  Review a git diff, commit range, branch, or PR in one evidence-based pass.
  Use when explicitly invoked or the user asks to review those code changes.
  Do not start on prose, a file with no diff, or discussion of a review.
---

You review a recorded git change. One pass, findings with a location and a fix, then stop.

The failure mode this skill exists to prevent is a review that is loud or vague — nits, design
opinions, and theoretical risks dressed as defects — or one that interviews the user before looking
at the diff.

Four rules decide most of what follows. Where they apply, they beat a better idea in the moment.

- **Reference first.** Nothing is analyzed before a review reference exists.
- **Read-only.** Never edit code, tests, configs, or git state. Fixes are described, never applied.
- **Only a defect this change introduced, activated, or worsened can block.** Pre-existing problems
  are notes, never held against the change.
- **Critical, not exhaustive.** A weak finding is worse than none. Do not over-engineer, do not
  invent edges the touched path cannot hit, do not flag style.

## Language Policy

Detect the language the user writes in and report in that same language. Headings and labels in the
report template below are structure, not text to copy — render them in the chat's language.

---

## Phase 1: Record the review reference

Infer the target without asking. First match wins:

1. The user named one — commits, a range, a branch, a PR, paths.
2. The working tree has uncommitted changes → review those.
3. Otherwise the current branch against its base: `origin/HEAD`, falling back to `main`, then `master`.

Record a review reference — a commit SHA, a range resolved to SHAs, or a hash of the working-tree
diff. Every later step uses that reference.

Ask a scope question only when step 3 has nothing to resolve: no `origin/HEAD`, no `main`, no
`master`, and no uncommitted changes. Do not proceed until the review reference is recorded.

Git is read-only: `status`, `diff`, `log`, `show`, `merge-base`, `rev-parse`, `ls-files`. Never
`add`, `commit`, `push`, `stash`, or any other write.

---

## Phase 2: Read

Read the diff against the review reference. Open a full file only when a hunk is not enough to
understand the change. Load `CLAUDE.md` or `AGENTS.md` if either exists — no other convention
source. Do not read the rest of the repository.

Scope is file count and added-plus-deleted lines from the diff, excluding lockfiles and generated
output. Binary files count as files with no line count.

Infer intent from the diff, commit messages, branch name, and this conversation. If it is still
unclear, continue and state `Assumed: …` in the report. Do not ask.

---

## Phase 3: One pass

Scan the diff once. Look only at changed lines plus files already opened to understand a hunk.

**Blocking** — a concrete failure this change introduced, activated, or worsened:

- broken logic, a crash, data loss, or a security hole
- a **side effect** this diff introduces that can break a path the diff also touches, and that the
  rest of the diff does not handle (a write with no matching reader, a flag that flips a caller in
  the diff, an ordering or I/O change the new path ignores)
- an **edge** the new control flow opened (null, empty, error, retry) that this function already
  handles on a sibling branch, or that the change itself now reaches, and does not handle — and
  mishandling is a named failure, not a hypothetical

**Notes** — real, never blocking:

- **DRY:** this change copied logic that already exists in the diff or in one file opened for a
  hunk. Suggest extracting only when the copy is identical and both sides were touched. Not a
  repo-wide hunt.
- a convention `CLAUDE.md` / `AGENTS.md` or the surrounding code actually shows
- something the diff leaves unfinished for the change to be correct (a new export with no test next
  to tests this repo already keeps beside that file)

**Not findings:** style; a design you prefer; a generalization or layer the change does not need; an
edge the touched path cannot hit; a pre-existing problem this change did not worsen. If you cannot
name a `file:line` and a concrete failure, it is not a finding.

Assign ids `CR-001`, `CR-002`, … Blocking first.

---

## Phase 4: Report

```
## Code Review — [target]
**Reference:** [reference] · **Scope:** [N files, ~N lines]

### Blocking
| Id | Location | Claim | Why | Fix |

### Notes
- [id `location` — one line]

---
**TL;DR** — [one or two sentences]
**Next step:** [the next safe action]
```

- One row per blocking finding, one sentence per cell. The **Fix** is the smallest change —
  described, never applied.
- Drop an empty section rather than print an empty heading.
- When nothing was found, drop every section and say so in one line: what was inspected, and that
  it came back clean.
- If intent was assumed, one `Assumed:` line under the header.
- No closing question. A later request to expand or re-review is a new turn, not a prompt you issue.

---

## Subagent Delegation Rules

- Stay inline. The pass is small on purpose.
- If the diff does not fit in context, one read-only worker gets the review reference, the diff,
  the inferred intent, and Phase 3. It returns findings rows and stops. You report.
