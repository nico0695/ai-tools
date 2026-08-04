# Generic Skills

Project-agnostic skills. Each triggers on its own phrases, or can be called by name.

## [code-review](./code-review/SKILL.md)

Reviews local commits or branch changes and returns evidence-based findings, each with a suggested fix. Light mode flags critical issues only; deep mode adds cross-module impact, convention checks, and a second pass for side effects that only appear when changes combine.

Use when:
- Reviewing your own commits before opening a PR
- Checking a branch someone else wrote
- You want to know what a change might break elsewhere

## [commit-closer](./commit-closer/SKILL.md)

Turns staged or unstaged changes into 6 commit message options (Conventional Commits), a full PR description with impact analysis, and a manual testing checklist. Output is in Spanish.

Use when:
- Wrapping up work and you need a commit message
- Writing a PR description
- A PR accumulated several commits you want summarized together

## [prototype](./prototype/SKILL.md)

Builds throwaway code that answers one design question by running it. Three shapes: a terminal app to drive a state model by hand, several structurally different UI variants on one route, or a one-shot probe against code or an API that already runs. It also tells you when a prototype is not the right instrument.

Use when:
- A design question came up mid-conversation and prose will not settle it
- Starting from a spec where one assumption is riskier than the rest
- You want to see options side by side before committing to one
- You want to know what a change would break before making it

## [questionnaire](./questionnaire/SKILL.md)

Turns a decision you cannot resolve alone into a questionnaire for the person who can. Reads the current session or a set of changes to find the open decisions, interviews you briefly about the shape of the problem, and confirms both the structure and the wording before writing anything. Output is a file or chat-ready text, from an editable template in `assets/`.

Use when:
- An answer depends on infra, a DBA, product, a client, or another team
- You need questions ready for a meeting or an async ask
- A session ended with several decisions left open and you need someone else to close them

## [resolving-merge-conflicts](./resolving-merge-conflicts/SKILL.md)

Resolves an in-progress merge, rebase, cherry-pick, or revert by tracing what each side was trying to do, instead of picking whichever hunk reads better. Never runs a git write command: it edits the files and hands back the closing command.

Use when:
- You are stuck mid-merge or mid-rebase
- `git status` shows unmerged paths
- You are not sure which side to keep
