---
name: commit-closer
description: |
  Draft commit messages and PR descriptions from Git changes or commit ranges.
  Use when explicitly invoked or the user asks to write a commit message or PR description.
  Suggest when asked to prepare a commit or PR without a specific drafting request.
---

# Commit Closer

Turns a set of changes into a commit message, a PR description, or both — read from git, never
written to git.

Three rules decide most of what follows:

- **Read-only with git, always.** `status`, `diff`, `log`, `show`, `merge-base`, `rev-parse`,
  `ls-files` — nothing that writes. Never run `add`, `commit`, `push`, `stash`, or any other
  state-changing command, and never offer to.
- **Draft what was asked for, not a fixed bundle.** A commit message request drafts a commit
  message. A PR description request drafts a PR description. Only draft both when both were asked
  for, or when the request doesn't say which one.
- **Never invent.** No ticket number, no `BREAKING CHANGE`, no risk or impact statement without
  something in the diff, the branch name, or the conversation that supports it.

## Language Policy

Chat follows the user's language. The drafted commit message and PR description are written in
English by default; use another language only when the user explicitly asks for it. Conventional
Commits types, footer keywords, identifiers, file paths, and commands stay in their original form
regardless of language.

## Step 1 — Resolve what to draft

First match wins:

1. The user asked for a commit message → `commit`.
2. The user asked for a PR description → `pr`.
3. The user asked for both, or didn't say which → `both`.

## Step 2 — Resolve the source (one question, always)

Before reading any diff, check what's available, read-only:

| Source | How to check |
|---|---|
| staged changes | `git diff --cached --name-only` |
| working tree (including new files) | `git diff --name-only` + `git ls-files --others --exclude-standard` |
| branch against its base | resolve the base from `git symbolic-ref refs/remotes/origin/HEAD` (or ask once if it doesn't resolve), then `git merge-base HEAD {base}` and `git diff --name-only {merge-base}..HEAD` for the file count |
| an explicit commit range | only if the user names one; `git diff --name-only {range}` for the file count |

Also check what was worked on in this session — it informs which source to propose, not which
source to use without asking.

Ask exactly one question, every time, even when only one source has changes: list every source
that has changes, with its file count, and mark one as the proposed default based on the session's
context. Include the explicit-range option as an escape hatch. If drafting a PR is in scope
(`pr` or `both`), fold a second choice into the same question: whether to include validation
steps.

If no source has any changes, say so and stop.

If the repository has no commits yet (`HEAD` doesn't resolve), drop any source and command that
depends on `HEAD` and work from staged and working-tree changes only.

## Step 3 — Read the changes

Read the diff for the resolved source. Open a full file only where the diff itself isn't enough to
understand what changed — don't read every modified file and its dependents by default.

## Step 4 — Fill in the why (ask only if still missing)

Check whether the reason for the change and its likely impact are already clear from the diff, the
branch name, or the conversation. If not, ask one question covering both. Never ask what was
changed — that comes from the diff.

## Step 5 — Draft the commit message

Format:

```
type(scope): summary

[optional body — what and why, not how]

[optional footer — BREAKING CHANGE: ..., Closes #X]
```

**Type** — first match wins:

| Type | When to use |
|---|---|
| `fix` | Corrects something that was broken |
| `feat` | Adds a new capability |
| `perf` | Same behavior, measurably faster |
| `refactor` | Restructures without changing behavior |
| `docs` | Only if the entire change is documentation |
| `test` | Only if the entire change is tests |
| `ci` | Only if the entire change is CI/CD config |
| `build` | Only if the entire change is build or dependency config |
| `style` | Only if the entire change is formatting, with no logic change |
| `chore` | Only if nothing above fits |
| `revert` | Reverts a previous commit |

**Scope** — the module or directory the change is actually about, when one is obvious from the
diff. Leave it out rather than force one.

**Summary line** — imperative mood ("add", not "added"), no trailing period, lowercase after the
colon, at most 72 characters counting `type(scope): ` and the summary together.

**Prefer one line.** Add a body only when the change spans several areas, has a side effect that
isn't obvious from the summary, or the reasoning is worth preserving. The body is two to four short
sentences: the problem, then what changes in practice — not how it was implemented. No file paths,
no function or class names, no line numbers. A name is fine when it identifies a recognizable
feature or flow (an endpoint, a command, a flag) — not when it names an internal detail.

**Footers** — `BREAKING CHANGE` only with a concrete break visible in the diff; `Closes #X` only
when the number is inferable from the branch name, the session, or an explicit user statement.
Never invented. Mark either one for the user to confirm rather than asserting it silently.

**If the diff mixes unrelated concerns**, say the change should be split into separate commits
instead of writing one message that covers all of it.

Produce one recommended message plus two alternatives that change the angle, not the format (for
example: framed around the mechanism vs. the symptom). Each alternative gets one line naming how it
differs from the recommendation. Only the recommended message carries a body.

## Step 6 — Draft the PR description

Use `assets/pr-description.md`. Same content discipline as the commit message: what changed and why,
minimal technical detail, no file paths, a name only when it identifies a recognizable feature or
flow.

- **What** — the changes grouped by topic, not by file. Never an exhaustive file table; the PR's
  own diff view already lists every file.
- **Why** — short: the problem or motivation, in plain terms.
- **Impact** — include only when at least one of these is true; otherwise omit the section
  entirely:
  - it changes something other code or people depend on: an API or contract, a data shape or
    migration, configuration or environment variables, or an existing capability that's removed or
    renamed;
  - it has an effect outside what "What" already describes — a different flow or module than the
    one that was changed;
  - it touches several areas at once, such that a problem in one might not surface while reviewing
    another.
  Size alone (a large diff in one place) does not qualify.
- **How to validate** — only if the user chose to include it in Step 2. Short, numbered steps; each
  one names what to do and what result confirms it worked. Never "check that it works."

## Step 7 — Present the output

Print each drafted text in its own copyable block, commit message first, then PR description, in
whatever combination Step 1 resolved. No duplicate checklist, no separate executive summary. Close
with a short TL;DR: what changed and what needs attention, in one or two sentences.

## Rules

- Follow the Language Policy for chat versus drafted output.
- Never run or suggest a git command that writes.
- Ask at most two questions in a run: the Step 2 source question (with the validation-steps choice
  folded in when relevant), and the Step 4 why question, only if still needed after reading the
  diff.
- Never present a file table in the PR description.
- Never mark a validation step as "check that it works" — name what to verify and in what scenario.
- Keep sentences short. Avoid filler phrases like "it is worth noting" or "it is important to
  mention".
