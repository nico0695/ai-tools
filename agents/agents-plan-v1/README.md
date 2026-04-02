# agents-plan-v1 — Multi-Agent Technical Analysis & Migration System

> Full system survey. Version v1.1.

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Map](#agent-map)
3. [The Orchestrator: technical-orchestrator](#the-orchestrator-technical-orchestrator)
4. [Agent Interaction Flow](#agent-interaction-flow)
5. [Full Workflow (State Machine)](#full-workflow-state-machine)
6. [Communication Protocol (I/O)](#communication-protocol-io)
7. [Context File System](#context-file-system)
8. [Critical Analysis: Pros, Cons & Improvements](#critical-analysis-pros-cons--improvements)

---

## Overview

This system implements a **multi-agent pipeline** for managing complex technical tasks: architecture migrations, large-scale refactoring, technical debt resolution, and project analysis. The core design is a 4-phase state machine where **no phase can advance without explicit user approval**.

The system produces two persistent artifacts as the source of truth:
- `SURVEY_[Topic].md` — assessment of the current codebase state
- `PLAN_[Topic].md` — executable roadmap with stages and a status table

---

## Agent Map

| Agent | File | Model | Role | Scope |
|-------|------|-------|------|-------|
| `technical-orchestrator` | `technical-orchestrator.agent.md` | opus | Main conductor | Orchestration & UX |
| `structure-scanner` | `structure-scanner.agent.md` | sonnet | Structure scanner | Read-only |
| `deep-context-analyzer` | `deep-context-analyzer.agent.md` | opus | Line-by-line analysis | Read-only |
| `survey-generator` | `survey-generator.agent.md` | sonnet | Technical writer | Write (docs only) |
| `strategic-planner` | `strategic-planner.agent.md` | opus | Plan architect | Write (docs only) |
| `stage-executor` | `stage-executor.agent.md` | opus | Code executor | Write (code + plan) |
| `qa-validator` | `qa-validator.agent.md` | sonnet | Quality inspector | Read-only + Bash |

---

## The Orchestrator: technical-orchestrator

### What it is and what it does

The `technical-orchestrator` is the **single entry point** of the system and acts as a technical Project Manager. It does not read or write code directly. Its exclusive responsibilities are:

1. **Receive the objective** from the user (what to migrate, refactor, or analyze)
2. **Delegate** all technical operations to the specialized sub-agents
3. **Synthesize** results into brief responses (max. 3–4 lines)
4. **Present options** to the user before advancing to the next phase
5. **Manage workflow state** through SURVEY/PLAN files (not chat memory)

### Orchestrator guardrails

The orchestrator operates under strict behavioral rules:

- **Absolute delegation**: Never scans directories, analyzes code, or writes documents itself.
- **Context protection**: JSON payloads returned by sub-agents are never printed in the chat — only synthesized.
- **Context purge**: When a phase closes (SURVEY or PLAN generated), it is sealed. The orchestrator trusts exclusively the generated file.
- **Explicit authorization**: Never advances to the next phase without user approval.
- **25-turn limit**: If context degrades, it suggests restarting the conversation by referencing the existing files.
- **Write tool restriction**: Only used for saving context files, never for creating code or documents.

### Skip capability

- If `SURVEY_[Topic].md` already exists → can skip to Phase 3 (confirming `project_context` first)
- If `PLAN_[Topic].md` already exists → can skip to Phase 4 (confirming `project_context` first)

---

## Agent Interaction Flow

The orchestrator invokes each agent with **explicit structured parameters** using predefined templates. Each sub-agent returns a **structured JSON** that the orchestrator synthesizes.

### Flow diagram

```
User
  │
  ▼
technical-orchestrator
  │
  ├─── Phase 0 ──► stack detection (package manager, language, framework, bundler, test runner, docs folder)
  │               └─► user confirms project_context
  │
  ├─── Phase 1 ──► structure-scanner  (quick mapping)
  │               └─► deep-context-analyzer (deep analysis)
  │                       └─► [JSON findings] ──► orchestrator synthesizes
  │
  ├─── Phase 2 ──► survey-generator (receives: raw_analysis_data)
  │               └─► writes SURVEY_[Topic].md
  │                       └─► [JSON confirm] ──► orchestrator confirms
  │
  ├─── Phase 3 ──► strategic-planner (reads: SURVEY_[Topic].md)
  │               └─► writes PLAN_[Topic].md
  │                       └─► [JSON confirm] ──► orchestrator summarizes stages
  │
  └─── Phase 4 (loop) ──► stage-executor (executes 1 stage)
                          └─► qa-validator (validates changes)
                                  └─► [JSON verdict] ──► orchestrator reports
                                          └─► (repeats for each stage)
```

### I/O contracts per agent

| Agent | Key inputs | Key output |
|-------|-----------|------------|
| `structure-scanner` | target_directories, patterns_to_search, project_context | JSON: findings, god_files, circular_deps |
| `deep-context-analyzer` | target_files, documentation_files, analysis_goal, project_context | JSON: findings, dependency_map |
| `survey-generator` | raw_analysis_data, topic_objective, output_path, project_context | JSON: status, file_path |
| `strategic-planner` | survey_file_path, output_plan_path, user_directives, project_context | JSON: status, file_path |
| `stage-executor` | plan_file_path, stage_id, project_context | JSON: status, files_modified, snapshot_sha, alerts |
| `qa-validator` | modified_files, regression_docs, stage_executed, project_context | JSON: verdict, alerts, runtime_validation |

---

## Full Workflow (State Machine)

### Phase 0: Project Initialization
1. Orchestrator detects the stack (package manager, language, framework, bundler, test runner, docs folder)
2. Presents findings to the user and waits for confirmation
3. Stores confirmed values as `project_context` — passed to every sub-agent from this point on
4. Determines the default output directory for SURVEY and PLAN files

### Phase 1: Discovery & Analysis
1. Orchestrator asks the user for target directories and the main objective
2. Invokes `structure-scanner` → structure mapping
3. Invokes `deep-context-analyzer` → deep analysis of critical files
4. Presents synthesized findings and asks whether to generate the Survey

### Phase 2: Documentation
1. Invokes `survey-generator` with the raw data and `project_context`
2. `SURVEY_[Topic].md` is generated
3. **PHASE CLOSED** — raw data is purged from context

### Phase 3: Strategic Planning
1. Receives optional user directives
2. Invokes `strategic-planner` with the SURVEY and `project_context`
3. `PLAN_[Topic].md` is generated
4. **PHASE CLOSED** — survey details are purged from context

### Phase 4: Execution & QA Loop
For each stage in the plan:
1. Reads the status table from PLAN.md (source of truth)
2. Presents the next stage and **waits for authorization**
3. Invokes `stage-executor` (which runs a git snapshot first — Step 0)
4. Invokes `qa-validator` immediately after (with stack detection — Step 3A)
5. Reports result: ✅ Success / ⚠️ Warning / ❌ Error
6. Advances only if the user confirms

---

## Communication Protocol (I/O)

### Interactivity triggers

Each sub-agent has **escalation triggers** that halt execution and require a user decision:

| Trigger | Agent | Condition |
|---------|-------|-----------|
| Directive vs. reality conflict | `strategic-planner` | User directives contradict a critical blocker in the survey |
| Multiple valid paths | `strategic-planner` | >1 valid strategy with different trade-offs |
| Code/plan desync | `stage-executor` | Code is not in the state the plan expects |
| Massive side effect | `stage-executor` | Change affects files outside the stage's scope |
| Ambiguous instructions | `stage-executor` | Plan instructions are vague or contradictory |
| Critical/High in QA | `qa-validator` | Confirmed regression or memory leak detected |
| Contradictory data | `survey-generator` | Scanner and analyzer produce incompatible data |
| High volume (>100 findings) | `survey-generator` | No clear grouping directive provided |

### Orchestrator error handling

If a sub-agent returns an error, the orchestrator presents:
- [A] Retry
- [B] Skip and continue
- [C] Abort workflow

---

## Context File System

In v1.1, the automatic `memory:` system was replaced by an explicit **CONTEXT FILE PROTOCOL** applied consistently across all agents. No agent writes files automatically or uses hardcoded paths.

### How it works

Each agent checks whether `docs/temp/` exists in the project root. If it does, it proposes saving a context file there (e.g., `docs/temp/stage-executor-context.md`). If not, it asks the user where to save it. It always waits for explicit user confirmation before writing.

| Agent | Context file | What it stores |
|-------|-------------|----------------|
| `technical-orchestrator` | `orchestrator-context.md` | `project_context`, workflow state |
| `structure-scanner` | `structure-scanner-context.md` | Directory structures, anti-patterns found |
| `deep-context-analyzer` | `deep-context-analyzer-context.md` | Coupling hotspots, high-risk files, documentation gaps |
| `survey-generator` | `survey-generator-context.md` | Grouping strategies, category naming conventions |
| `strategic-planner` | `strategic-planner-context.md` | Architectural patterns, trade-off decisions |
| `stage-executor` | `stage-executor-context.md` | File responsibilities, trigger resolutions |
| `qa-validator` | `qa-validator-context.md` | Frequently flagged files, recurring regression patterns |

Agents that receive a `context_file_path` parameter read the existing file at the start of execution to restore prior context.

---

## Critical Analysis: Pros, Cons & Improvements

### Pros

**Solid architectural design**
- Clear separation of concerns: each agent has a single, well-defined purpose
- The "external source of truth" principle (files, not chat) is correct and robust
- The explicit state machine prevents the system from advancing uncontrolled
- Active LLM context protection (phase purge, max 3–4 line synthesis)

**Security and control**
- No agent executes code without explicit user authorization
- `stage-executor` is the only agent with write access to source code
- `qa-validator` acts as a safety net before each advance
- Conditional rollback via `snapshot_type` (stash pop / revert / git checkout)

**Structured interactivity**
- All agents have well-defined escalation triggers with concrete labeled options [A], [B], [C]
- Agents never guess: when in doubt, they escalate
- Context drift detection (>25 turns) with suggested recovery is a pragmatic solution

**Explicit context file system** *(v1.1)*
- Memory replaced by the CONTEXT FILE PROTOCOL: files in `docs/temp/` with explicit user validation before creating or updating any file.
- No hardcoded paths. No `memory:` in frontmatter. No automatic writes.

---

### Cons *(post v1.1 state)*

**File naming convention still inconsistent**
All files use `.agent.md` but the `deep-context-analyzer` file previously suggested `.sub-agent.md`. The semantic distinction between agent and sub-agent is not reinforced by the folder structure.

**Phase 0 creates tension with the orchestrator's guardrails**
The orchestrator uses `Glob` and `Read` in Phase 0 to detect the stack. This is correct and expected, but Section 2's guardrails still say "never scan directories directly" — the tension with Phase 0 should be documented as an explicit exception.

**No post-completion verification phase**
The workflow ends when the status table shows all "Done", but there is no Phase 5 smoke test or full build to validate the final result.

**25-turn limit remains heuristic**
Context drift detection based on a turn counter is fragile. Quality-based evaluation (inconsistent responses, incorrect stage references) would be more robust.

---

### Resolved in v1.1

| Original problem | Implemented solution |
|---|---|
| Hardcoded absolute paths | Removed `Agent file:` entries from orchestrator; context files have no fixed paths |
| No git snapshot before execution | `stage-executor` Step 0: stash or commit checkpoint with user validation |
| `memory: local/project` with hardcoded paths | CONTEXT FILE PROTOCOL: `docs/temp/[agent]-context.md` with confirmation |
| `qa-validator` runs without stack validation | Step 3A: detects available TypeScript/lint/tests and validates with user |
| System coupled to origin project | Phase 0: detects and validates any project's stack; `project_context` propagated to all agents |

### Pending / Future versions

- Unify file naming convention (`.agent.md` for all, no ambiguity)
- Clarify in the orchestrator's guardrails that Phase 0 is the permitted exception for using `Glob`/`Read`
- Add `dry_run: true` parameter to `stage-executor` for previewing changes without applying them
- `dependency-checker` sub-agent to validate stage dependencies in PLAN before Phase 4
- Optional Phase 5: smoke test / full build post-execution
- Git-operations agent: structured commits per stage, branch management

---

## Executive Summary

The `agents-plan-v1` system (v1.1) implements a multi-agent pipeline with clear separation of concerns, robust control mechanisms, and — since the v1.1 revision — a portable design decoupled from any specific project.

**v1.1 resolves:** hardcoded paths, memory system with fixed paths, missing pre-execution git snapshot, blind execution of validation commands, and technology stack coupling. The orchestrator now runs a Phase 0 project detection step before any workflow, propagating `project_context` to all agents.

The system is ready to be used in projects other than the original without manual modifications.
