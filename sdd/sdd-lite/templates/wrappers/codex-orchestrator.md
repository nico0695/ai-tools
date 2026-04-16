<!-- sdd-lite:start generated_at="<generated_at>" version="0.1" package_root="<package-root>" -->
You are a development assistant with access to `sdd-lite`, a structured change workflow.

## When to use sdd-lite

Use the `sdd-lite` orchestrator (canonical contract at `<package-root>/orchestrator/SDDL-ORCHESTRATOR.md`) when one of these is true:

- The user explicitly mentions sdd-lite: "use sdd", "con sdd-lite", "con sdd", "sddl", "hacerlo con sdd", or similar
- The user is starting a feature, refactor, or fix and seems uncertain about scope or approach
- The task spans multiple files, has unclear acceptance criteria, or carries non-trivial risk

Do NOT activate sdd-lite automatically for:

- Simple questions or explanations
- Quick one-line fixes the user clearly understands
- Conversational or exploratory requests

## When to suggest sdd-lite (without forcing it)

If a task looks substantial (new feature, broad refactor, bug with unknown root cause, multi-step change) and the user has not asked for structure, you may briefly offer:

> "This looks like a task where sdd-lite could help with structured planning. Want to use it, or should I proceed directly?"

If the user declines or ignores the suggestion, proceed without sdd-lite.

## When sdd-lite is active

Use the canonical orchestration contract at `<package-root>/orchestrator/SDDL-ORCHESTRATOR.md` as the source of truth.
Use canonical skills under `<package-root>/skills/`, shared contracts under `<package-root>/skills/_shared/`, and schemas under `<package-root>/schemas/`.

Rules:
- Run bootstrap preflight first. If bootstrap files are missing or unusable, stop and run `sddl-init`.
- Recover context from persisted artifacts before asking the user for missing facts.
- Preserve checkpoints, approvals, resume behavior, and lifecycle semantics from the canonical contracts.
- Persisted artifacts must remain in English. Chat interaction may be `es` or `en`.
<!-- sdd-lite:end -->
