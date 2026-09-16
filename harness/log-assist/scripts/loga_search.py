#!/usr/bin/env python3
"""Search across analyses by reading every state.toml at call time."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "loga_search",
    "question": "which other analyses match this status, platform, version, tag, ticket or title",
    "use_when": "creating an analysis, or looking for a related case",
    "not_for": "searching inside logs — that is loga_grep",
    "args": "[--status S] [--outcome O] [--platform P] [--player-version V] [--tag T] "
            "[--jira K] [--text S] [--root PATH]",
    "columns": "id, status, outcome, platform, screens, updated, title",
    "size": "one row per match",
    "group": "state",
}


def matches(state: dict, args) -> bool:
    def has(field: str, wanted: str) -> bool:
        value = state.get(field) or []
        values = value if isinstance(value, list) else [value]
        return any(wanted.lower() == str(v).lower() for v in values)

    if args.status and state.get("status") != args.status:
        return False
    if args.outcome and state.get("outcome") != args.outcome:
        return False
    if args.platform and not has("platform", args.platform):
        return False
    if args.player_version and not has("player_version", args.player_version):
        return False
    if args.tag and not has("tags", args.tag):
        return False
    if args.jira and str(state.get("jira", "")).lower() != args.jira.lower():
        return False
    if args.text:
        haystack = " ".join(str(state.get(f, "")) for f in ("id", "title", "jira"))
        haystack += " " + " ".join(str(t) for t in state.get("tags", []))
        if args.text.lower() not in haystack.lower():
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    for flag in ("--status", "--outcome", "--platform", "--player-version", "--jira", "--tag", "--text"):
        parser.add_argument(flag, default=None)
    parser.add_argument("--root", default=None)
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    root = Path(args.root).resolve() if args.root else an.repo_root()

    if args.status and args.status not in an.STATUS_VALUES:
        envelope.ok = False
        envelope.warn(f"--status must be one of {', '.join(an.STATUS_VALUES)}")
        cli.emit(envelope, "", args, {"error": "bad status"})
        return cli.EXIT_ARGS

    rows = []
    for item in an.find_analyses(root):
        try:
            state = an.load_state(item)
        except tomllib.TOMLDecodeError:
            envelope.warn(f"{item.id}: state.toml is not valid TOML, skipped")
            continue
        if matches(state, args):
            rows.append({
                "id": item.id,
                "status": state.get("status", ""),
                "outcome": state.get("outcome", ""),
                "platform": ", ".join(state.get("platform", [])),
                "screens": ", ".join(state.get("screens", [])),
                "updated": state.get("updated", ""),
                "title": state.get("title", ""),
            })

    envelope.total = len(rows)
    page = cli.paginate(rows, args.offset, args.limit)
    envelope.returned = len(page)
    if not rows:
        envelope.warn("no analysis matched; this is a result, not an error")

    body = "\n".join([
        "# Analyses", "",
        "| id | status | outcome | platform | screens | updated | title |",
        "|---|---|---|---|---|---|---|",
        *[f"| `{r['id']}` | {r['status']} | {r['outcome'] or '—'} | {r['platform'] or '—'} "
          f"| {r['screens'] or '—'} | {r['updated'] or '—'} | {r['title']} |" for r in page],
    ]) if page else "# Analyses\n\nNo match."
    cli.emit(envelope, body, args, {"matches": rows})
    return cli.EXIT_OK


if __name__ == "__main__":
    cli.run(main)
