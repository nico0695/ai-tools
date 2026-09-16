"""The analysis folder: layout, id rule, and reading state.toml.

Normative source: skills/_shared/loga-persistence-contract.md.
Scripts read TOML; they never serialize it. loga_new copies templates/state.toml
and substitutes the mechanical fields, so the structure and its comments survive.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

ANALYSES_DIR = "analyses"
ID_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>")

REQUIRED_FIELDS = ("id", "title", "created", "status")
STATUS_VALUES = ("new", "analyzing", "needs-info", "concluded", "closed")
OUTCOME_VALUES = ("confirmed", "probable", "inconclusive", "not-an-issue")
ROUND_RESULTS = ("progress", "no-progress")

# Files loga_new creates. record/*.md are deliberately NOT seeded: loga_progress
# derives progress from which of them exist, so an empty one would read as done.
SEEDED = ("state.toml", "SUMMARY.md")
SUBDIRS = ("logs", "record", "record/runs", "reports")

# Where the user drops logs before they belong to an analysis. Emptied by
# loga-import, which moves what it recognizes into analyses/<id>/logs/.
INBOX = "inbox"

# Which artifact proves a step ran, in flow order.
STEP_ARTIFACTS = (
    ("intake", "record/intake.md"),
    ("inventory", "record/inventory.md"),
    ("analyze", "record/findings.md"),
    ("report", "reports"),
)


def repo_root() -> Path:
    """The clone root, two levels above this module."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Analysis:
    id: str
    path: Path

    @property
    def state_path(self) -> Path:
        return self.path / "state.toml"

    @property
    def logs_dir(self) -> Path:
        return self.path / "logs"

    @property
    def record_dir(self) -> Path:
        return self.path / "record"

    @property
    def reports_dir(self) -> Path:
        return self.path / "reports"


def analyses_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / ANALYSES_DIR


def find_analyses(root: Path | None = None) -> list[Analysis]:
    base = analyses_root(root)
    if not base.is_dir():
        return []
    return sorted(
        (Analysis(p.name, p) for p in base.iterdir() if p.is_dir() and (p / "state.toml").is_file()),
        key=lambda a: a.id,
    )


def load_state(analysis: Analysis) -> dict:
    with analysis.state_path.open("rb") as handle:
        return tomllib.load(handle)


def validate_state(state: dict, analysis_id: str | None = None) -> list[str]:
    """Every problem found, as one message each. Empty list means valid."""
    problems: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in state:
            problems.append(f"missing required field `{field}`")
        elif isinstance(state[field], str):
            if not state[field].strip():
                problems.append(f"required field `{field}` is empty")
            elif PLACEHOLDER_RE.search(state[field]):
                problems.append(f"required field `{field}` still holds the template placeholder "
                                f"{state[field]!r}")

    if analysis_id and state.get("id") and state["id"] != analysis_id:
        problems.append(f"`id` is {state['id']!r} but the folder is {analysis_id!r}")
    if state.get("id") and not ID_RE.match(str(state["id"])):
        problems.append(f"`id` {state['id']!r} is not <ref>-<slug>: letters, digits and hyphens only")

    for field in ("created", "updated"):
        value = state.get(field)
        if isinstance(value, str) and value and not DATE_RE.match(value):
            problems.append(f"`{field}` is {value!r}; dates are ISO strings like \"2026-09-13\"")

    status = state.get("status")
    if status is not None and status not in STATUS_VALUES:
        problems.append(f"`status` is {status!r}; allowed: {', '.join(STATUS_VALUES)}")

    outcome = state.get("outcome", "")
    if outcome and outcome not in OUTCOME_VALUES:
        problems.append(f"`outcome` is {outcome!r}; allowed: empty, {', '.join(OUTCOME_VALUES)}")
    if outcome and status not in ("concluded", "closed"):
        problems.append(f"`outcome` is set but `status` is {status!r}; an outcome needs `concluded`")

    for index, entry in enumerate(state.get("rounds", []), start=1):
        if entry.get("result") not in ROUND_RESULTS:
            problems.append(f"rounds[{index}].result is {entry.get('result')!r}; "
                            f"allowed: {', '.join(ROUND_RESULTS)}")
    return problems


def derive_progress(analysis: Analysis) -> dict:
    """What actually exists on disk, independent of what status claims."""
    done = {}
    for step, relative in STEP_ARTIFACTS:
        target = analysis.path / relative
        done[step] = any(target.glob("*.md")) if target.is_dir() else target.is_file()
    logs = sorted(p for p in analysis.logs_dir.rglob("*") if p.is_file()) \
        if analysis.logs_dir.is_dir() else []
    done["logs"] = len(logs) > 0
    done["log_count"] = len(logs)
    inbox = repo_root() / INBOX
    done["inbox_count"] = sum(1 for p in inbox.rglob("*")
                              if p.is_file() and not p.name.startswith(".")) \
        if inbox.is_dir() else 0
    return done


def suggest_next(state: dict, progress: dict) -> tuple[str, str]:
    """The next step and why. Advisory: the orchestrator still routes."""
    status = state.get("status")
    if status == "closed":
        return "none", "the analysis is closed"
    if not progress["intake"]:
        return "loga-intake", "there is no record/intake.md; gate 1 blocks any log query"
    if not progress["logs"]:
        if progress.get("inbox_count"):
            return "loga-import", (f"logs/ is empty, and {INBOX}/ holds "
                                   f"{progress['inbox_count']} file(s) to triage")
        return "ask-for-logs", "logs/ is empty"
    if not progress["inventory"]:
        return "loga-inventory", "logs are present but there is no record/inventory.md"
    if status == "needs-info":
        return "loga-intake", "status is needs-info"
    if not progress["report"]:
        return "loga-analyze", "inventory is done; run analysis rounds"
    if status == "concluded":
        return "close", "a report exists and the analysis is concluded"
    return "loga-report", "a report may be emitted, or keep analyzing"
