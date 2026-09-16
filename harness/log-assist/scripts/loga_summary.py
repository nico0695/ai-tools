#!/usr/bin/env python3
"""What a log is made of: levels, components, message shapes, and the errors."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, normalize, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_summary",
    "question": "what messages are here by level, component and shape, and how much is noise",
    "use_when": "getting oriented in a log before asking anything specific",
    "not_for": "the lines themselves — that is loga_grep",
    "args": "--analysis <id> | --path <dir> [--top N] [--level L] [--component C] [--errors-only]",
    "columns": "level counts, top shapes with share, components, distinct ERROR forms",
    "size": "about 40 lines at --top 20",
    "group": "query",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--top", type=int, default=20, help="how many shapes to list")
    parser.add_argument("--level", default=None)
    parser.add_argument("--component", default=None)
    parser.add_argument("--errors-only", action="store_true")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    levels, shapes, components = Counter(), Counter(), Counter()
    error_forms: dict[str, tuple] = {}
    total_events = folded_frames = 0
    differing = 0
    first_seen: dict[str, tuple] = {}

    for item in target.files:
        kept, frames = logfmt.fold_traces(item.events)
        folded_frames += sum(len(v) for v in frames.values())
        for event in kept:
            if args.level and event.effective_level != args.level.upper():
                continue
            if args.component and args.component.lower() not in event.component.lower():
                continue
            if args.errors_only and event.effective_level not in ("ERROR", "WARNING"):
                continue
            total_events += 1
            differing += 1 if event.level_differs else 0
            levels[event.effective_level] += 1
            components[event.component or "(none)"] += 1
            shape = normalize.signature(event.component, event.effective_level, event.text)
            shapes[shape] += 1
            first_seen.setdefault(shape, (item, event))
            if event.effective_level == "ERROR":
                error_forms.setdefault(shape, (item, event, 0))
                previous = error_forms[shape]
                error_forms[shape] = (previous[0], previous[1], previous[2] + 1)

    if not total_events:
        envelope.warn("nothing matched the filters; this is a result, not an error")
    if differing:
        envelope.warn(logfmt.level_note([e for f in target.files for e in f.events]) or "")
    if folded_frames:
        envelope.warn(f"{folded_frames} stack-trace frame(s) folded into their error and not "
                      f"counted as events")

    top = shapes.most_common(args.top)
    covered = sum(count for _, count in top)
    envelope.total = len(shapes)
    envelope.returned = len(top)
    envelope.suggest("loga_grep.py --regex <shape> " +
                     (f"--analysis {args.analysis}" if args.analysis else f"--path {args.path}"))

    def pct(value: int) -> str:
        return f"{100 * value / total_events:.1f} %" if total_events else "—"

    body = ["# Summary", "",
            f"- {total_events} event(s) across {len(target.files)} file(s), "
            f"{len(shapes)} distinct shape(s)",
            f"- levels: " + " · ".join(f"**{k}** {v} ({pct(v)})" for k, v in levels.most_common()),
            f"- the top {len(top)} shapes are {pct(covered)} of the volume", "",
            "## Shapes", "",
            "| # | Level · Component · Shape | Lines | Share | First |",
            "|---|---|---|---|---|"]
    for index, (shape, count) in enumerate(top, start=1):
        item, event = first_seen[shape]
        display = cli.md_cell(shape if len(shape) <= 110 else shape[:110] + "…")
        body.append(f"| {index} | `{display}` | {count} | {pct(count)} "
                    f"| `{tg.cite(item, event.number, target)}` |")

    body += ["", "## Components", "",
             " · ".join(f"`{name}` {count}" for name, count in components.most_common(12))]

    if error_forms:
        body += ["", f"## ERROR forms ({len(error_forms)} distinct)", "",
                 "| Form | Lines | First |", "|---|---|---|"]
        for shape, (item, event, count) in sorted(error_forms.items(),
                                                  key=lambda kv: -kv[1][2]):
            display = cli.md_cell(shape if len(shape) <= 110 else shape[:110] + "…")
            body.append(f"| `{display}` | {count} | `{tg.cite(item, event.number, target)}` |")

    body += ["", "Noise is derived by frequency over these logs, never from a fixed list. "
                 "Nothing is hidden from the counts."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args, {
        "events": total_events, "levels": dict(levels),
        "shapes": [{"shape": s, "count": c} for s, c in top],
        "error_forms": len(error_forms),
    })
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
