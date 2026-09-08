# Generic Skills

Project-agnostic skills with English descriptions and a small set of natural Spanish aliases.
Activate on an explicit invocation or the specific request described below. Names mentioned in
quotes, documents, examples, or requests to analyze a skill are not invocations.

Suggestions are separate from activation: offer them only when relevant to the current request,
without starting the skill, interrupting the task, or repeating a suggestion already made.

Static activation scenarios live in [evals/trigger-cases.json](./evals/trigger-cases.json).
They record expected routing (`activate`, `suggest`, `none`), not measured activation results.

## [4r-review](./4r-review/SKILL.md)

Risk-tiered 4R review (Risk, Readability, Reliability, Resilience) of a frozen diff, branch, or PR. Triage decides how much review the target deserves - from none (docs-only) to all four lenses plus a refuter pass that corroborates severe inferential findings. Reports in chat; optionally saves a review ledger. Distinct from code-review: triggered explicitly by name, sized by risk instead of a user-chosen depth.

Activate only when explicitly requested as `4r-review`, `4r`, or "revisión 4R".
During a requested code review, suggest once if the already inspected diff exceeds 600 added-plus-deleted
lines or 15 changed files. Neither threshold activates the skill automatically. Count binary files
as files without inventing line counts, and do not broaden inspection just to evaluate the trigger.
The existing internal triage threshold of more than 400 lines remains unchanged; it determines review
depth after activation, not whether to suggest the skill.

## [code-review](./code-review/SKILL.md)

Reviews local commits or branch changes and returns evidence-based findings, each with a suggested fix. Light mode flags critical issues only; deep mode adds cross-module impact, convention checks, and a second pass for side effects that only appear when changes combine.

Activate when explicitly invoked or asked to review code changes in a diff, commits, a branch, or a PR.
An explicitly requested alternative review protocol takes precedence. Reviewing prose or merely
discussing a review does not activate this skill.

## [commit-closer](./commit-closer/SKILL.md)

Turns staged or unstaged changes into 6 commit message options (Conventional Commits), a full PR description with impact analysis, and a manual testing checklist. Generated commits and PR descriptions follow the requested language, then the repository's documented language convention for that artifact, then the user's language. Chat follows the user's language.

Activate when explicitly invoked or asked to write a commit message or PR description.
Suggest when asked to prepare a commit or PR without a specific drafting request.
Generic change analysis does not activate it; drafting does not authorize committing or publishing a PR.

## [doc-writer](./doc-writer/SKILL.md)

Turns the available context - the session, code, a diff, a spec, sources you point at - into a structured Markdown document that is grounded in evidence instead of filled in from plausibility. Picks the document type the situation calls for, uses an editable template from `assets/templates/`, agrees on a plan before writing, adds tables and diagrams only where they carry something prose does not, and validates the result back against the sources. Interactive or auto.

Activate when explicitly invoked or asked to create technical documentation, such as an ADR,
runbook, API reference, or architecture document. Suggest when the user wants technical decisions
or knowledge recorded. Mentioning an ADR or asking to explain a README does not activate it.

## [grill-me](./grill-me/SKILL.md)

Relentless interview that stress-tests a plan, design, or decision until you and the agent reach a shared understanding. Models the plan as a decision tree and asks the current frontier each round, every question with a recommended answer. Looks up facts itself instead of asking for them; the decisions are yours. Works cold, from a spec or diff, or mid-session without re-asking what you already decided. Writes nothing - the output is a final read-back of what was decided, what was assumed, and what got parked for somebody else or for a prototype.

Activate when explicitly invoked or asked to "question me about this plan", "preguntame", or
"hazme preguntas" about a plan, design, or decision. Suggest when the user wants to uncover
assumptions or unresolved decisions before implementation. Questions for a third party belong to
`questionnaire`; a general request for an opinion does not start an interview.

## [judgment-day](./judgment-day/SKILL.md)

Adversarial dual review: two blind, independent judges review the same frozen target and convergence decides what counts - both agree = confirmed, one reports = suspect, incompatible claims = contradiction escalated to you. Works on code or on a single document. Ends in exactly APPROVED or ESCALATED. The expensive, opt-in path; never run on a target 4r-review already covered.

Activate when explicitly invoked, requested as "juicio final", or asked for two independent reviewers.
Suggest when the user wants corroboration of a review before a critical decision.
"Judge this" or a generic second opinion does not by itself request two independent reviewers.

## [prototype](./prototype/SKILL.md)

Builds throwaway code that answers one design question by running it. Three shapes: a terminal app to drive a state model by hand, several structurally different UI variants on one route, or a one-shot probe against code or an API that already runs. It also tells you when a prototype is not the right instrument.

Activate only when explicitly invoked or asked to build a prototype, including "crear un prototipo".
General testing, exploration, mockups, and requests mentioning only PoC or spike do not activate it.
There is no contextual suggestion trigger for this skill.

## [questionnaire](./questionnaire/SKILL.md)

Turns a decision you cannot resolve alone into a questionnaire for the person who can. Reads the current session or a set of changes to find the open decisions, interviews you briefly about the shape of the problem, and confirms both the structure and the wording before writing anything. Output is a file or chat-ready text, from an editable template in `assets/`.

Activate when explicitly invoked or asked to create a questionnaire, "armá un cuestionario", or
prepare questions for someone else. Suggest when an unresolved decision requires information from
another person. "I don't know" alone is insufficient; interviewing the user about their own plan
belongs to `grill-me`.

## [resolving-merge-conflicts](./resolving-merge-conflicts/SKILL.md)

Resolves an in-progress merge, rebase, cherry-pick, or revert by tracing what each side was trying to do, instead of picking whichever hunk reads better. Never runs a git write command: it edits the files and hands back the closing command.

Activate when explicitly invoked or asked to resolve conflicts, including "resolver merge" or
"resolver conflictos", with Git context established in the message or conversation.
Explanations, unmerged status output alone, and requests to merge without resolving conflicts
do not activate it.
