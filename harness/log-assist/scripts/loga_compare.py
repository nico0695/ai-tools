#!/usr/bin/env python3
"""Screen by metric: where the screens agree and where they diverge."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, logset, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_compare",
    "question": "where do these screens agree and where do they diverge",
    "use_when": "two or more screens are in scope, especially in the same sync group",
    "not_for": "a single screen — there is nothing to compare",
    "args": "--analysis <id> | --path <dir> [--screens A,B] [--group G]",
    "columns": "one row per metric, one column per screen",
    "size": "about 12 rows",
    "group": "query",
}

PLAYING_RE = re.compile(r'^Playing Playlist "(?P<name>.+)"$')
HB_OK_RE = re.compile(r"^Heartbeat received from server$")
HB_FAIL_RE = re.compile(r"^Heartbeat Sync failed")
MISSING_RE = re.compile(r"Missing Content: (?P<n>\d+) files")


def measure(files, target) -> dict:
    """Every metric for one screen, aggregating all of its files."""
    events = [e for item in files for e in item.events]
    folded = []
    for item in files:
        kept, _ = logfmt.fold_traces(item.events)
        folded += kept
    identity = next((f.identity for f in files if f.identity.machine), files[0].identity)

    def first_cite(matcher):
        for item in files:
            for event in item.events:
                if logfmt.search(matcher, event):
                    return tg.cite(item, event.number, target)
        return None

    def last_match(matcher):
        found = None
        for item in files:
            for event in item.events:
                hit = logfmt.search(matcher, event)
                if hit:
                    found = (hit, tg.cite(item, event.number, target))
        return found

    ordered = [(item, e) for item in files for e in item.events if not e.is_epoch]
    playing = last_match(PLAYING_RE)
    missing = [m for item in files for e in item.events
               if (m := logfmt.search(MISSING_RE, e))]

    return {
        "files": ", ".join(f.alias for f in files),
        "platform": identity.platform or "—",
        "player": ", ".join(identity.player_version) or "—",
        "boots": sum(f.boots for f in files),
        "first": logfmt.stamp(ordered[0][1].timestamp) if ordered else "—",
        "last": logfmt.stamp(ordered[-1][1].timestamp) if ordered else "—",
        "errors": sum(1 for e in folded if e.effective_level == "ERROR"),
        "hb_ok": sum(1 for e in events if logfmt.search(HB_OK_RE, e)),
        "hb_fail": sum(1 for e in events if logfmt.search(HB_FAIL_RE, e)),
        "playlist": playing[0].group("name") if playing else "—",
        "playlist_cite": playing[1] if playing else None,
        "group": identity.sync_group or "—",
        "role": ("master" if identity.own_ip and identity.own_ip in identity.masters
                 else "member" if identity.members else "—"),
        "missing_content": len(missing),
        "missing_max_files": max((int(m.group("n")) for m in missing), default=0),
        "missing_cite": first_cite(MISSING_RE),
        "lines": sum(len(f.lines) for f in files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--screens", default=None, help="comma-separated screen names or ids")
    parser.add_argument("--group", default=None, help="restrict to one sync group")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    screens = logset.by_screen(target.files)
    if args.group:
        screens = {k: v for k, v in screens.items()
                   if any(args.group.lower() in (f.identity.sync_group or "").lower() for f in v)}
    if args.screens:
        wanted = [w.strip().lower() for w in args.screens.split(",")]
        screens = {k: v for k, v in screens.items()
                   if any(w in k.lower() or any(w in (f.identity.machine or "").lower()
                                                for f in v) for w in wanted)}
    if len(screens) < 2:
        envelope.warn(f"{len(screens)} screen(s) in scope: there is nothing to compare. "
                      f"Widen --path, or drop --screens/--group")
        cli.emit(envelope, "# Comparison\n\nFewer than two screens in scope.", args,
                 {"screens": list(screens)})
        return cli.EXIT_OK

    columns = {}
    for key, files in screens.items():
        named = next((f.identity.machine for f in files
                      if f.identity.machine and not f.identity.machine_ambiguous), None)
        if named:
            label = named
        else:
            ip = next((f.identity.own_ip for f in files if f.identity.own_ip), "")
            label = f"{ip} (name ambiguous)" if ip else key
        columns[label] = measure(files, target)

    names = list(columns)
    envelope.total = envelope.returned = len(names)
    if len({c["platform"] for c in columns.values()}) > 1:
        envelope.warn("these screens are not on the same platform: cadences and ranges are "
                      "not comparable between them")
    if len({c["player"] for c in columns.values()}) > 1:
        envelope.warn("player versions differ across these screens")
    envelope.warn("timestamps carry no timezone, so any time alignment between screens is an "
                  "assumption")

    rows = [
        ("files", lambda c: c["files"]),
        ("platform", lambda c: c["platform"]),
        ("player", lambda c: c["player"]),
        ("sync group", lambda c: cli.md_cell(c["group"])),
        ("sync role", lambda c: c["role"]),
        ("lines", lambda c: str(c["lines"])),
        ("boots", lambda c: str(c["boots"])),
        ("first line", lambda c: c["first"]),
        ("last line", lambda c: c["last"]),
        ("ERROR lines", lambda c: str(c["errors"])),
        ("heartbeat ok", lambda c: str(c["hb_ok"])),
        ("heartbeat failed", lambda c: str(c["hb_fail"])),
        ("current playlist", lambda c: cli.md_cell(c["playlist"])),
        ("missing content", lambda c: (f"{c['missing_content']} line(s), "
                                       f"up to {c['missing_max_files']} file(s)")
                                      if c["missing_content"] else "—"),
    ]

    header = "| Metric | " + " | ".join(cli.md_cell(n) for n in names) + " |"
    body = ["# Comparison", "",
            f"- {len(names)} screen(s) from {len(target.files)} file(s)", "",
            header, "|---|" + "---|" * len(names)]
    divergent = []
    for label, getter in rows:
        values = [getter(columns[n]) for n in names]
        if label not in ("files", "lines", "first line", "last line") and len(set(values)) > 1:
            divergent.append(label)
        marker = " 🔴" if label in divergent else ""
        body.append(f"| **{label}**{marker} | " + " | ".join(values) + " |")

    body += ["", "## Divergences", ""]
    body += ([f"- **{d}**" for d in divergent] if divergent
             else ["- none: these screens agree on every compared metric"])
    body += ["", "Columns are screens, not files: two files of one screen are aggregated. "
                 "A cell that could not be measured is `—`, never zero."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args,
             {"screens": {n: columns[n] for n in names}, "divergent": divergent})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
