#!/usr/bin/env python3
"""Lines matching a catalog pattern or a regex, with citations and verbatim excerpts."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, reader, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_grep",
    "question": "which lines match this pattern or regex",
    "use_when": "you know what you are looking for",
    "not_for": "an overview — that is loga_summary",
    "args": "--regex <re> | --pattern <catalog-id> [--level L] [--component C] "
            "[--before N] [--after N]",
    "columns": "citation, level, component, excerpt",
    "size": "one row per match, paginated",
    "group": "query",
}


def load_pattern(pattern_id: str) -> tuple[str | None, str]:
    catalog = Path(__file__).resolve().parent / "catalog.toml"
    if not catalog.is_file():
        return None, "scripts/catalog.toml does not exist yet"
    with catalog.open("rb") as handle:
        data = tomllib.load(handle)
    for entry in data.get("patterns", []):
        if entry.get("id") == pattern_id:
            return entry.get("regex"), ""
    known = ", ".join(e.get("id", "?") for e in data.get("patterns", [])[:12])
    return None, f"no pattern {pattern_id!r} in the catalog; known ids include {known}"


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--regex", default=None)
    parser.add_argument("--pattern", default=None, help="a pattern id from scripts/catalog.toml")
    parser.add_argument("--level", default=None)
    parser.add_argument("--component", default=None)
    parser.add_argument("--before", type=int, default=0)
    parser.add_argument("--after", type=int, default=0)
    parser.add_argument("--no-fold-traces", action="store_true",
                        help="show stack-trace frames as their own matches")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    if bool(args.regex) == bool(args.pattern):
        envelope.ok = False
        envelope.warn("give exactly one of --regex or --pattern")
        cli.emit(envelope, "", args, {"error": "bad args"})
        return cli.EXIT_ARGS

    expression = args.regex
    if args.pattern:
        expression, problem = load_pattern(args.pattern)
        if expression is None:
            envelope.ok = False
            envelope.warn(problem)
            cli.emit(envelope, "", args, {"error": "unknown pattern"})
            return cli.EXIT_ARGS
    try:
        matcher = re.compile(expression)
    except re.error as exc:
        envelope.ok = False
        envelope.warn(f"invalid regex: {exc}")
        cli.emit(envelope, "", args, {"error": "bad regex"})
        return cli.EXIT_ARGS

    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    hits = []
    for item in target.files:
        events = item.events
        if not args.no_fold_traces:
            events, _ = logfmt.fold_traces(events)
        for event in events:
            if args.level and event.effective_level != args.level.upper():
                continue
            if args.component and args.component.lower() not in event.component.lower():
                continue
            # Anchored against the text after the component, with the raw
            # message as fallback. Never against the line: it starts with a timestamp.
            if not logfmt.search(matcher, event):
                continue
            hits.append({
                "citation": tg.cite(item, event.number, target),
                "level": event.effective_level,
                "component": event.component or "—",
                "excerpt": reader.excerpt(event.raw_message),
                "file": item, "event": event,
            })

    envelope.total = len(hits)
    page = cli.paginate(hits, args.offset, args.limit)
    envelope.returned = len(page)

    if not hits:
        envelope.warn("no line matched; this is a result, not an error")
        if expression.startswith("^"):
            envelope.warn("the pattern is anchored with `^`: it is applied to the message, "
                          "after the level — not to the whole line, which always starts "
                          "with a timestamp")

    body = ["# Matches", "",
            f"- pattern: `{expression}`",
            f"- {len(hits)} match(es) in {len(target.files)} file(s)", ""]
    if page:
        body += ["| Citation | Level | Component | Excerpt |", "|---|---|---|---|"]
        for hit in page:
            excerpt = cli.md_cell(hit["excerpt"])
            body.append(f"| `{hit['citation']}` | {hit['level']} | `{hit['component']}` "
                        f"| {excerpt} |")
        if args.before or args.after:
            body += ["", "## Context", ""]
            for hit in page[:10]:
                item, event = hit["file"], hit["event"]
                low = max(1, event.number - args.before)
                high = min(len(item.lines), event.number + args.after)
                body.append(f"**`{hit['citation']}`**")
                body += [f"    {n:>7} {reader.truncate(item.lines[n - 1].text)}"
                         for n in range(low, high + 1)]
                body.append("")
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args,
             {"pattern": expression, "total": len(hits),
              "matches": [{k: h[k] for k in ("citation", "level", "component", "excerpt")}
                          for h in page]})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
