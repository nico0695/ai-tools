#!/usr/bin/env python3
"""How RAM and CPU moved, per session, measured against this corpus and nothing else."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_resources",
    "question": "how did RAM and CPU move per session, and are samples missing",
    "use_when": "the complaint mentions slowness, freezing or a suspected memory leak",
    "not_for": "declaring a leak — there is no product threshold, only the observed range",
    "args": "--analysis <id> | --path <dir> [--samples] [--baseline min:max]",
    "columns": "session, samples, cpu min/max/mean, ram min/max/mean, trend, cadence, missing",
    "size": "one row per session",
    "group": "query",
}

TELEMETRY_RE = re.compile(r"^CPU: (?P<cpu>[\d.]+)%\. Used RAM: (?P<ram>[\d.]+) Mb$")
# A second, undocumented source inside the status block: no component prefix and a
# different wording, so the telemetry regex misses it. Counted apart, never merged.
STATUS_RE = re.compile(r"^CPU usage: (?P<cpu>[\d.]+)%\. Used RAM: (?P<ram>[\d.]+) Mb$")


def slope(points: list[tuple[float, float]]) -> float | None:
    """Least-squares slope in Mb per hour. A measurement, not a verdict."""
    if len(points) < 3:
        return None
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        return None
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in points)
    return (numerator / denominator) * 3600


def stats(values: list[float]) -> tuple[float, float, float]:
    return min(values), max(values), sum(values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--samples", action="store_true", help="print every sample")
    parser.add_argument("--baseline", default=None, metavar="MIN:MAX",
                        help="optional RAM range to compare against; without it, only the "
                             "observed range is used")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    baseline = None
    if args.baseline:
        try:
            low, high = (float(v) for v in args.baseline.split(":", 1))
            baseline = (low, high)
        except ValueError:
            envelope.ok = False
            envelope.warn("--baseline must look like 648:885")
            cli.emit(envelope, "", args, {"error": "bad baseline"})
            return cli.EXIT_ARGS

    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    rows, all_samples, status_source = [], [], 0
    for item in target.files:
        boots = [e.number for e in item.events if e.is_boot] or [0]
        status_source += sum(1 for e in item.events if STATUS_RE.match(e.text))
        for index, start in enumerate(boots):
            end = boots[index + 1] if index + 1 < len(boots) else None
            samples = [(e, m) for e in item.events
                       if e.number >= start and (end is None or e.number < end)
                       and (m := TELEMETRY_RE.match(e.text))]
            if not samples:
                continue
            usable = [(e, m) for e, m in samples if not e.is_epoch]
            # The first sample after a boot is a structural outlier: on the Tizen files
            # of the corpus it is the file maximum (98-99 %) and the next one is 27-33 %.
            head, tail = (usable[0] if usable else None), usable[1:]
            body_samples = tail or usable
            cpu = [float(m.group("cpu")) for _, m in body_samples]
            ram = [float(m.group("ram")) for _, m in body_samples]
            times = [e.timestamp for e, _ in body_samples]
            origin = times[0] if times else None
            trend = slope([((t - origin).total_seconds(), r) for t, r in zip(times, ram)]) \
                if origin else None
            cadence = logfmt.cadence([e for e, _ in body_samples])
            missing = 0
            if cadence["median"]:
                for before, after in zip(times, times[1:]):
                    gap = (after - before).total_seconds()
                    if gap > cadence["median"] * 1.5:
                        missing += int(round(gap / cadence["median"])) - 1

            cpu_lo, cpu_hi, cpu_mean = stats(cpu)
            ram_lo, ram_hi, ram_mean = stats(ram)
            rows.append({
                "file": item.alias, "session": index + 1,
                "boot": tg.cite(item, start, target) if start else "—",
                "n": len(body_samples),
                "cpu": (cpu_lo, cpu_hi, cpu_mean),
                "ram": (ram_lo, ram_hi, ram_mean),
                "first_after_boot": (float(head[1].group("cpu")), float(head[1].group("ram")),
                                     tg.cite(item, head[0].number, target)) if head and tail
                                    else None,
                "trend": trend,
                "cadence": cadence["median"],
                "missing": missing,
                "below_baseline": sum(1 for r in ram if baseline and r < baseline[0]),
            })
            all_samples += ram

    if not rows:
        envelope.warn("no telemetry lines found in these logs")
    if status_source:
        envelope.warn(f"{status_source} reading(s) come from the status block "
                      f"(`CPU usage: …`), a second source with different wording; counted "
                      f"apart and not mixed into the series")
    envelope.total = envelope.returned = len(rows)

    body = ["# Resources", ""]
    if all_samples:
        body.append(f"- observed RAM across these logs: **{min(all_samples):.0f} – "
                    f"{max(all_samples):.0f} Mb**")
    if baseline:
        below = sum(r["below_baseline"] for r in rows)
        body.append(f"- against the given baseline {baseline[0]:.0f}–{baseline[1]:.0f} Mb: "
                    f"{below} sample(s) below the floor")
    else:
        body.append("- no baseline given, so nothing is called high or low: only the range "
                    "observed here is reported")
    body += ["",
             "| File | Sess | Samples | CPU min/max/mean | RAM min/max/mean | Trend Mb/h "
             "| Cadence | Missing | First after boot |", "|---|---|---|---|---|---|---|---|---|"]
    for row in cli.paginate(rows, args.offset, args.limit):
        trend = f"{row['trend']:+.2f}" if row["trend"] is not None else "—"
        peak = (f"{row['first_after_boot'][0]:.0f} % · `{row['first_after_boot'][2]}`"
                if row["first_after_boot"] else "—")
        cadence = f"{row['cadence']:.0f} s" if row["cadence"] else "—"
        body.append(
            f"| `{row['file']}` | {row['session']} | {row['n']} "
            f"| {row['cpu'][0]:.0f} / {row['cpu'][1]:.0f} / {row['cpu'][2]:.1f} "
            f"| {row['ram'][0]:.0f} / {row['ram'][1]:.0f} / {row['ram'][2]:.0f} "
            f"| {trend} | {cadence} | {row['missing']} | {peak} |")

    body += ["", "The first sample after each boot is reported separately and excluded from the "
                 "statistics: it is an initialization spike, not a steady-state reading.",
             "Trend is a least-squares slope over the session. It measures direction; it does "
             "not declare a leak."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args, {"sessions": len(rows)})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
