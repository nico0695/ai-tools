#!/usr/bin/env python3
"""What files are here, which screen each belongs to, and what they cover."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, logset, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_scan",
    "question": "what files are here, which screen and platform, what range, do they parse",
    "use_when": "starting an inventory, or after new logs arrive",
    "not_for": "finding a specific message — that is loga_grep",
    "args": "--analysis <id> | --path <dir> [--refresh]",
    "columns": "alias, file, screen, platform, player, range, lines, parse_rate, boots",
    "size": "one row per file plus a coverage block",
    "group": "query",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--refresh", action="store_true", help="rewrite record/runs/manifest.json")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    rows = []
    for item in target.files:
        identity = item.identity
        first, last = item.first, item.last
        screen = identity.machine or "—"
        if identity.machine_ambiguous:
            screen = f"{identity.machine} ⚠"
            envelope.warn(f"{item.alias}: `Machine:` holds an <IP> <MAC>, not a screen name; "
                          f"identity resolved by machine_id or IP instead")
        rows.append({
            "alias": item.alias,
            "file": logset.relative(item.path, target.citation_root),
            "screen": screen,
            "screen_key": identity.screen_key,
            "platform": identity.platform or "—",
            "player": ", ".join(identity.player_version) or "—",
            "first": logfmt.stamp(first.timestamp) if first else "—",
            "last": logfmt.stamp(last.timestamp) if last else "—",
            "lines": len(item.lines),
            "parse_rate": round(item.parse_rate, 6),
            "boots": item.boots,
            "group": identity.sync_group or "—",
        })

    screens = logset.by_screen(target.files)
    groups = sorted({f.identity.sync_group for f in target.files
                 if f.identity.sync_group and f.identity.sync_group != "undefined"})
    groupless = [f.alias for f in target.files
                 if f.identity.sync_group == "undefined"]
    if groupless:
        envelope.warn(f"{', '.join(groupless)} report `Group: undefined` — "
                      f"a node without a group, not a group without a master")
    envelope.total = envelope.returned = len(rows)

    if len(screens) < len(target.files):
        shared = [f"{key}: {', '.join(f.alias for f in group)}"
                  for key, group in screens.items() if len(group) > 1]
        envelope.warn("some files are the same screen — " + " · ".join(shared))
    unknown = [f.alias for f in target.files if not f.identity.screen_key]
    if unknown:
        envelope.warn(f"identity unresolved for {', '.join(unknown)}; they are kept separate, "
                      f"never merged")

    manifest_note = ""
    if target.analysis_dir and (args.refresh or
                                not (target.analysis_dir / logset.MANIFEST).is_file()):
        written = logset.write_manifest(target.analysis_dir, target.files, target.citation_root)
        manifest_note = f"\nManifest: `{logset.relative(written, target.citation_root)}`"

    envelope.suggest("loga_summary.py " + (f"--analysis {args.analysis}" if args.analysis
                                           else f"--path {args.path}"))
    body = "\n".join([
        "# Scan", "",
        f"- {len(rows)} file(s), **{len(screens)} distinct screen(s)**, "
        f"{len(groups) or 'no'} sync group(s)", "",
        "| Alias | Screen | Platform | Player | First | Last | Lines | parse_rate | Boots |",
        "|---|---|---|---|---|---|---|---|---|",
        *[f"| `{r['alias']}` | {cli.md_cell(r['screen'])} | {r['platform']} | {r['player']} | {r['first']} "
          f"| {r['last']} | {r['lines']} | {r['parse_rate']} | {r['boots']} |" for r in rows],
        "",
        "## Coverage", "",
        *[f"- **{key}** — {', '.join(f.alias for f in group)}"
          f"{' (same screen, different files)' if len(group) > 1 else ''}"
          for key, group in screens.items()],
        "",
        "Files are never merged by name or line count: two files of the same size are "
        "different screens until their identity says otherwise.",
        *tg.legend(target), manifest_note,
    ])
    cli.emit(envelope, body, args, {"files": rows, "screens": list(screens)})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
