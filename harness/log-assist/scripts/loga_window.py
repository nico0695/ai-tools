#!/usr/bin/env python3
"""What happened around a point in the logs."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, reader, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_window",
    "question": "what happened around this timestamp or this file:line",
    "use_when": "you have a citation and need its context",
    "not_for": "searching — that is loga_grep",
    "args": "--at <alias-or-file>:<line> | --time '<YYYY-MM-DD HH:MM:SS>' "
            "[--before N] [--after N] [--merge]",
    "columns": "citation, line, verbatim text",
    "size": "before + after + 1 lines per file",
    "group": "query",
}

_AT = re.compile(r"^(?P<file>.+):(?P<line>\d+)$")


def find_file(files, token: str):
    token = token.strip()
    for item in files:
        if item.alias.upper() == token.upper() or item.name == token \
                or item.path.as_posix().endswith(token):
            return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--at", default=None, help="alias-or-filename:line")
    parser.add_argument("--time", default=None, help="'YYYY-MM-DD HH:MM:SS'")
    parser.add_argument("--before", type=int, default=20)
    parser.add_argument("--after", type=int, default=20)
    parser.add_argument("--merge", action="store_true",
                        help="interleave every file around the same moment")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    if bool(args.at) == bool(args.time):
        envelope.ok = False
        envelope.warn("give exactly one of --at or --time")
        cli.emit(envelope, "", args, {"error": "bad args"})
        return cli.EXIT_ARGS

    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    windows: list[tuple] = []          # (file, low, high)
    moment: datetime | None = None

    if args.at:
        match = _AT.match(args.at)
        if not match:
            envelope.ok = False
            envelope.warn("--at must look like F1:1234 or name.log:1234")
            cli.emit(envelope, "", args, {"error": "bad --at"})
            return cli.EXIT_ARGS
        item = find_file(target.files, match.group("file"))
        if item is None:
            envelope.ok = False
            envelope.warn(f"no file matching {match.group('file')!r}; run loga_scan for aliases")
            cli.emit(envelope, "", args, {"error": "unknown file"})
            return cli.EXIT_INPUT
        number = int(match.group("line"))
        if not 1 <= number <= len(item.lines):
            envelope.ok = False
            envelope.warn(f"line {number} is outside {item.alias} ({len(item.lines)} lines)")
            cli.emit(envelope, "", args, {"error": "line out of range"})
            return cli.EXIT_INPUT
        anchor = logfmt.parse_line(number, item.lines[number - 1].text)
        moment = anchor.timestamp if anchor else None
        windows.append((item, max(1, number - args.before),
                        min(len(item.lines), number + args.after)))
        if args.merge:
            if moment is None:
                envelope.warn("the anchor line has no usable timestamp, so --merge is skipped")
            else:
                for other in target.files:
                    if other is not item:
                        windows.append(around_time(other, moment, args))
    else:
        try:
            moment = datetime.strptime(args.time.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            envelope.ok = False
            envelope.warn("--time must be 'YYYY-MM-DD HH:MM:SS'")
            cli.emit(envelope, "", args, {"error": "bad --time"})
            return cli.EXIT_ARGS
        chosen = target.files if args.merge else target.files[:1]
        if not args.merge and len(target.files) > 1:
            envelope.warn(f"{len(target.files)} files in scope; showing {chosen[0].alias} only. "
                          f"Add --merge to see them together")
        for item in chosen:
            windows.append(around_time(item, moment, args))

    if len(windows) > 1:
        envelope.warn("timestamps carry no timezone, so lining up different screens in time "
                      "is an assumption, not a fact")

    body = ["# Window", ""]
    if moment:
        body.append(f"- anchor: `{logfmt.stamp(moment)}`")
    shown = 0
    epoch_seen = False
    for item, low, high in windows:
        if low is None:
            body += ["", f"**{item.alias}** — nothing within range", ""]
            continue
        body += ["", f"**{item.alias}** — `{tg.cite(item, low, target)}` … "
                     f"`{tg.cite(item, high, target)}`", "```"]
        for number in range(low, high + 1):
            text = item.lines[number - 1].text
            body.append(f"{number:>7} {reader.truncate(text)}")
            shown += 1
            if text.startswith("1969-") or text.startswith("1970-"):
                epoch_seen = True
        body.append("```")

    if epoch_seen:
        envelope.warn("this window crosses the epoch boundary of a cold boot: wall-clock "
                      "differences across it are meaningless. Read it in line order")

    envelope.total = envelope.returned = shown
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args,
             {"anchor": logfmt.stamp(moment) if moment else None, "lines": shown})
    return tg.partial_exit(target)


def around_time(item, moment, args):
    """The line closest to `moment` in this file, and the range around it."""
    best, distance = None, None
    for event in item.events:
        gap = abs((event.timestamp - moment).total_seconds())
        if distance is None or gap < distance:
            best, distance = event.number, gap
    if best is None:
        return (item, None, None)
    return (item, max(1, best - args.before), min(len(item.lines), best + args.after))


if __name__ == "__main__":
    cli.run(main)
