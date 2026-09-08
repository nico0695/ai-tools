---
name: commit-closer
description: |
  Draft commit messages and PR descriptions from Git changes or commit ranges.
  Use when explicitly invoked or the user asks to write a commit message or PR description.
  Suggest when asked to prepare a commit or PR without a specific drafting request.
---

# Commit Closer

Workflow for generating commit messages, PR descriptions, and impact analysis from staged/unstaged git changes.

## Language Policy

Respond in the user's language. For generated commit messages and PR descriptions, use the language explicitly requested by the user; otherwise follow the repository's documented language convention for that artifact, falling back to the user's language when none is documented.

The headings, questions, and prose examples below are in English for maintenance; adapt them to the selected output language. Preserve Conventional Commits types and footer keywords, identifiers, file paths, and commands in their original form.

## Workflow

Follow these steps in order. Do not skip steps.

### Step 1 — Gather user context (mandatory)

Ask the user two specific questions before doing anything else. Do not proceed until both are answered:

1. **Change description:** What did you change and why?
2. **Expected impact:** Which areas or features of the project could these changes affect?

These answers are the foundation of all output. If the user gives vague answers, ask for clarification once before proceeding.

### Step 2 — Analyze git state

Run these commands to understand what changed:

```bash
git status --short
git diff --stat HEAD
git diff HEAD
git log --oneline -1
```

If the repo has staged changes, also run:
```bash
git diff --cached --stat
git diff --cached
```

Read every modified file relevant to the change. If the project has a `docs/API_REFERENCE.md`, check if any modified module is documented there and read the relevant section to deepen the impact analysis.

For deep analysis: identify what each changed function/section does, how it's called, and what depends on it. Cross-reference with related files if needed.

### Step 3 — Generate commit messages

#### Commit format reference

Important: just one line, not include author or date in the message.

```
<type>(<scope>): <summary>

[optional body — what and why, not how]

[optional footer — BREAKING CHANGE: ..., Closes #X]
```

**Types:**

| Type | When to use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructure without behavior change |
| `perf` | Performance improvement |
| `chore` | Build, tooling, dependency updates |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `style` | Formatting, whitespace (no logic change) |
| `ci` | CI/CD config changes |
| `revert` | Reverts a previous commit |

**Scopes** — use the module or layer affected:
- Modules: `conversations`, `alerts`, `tasks`, `notes`, `links`, `images`, `reminders`, `users`, `system`
- Layers: `controller`, `services`, `repositories`, `shared`
- Infrastructure: `config`, `build`, `deps`

**Summary line rules:**
- Imperative mood: "add" not "added" or "adds"
- No period at the end
- Max 72 characters
- Lowercase after the colon

**One-liner vs full message:**
- One-liner: change is small, single area, self-evident from the diff
- Full message: affects multiple areas, has side effects, or non-obvious reasoning worth preserving

---

Generate **6 commit message options** organized into two groups:

**Group A — Full messages (with body)**
Produce 3 alternatives with different type/scope/emphasis combinations. Each must have:
- A subject line (≤72 chars, imperative, type + scope)
- A body explaining what changed and why (not how)
- Footers if applicable (BREAKING CHANGE, Closes #X)

**Group B — Simplified messages (one-liner only)**
Produce 3 alternatives — concise subject lines only. Vary the phrasing and emphasis across the 3 options.

Present all 6 clearly labeled. Ask the user which one to use (or if they want to combine elements).

### Step 4 — Generate PR description

#### PR description structure

Produce a complete PR description in the language selected by the Language Policy, adapting these headings:

**### Change description**
2–4 sentences. What was changed and why. Focus on behavior, not implementation details.

**### Modified files**
Table with columns: `File | Change type | Detail`. List every modified file — do not group or summarize.

**### Project impact**
Bullet list of affected modules or areas. Be specific: "affects the reminders REST endpoint" is better than "affects the module". Use "could affect" when not confirmed.

**### Manual review and testing checklist**
Actionable checklist with `- [ ]`. Each item must specify what to verify and in what scenario — never "check that it works".

**### Additional context** *(optional)*
Include only if relevant: migration steps, related PRs, known limitations, pending work.

---

The analysis must be strict: identify real risks, not just hypothetical ones. If a change could break something, say it clearly.

### Step 5 — Offer previous commits analysis (optional)

Ask the user:

> "Do you want to include earlier commits from the same PR? This is useful when the PR contains several commits you want summarized in the description."

If yes:
1. Ask: "How many previous commits, or back to which commit hash?"
2. Run `git log --oneline -N` (where N is the number requested) or `git log --oneline <hash>..HEAD`
3. Display the full list: hash + message for each commit
4. Ask the user to confirm the list is correct, and whether any commit should be removed from the analysis
5. Wait for explicit confirmation before proceeding
6. Once confirmed, run `git show <hash>` for each commit and incorporate their changes into the PR description and impact analysis
7. Re-generate the PR description to include all commits

### Step 6 — Final output

Present the complete output grouped in this order:

1. **Commit messages** — Group A (full) then Group B (simplified)
2. **PR description** — full PR description ready to paste
3. **Testing checklist** — extracted from the PR description, as a standalone checklist
4. **Executive summary** — 3–5 sentences maximum. What changed, why, and what needs attention. Easy to read at a glance.
5. *(Optional)* **Additional section** — only if genuinely relevant: migration notes, related work, architectural impact worth highlighting

## Rules

- Follow the Language Policy for chat and generated artifacts; preserve commands, paths, and identifiers.
- Never skip Step 1 — user context is mandatory.
- Never mark a testing item as "check that it works" — each item must specify what to verify and in what scenario.
- If a modified file is under a module's `controller/` directory, identify which interface is affected: `<module>.controller.ts` handles Slack commands/events; `<module>Web.controller.ts` handles HTTP/REST endpoints. If both are modified, call it out explicitly in the impact section.
- If the diff touches event handlers, singletons, or global state, flag it in the impact section.
- Before suggesting to commit, warn the user once: this project has Husky pre-commit hooks that run `lint + tests` automatically — if they fail, the commit will be aborted.
- Keep sentences short. Avoid filler phrases like "it is worth noting" or "it is important to mention".
