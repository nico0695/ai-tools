#!/usr/bin/env python3
"""Create an analysis folder from the templates."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "loga_new",
    "question": "create the folder and starting state for a new analysis",
    "use_when": "the user asks to analyze a new incident",
    "not_for": "filling in what the incident is — the orchestrator writes that",
    "args": "<id> [--jira KEY] [--root PATH]",
    "columns": "created paths",
    "size": "a handful of lines",
    "group": "state",
}

# Only the mechanical fields. Everything semantic is the orchestrator's to write,
# with the template's comments still in the file to guide it.
MECHANICAL = ("id", "created", "updated")


def substitute(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = re.sub(rf'^({key} = )"<[^"]*>"', rf'\1"{value}"', text, count=1, flags=re.MULTILINE)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("id", help="<ref>-<slug>, e.g. DEX-1234-black-screen")
    parser.add_argument("--jira", default=None, help="Jira key, when there is one")
    parser.add_argument("--root", default=None, help="clone root (defaults to this repo)")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    root = Path(args.root).resolve() if args.root else an.repo_root()

    if not an.ID_RE.match(args.id):
        envelope.ok = False
        envelope.warn(f"{args.id!r} is not a valid id: letters, digits and hyphens, "
                      f"no spaces, no slashes, no dates")
        cli.emit(envelope, "", args, {"error": "invalid id"})
        return cli.EXIT_ARGS

    target = an.analyses_root(root) / args.id
    if target.exists():
        envelope.ok = False
        envelope.warn(f"{target.as_posix()} already exists; nothing was written")
        envelope.suggest(f"loga_progress.py {args.id}")
        cli.emit(envelope, "", args, {"error": "already exists"})
        return cli.EXIT_INPUT

    templates = root / "templates"
    if not (templates / "state.toml").is_file():
        envelope.ok = False
        envelope.warn(f"templates not found under {templates.as_posix()}")
        cli.emit(envelope, "", args, {"error": "templates missing"})
        return cli.EXIT_INPUT

    today = date.today().isoformat()
    for sub in an.SUBDIRS:
        (target / sub).mkdir(parents=True, exist_ok=True)

    state = substitute((templates / "state.toml").read_text(encoding="utf-8"),
                       {"id": args.id, "created": today, "updated": today})
    if args.jira:
        state = re.sub(r'^(jira = )""', rf'\1"{args.jira}"', state, count=1, flags=re.MULTILINE)
    (target / "state.toml").write_text(state, encoding="utf-8", newline="\n")
    shutil.copyfile(templates / "SUMMARY.md", target / "SUMMARY.md")

    created = [f"{target.relative_to(root).as_posix()}/{s}/" for s in an.SUBDIRS]
    created += [f"{target.relative_to(root).as_posix()}/{f}" for f in an.SEEDED]
    envelope.returned = envelope.total = len(created)
    envelope.warn("record/*.md are not seeded on purpose: loga_progress reads their "
                  "presence as proof a step ran")
    envelope.suggest(f"loga_search.py --text {args.id.split('-')[0]}")
    envelope.suggest(f"loga_progress.py {args.id}")

    body = "\n".join([
        f"# Created `{args.id}`", "",
        "| Path | |", "|---|---|",
        *[f"| `{path}` | |" for path in created], "",
        "Next: the orchestrator fills `title` in `state.toml` (and `jira`, `tags`, "
        "`incident_window` when known), then runs `loga-intake`.",
        "The template's comments stay in the file and list the allowed values.",
    ])
    cli.emit(envelope, body, args, {"id": args.id, "created": created})
    return cli.EXIT_OK


if __name__ == "__main__":
    cli.run(main)
