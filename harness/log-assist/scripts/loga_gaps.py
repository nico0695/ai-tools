#!/usr/bin/env python3
"""Periodic signals that stopped: when, for how long, and whether it means anything."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, logset, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_gaps",
    "question": "which periodic signal stopped, when, and for how long",
    "use_when": "looking for an outage, or a period the screen was not reporting",
    "not_for": "concluding the screen was broken — a gap can be a scheduled power-off",
    "args": "--analysis <id> | --path <dir> [--signal heartbeat|telemetry|policy|screenshot|any] "
            "[--regex <re>] [--min-gap S] [--include-reboots]",
    "columns": "signal, from, to, duration, missed samples, kind",
    "size": "one row per gap, largest first",
    "group": "query",
}

# The baseline is derived, never fixed: telemetry is 60 s on Tizen and 300 s on webOS,
# and the largest ordinary gap per file in the corpus is 21-63 s. A single number
# either drowns in noise or misses everything.
DEFAULT_FACTOR = 3.0
# One occurrence of a signal can write two lines seconds apart (`Screenshot API called`
# then `Screenshot Uploaded`, 6.5 s later). Counting both halves the measured cadence
# and turns every normal interval into a gap. The built-in signals match only the
# completion line; this guard covers custom ones.
SAME_OCCURRENCE_S = 30.0


def duration(seconds: float) -> str:
    if seconds < 120:
        return f"{seconds:.0f} s"
    if seconds < 7200:
        return f"{seconds / 60:.0f} min"
    return f"{seconds / 3600:.1f} h"


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--signal", default="any", choices=("any", *sorted(logfmt.SIGNALS)))
    parser.add_argument("--regex", default=None, help="a custom signal, matched on the message")
    parser.add_argument("--min-gap", type=float, default=None,
                        help="seconds; default is 3x the measured median cadence")
    parser.add_argument("--include-reboots", action="store_true")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    if args.regex:
        try:
            signals = {"custom": re.compile(args.regex)}
        except re.error as exc:
            envelope.ok = False
            envelope.warn(f"invalid regex: {exc}")
            cli.emit(envelope, "", args, {"error": "bad regex"})
            return cli.EXIT_ARGS
    elif args.signal == "any":
        signals = dict(logfmt.SIGNALS)
    else:
        signals = {args.signal: logfmt.SIGNALS[args.signal]}

    gaps, baselines, corrections = [], [], []

    # A gap belongs to a screen, not to a file: the largest real gap in the corpus
    # (31.6 h) sits between two consecutive files of one screen, and a per-file scan
    # cannot see it. Each event keeps its own file so citations stay exact.
    for members in logset.by_screen(target.files).values():
        members = sorted(members, key=lambda f: f.first.timestamp if f.first else None)
        label = ", ".join(f.alias for f in members)

        for item in members:
            for jump in logfmt.backward_jumps(item.events):
                corrections.append({
                    "file": item.alias, "at": tg.cite(item, jump["to"], target),
                    "seconds": jump["seconds"], "kind": jump["kind"],
                    "offset_ms": jump["offset_ms"],
                })

        for name, matcher in signals.items():
            stream = [(item, event) for item in members for event in item.events
                      if logfmt.search(matcher, event) and not event.is_epoch]
            stream.sort(key=lambda pair: pair[1].timestamp)

            kept = []
            for pair in stream:
                if kept and (pair[1].timestamp - kept[-1][1].timestamp).total_seconds() \
                        < SAME_OCCURRENCE_S:
                    continue
                kept.append(pair)
            collapsed, stream = len(stream) - len(kept), kept
            if len(stream) < 3:
                continue

            cadence = logfmt.cadence_of([e.timestamp for _, e in stream])
            if not cadence["median"]:
                envelope.warn(f"{label}/{name}: median cadence is 0, so absence cannot be "
                              f"measured; skipped")
                continue
            if collapsed:
                envelope.warn(f"{label}/{name}: {collapsed} line(s) belong to an occurrence "
                              f"already counted and were collapsed before measuring")
            if cadence["mode_share"] < 0.5:
                envelope.warn(f"{label}/{name}: only {cadence['mode_share']:.0%} of intervals "
                              f"sit at the dominant value, so this signal is not periodic "
                              f"enough for a gap to mean much")

            threshold = args.min_gap if args.min_gap is not None \
                else cadence["median"] * DEFAULT_FACTOR
            baselines.append({"screen": label, "signal": name, "median": cadence["median"],
                              "threshold": threshold, "samples": len(stream)})

            for (before_file, before), (after_file, after) in zip(stream, stream[1:]):
                seconds = (after.timestamp - before.timestamp).total_seconds()
                if seconds < threshold:
                    continue
                crosses = before_file is not after_file
                has_boot = crosses or any(
                    before.number < e.number < after.number
                    for e in before_file.events if e.is_boot)
                gaps.append({
                    "screen": label,
                    "file": label if crosses else before_file.alias,
                    "signal": name,
                    "from": tg.cite(before_file, before.number, target),
                    "to": tg.cite(after_file, after.number, target),
                    "seconds": seconds,
                    "missed": max(0, int(round(seconds / cadence["median"])) - 1),
                    "kind": "between-files" if crosses else
                            ("reboot" if has_boot else "outage"),
                })

    listed = [g for g in gaps if args.include_reboots or g["kind"] != "reboot"]
    listed.sort(key=lambda g: -g["seconds"])
    hidden = len(gaps) - len(listed)

    envelope.total = len(listed)
    page = cli.paginate(listed, args.offset, args.limit)
    envelope.returned = len(page)
    if hidden:
        envelope.warn(f"{hidden} gap(s) contain a boot and are not listed; add --include-reboots")
    if not listed:
        envelope.warn("no gap above the derived baseline; this is a result, not an error")
    fixes = [c for c in corrections if c["kind"] == "clock-correction"]
    if fixes:
        envelope.warn(f"{len(fixes)} backward time step(s) are clock corrections against the "
                      f"server, not gaps — the jump equals the reported `Server time offset`")

    body = ["# Gaps", "", f"- {len(listed)} gap(s) above the baseline", ""]
    if baselines:
        body += ["## Baselines used", "",
                 "| Screen | Signal | Median cadence | Gap threshold | Occurrences |",
                 "|---|---|---|---|---|"]
        for base in baselines[:12]:
            body.append(f"| `{base['screen']}` | {base['signal']} | {base['median']:.0f} s "
                        f"| {base['threshold']:.0f} s | {base['samples']} |")
        if len(baselines) > 12:
            body.append(f"| … | {len(baselines) - 12} more | | | |")
    if page:
        body += ["", "## Gaps", "",
                 "| Screen | Signal | From | To | Duration | Missed | Kind |",
                 "|---|---|---|---|---|---|---|"]
        for gap in page:
            body.append(f"| `{gap['file']}` | {gap['signal']} | `{gap['from']}` | `{gap['to']}` "
                        f"| {duration(gap['seconds'])} | {gap['missed']} | `{gap['kind']}` |")
    if corrections:
        body += ["", "## Backward time steps", "",
                 "| File | At | Step | Kind | Reported offset |", "|---|---|---|---|---|"]
        for item in corrections:
            offset = f"{item['offset_ms']} ms" if item["offset_ms"] is not None else "—"
            body.append(f"| `{item['file']}` | `{item['at']}` | {item['seconds']:.2f} s "
                        f"| `{item['kind']}` | {offset} |")
    body += ["", "A gap is not a failure: a screen off by schedule looks the same. The threshold "
                 "is 3x the cadence measured in these logs, not a fixed number.",
             "`between-files` means the screen's own files do not join up — a coverage hole, "
             "not necessarily an outage."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args,
             {"gaps": page, "baselines": baselines, "clock_steps": corrections})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
