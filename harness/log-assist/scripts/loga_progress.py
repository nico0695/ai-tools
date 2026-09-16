#!/usr/bin/env python3
"""Validate state.toml, derive what is actually done, and suggest the next step."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "loga_progress",
    "question": "is this state.toml valid, what is done, and what comes next",
    "use_when": "resuming an analysis, or after any step writes",
    "not_for": "changing state — this script never writes",
    "args": "<id> [--root PATH]",
    "columns": "validation problems, derived progress, suggested next step",
    "size": "under 30 lines",
    "group": "state",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("id")
    parser.add_argument("--root", default=None)
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    root = Path(args.root).resolve() if args.root else an.repo_root()
    target = an.analyses_root(root) / args.id

    if not (target / "state.toml").is_file():
        envelope.ok = False
        envelope.warn(f"no state.toml under {target.as_posix()}")
        envelope.suggest(f"loga_new.py {args.id}")
        cli.emit(envelope, "", args, {"error": "not found"})
        return cli.EXIT_INPUT

    item = an.Analysis(args.id, target)
    try:
        state = an.load_state(item)
    except tomllib.TOMLDecodeError as exc:
        envelope.ok = False
        envelope.warn(f"state.toml is not valid TOML: {exc}")
        cli.emit(envelope, "", args, {"error": "unparseable"})
        return cli.EXIT_INPUT

    problems = an.validate_state(state, args.id)
    progress = an.derive_progress(item)
    step, why = an.suggest_next(state, progress)

    declared = state.get("status")
    if declared == "analyzing" and not progress["inventory"]:
        problems.append("status is `analyzing` but there is no record/inventory.md")
    if declared == "concluded" and not progress["report"]:
        problems.append("status is `concluded` but reports/ is empty")

    envelope.total = envelope.returned = len(problems)
    envelope.ok = not problems
    for problem in problems:
        envelope.warn(problem)
    if not problems and step.startswith("loga-"):
        envelope.suggest(f"delegate {step}")

    done = [name for name in ("intake", "inventory", "analyze", "report") if progress[name]]
    body = "\n".join([
        f"# Progress — `{args.id}`", "",
        f"- status: `{declared}` · outcome: `{state.get('outcome') or '—'}` "
        f"· round: {state.get('current_round', 0)}",
        f"- logs: {progress['log_count']} file(s)" + (
            f" · inbox: {progress['inbox_count']} waiting"
            if progress["inbox_count"] else ""),
        f"- done: {', '.join(done) if done else 'nothing yet'}",
        f"- next: **{step}** — {why}", "",
        "## Validation", "",
        ("state.toml is valid." if not problems else
         "\n".join(f"- {problem}" for problem in problems)),
    ])
    cli.emit(envelope, body, args, {
        "id": args.id, "status": declared, "progress": progress,
        "next": step, "why": why, "problems": problems,
    })
    return cli.EXIT_OK if not problems else cli.EXIT_INPUT


if __name__ == "__main__":
    cli.run(main)
