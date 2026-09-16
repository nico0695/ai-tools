#!/usr/bin/env python3
"""How many times the player started, whether it was planned, and how long it ran."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_sessions",
    "question": "how many times it booted, scheduled or unexpected, and the uptime of each run",
    "use_when": "the complaint mentions restarts, or before trusting any uptime figure",
    "not_for": "why it rebooted when the log does not say — it often does not",
    "args": "--analysis <id> | --path <dir> [--reason-window N]",
    "columns": "session, boot citation, reason, classification, span, duration",
    "size": "one row per boot",
    "group": "query",
}

REASON_RE = re.compile(r"^System will reboot\. Reason: (?P<reason>.+)$")
SUPPORT = {
    "reboot-command": re.compile(r"^Reboot command received"),
    "tasks-finished": re.compile(r"^All tasks were finished"),
}
# The countdown deliberately plays no part in classification: the lowest value seen in
# the corpus is 909 minutes, and the two real scheduled reboots cut at 1439 and 1437.
# Only the explicit reason line is evidence. See docs/log-format.md and scripts-idea/02.
COUNTDOWN_RE = re.compile(r"^Device will reboot in (\d+) minutes")


def classify(reason: str | None, boot_index: int) -> str:
    if reason is None:
        return "unknown" if boot_index <= 2 else "unexpected"
    upper = reason.upper()
    if "SCHEDULED" in upper:
        return "scheduled"
    if "COMMAND" in upper:
        return "commanded"
    return "other-reason"


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--reason-window", type=int, default=12,
                        help="lines to look back for the reason (default 12: two of the "
                             "four reasons in the corpus were 8 and 9 lines away)")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    rows, countdowns = [], []
    for item in target.files:
        boots = [e for e in item.events if e.is_boot]
        for index, boot in enumerate(boots):
            reason, reason_at, support = None, None, []
            low = max(0, boot.number - args.reason_window - 1)
            for event in item.events:
                if not low < event.number < boot.number:
                    continue
                if match := REASON_RE.match(event.text):
                    reason, reason_at = match.group("reason"), event.number
                for label, matcher in SUPPORT.items():
                    if matcher.match(event.text):
                        support.append(label)

            after = [e for e in item.events if e.number >= boot.number and not e.is_epoch]
            next_boot = boots[index + 1].number if index + 1 < len(boots) else None
            span = [e for e in after if next_boot is None or e.number < next_boot]
            first = span[0] if span else None
            last = span[-1] if span else None
            duration = ((last.timestamp - first.timestamp).total_seconds()
                        if first and last else None)
            epoch = [e for e in item.events
                     if e.is_epoch and e.number >= boot.number
                     and (next_boot is None or e.number < next_boot)]

            rows.append({
                "file": item.alias,
                "n": index + 1,
                "boot": tg.cite(item, boot.number, target),
                "reason": reason or "—",
                "reason_at": tg.cite(item, reason_at, target) if reason_at else "—",
                "class": classify(reason, boot.number),
                "first": logfmt.stamp(first.timestamp) if first else "—",
                "last": logfmt.stamp(last.timestamp) if last else "—",
                "duration_s": round(duration) if duration is not None else None,
                "support": ", ".join(sorted(set(support))) or "—",
                "epoch_lines": len(epoch),
            })
        countdowns += [int(m.group(1)) for e in item.events
                       if (m := COUNTDOWN_RE.match(e.text))]

    unknown = sum(1 for r in rows if r["class"] == "unknown")
    epoch_total = sum(r["epoch_lines"] for r in rows)
    envelope.total = envelope.returned = len(rows)
    if unknown:
        envelope.warn(f"{unknown} boot(s) are the first lines of their file: there is no previous "
                      f"session in the log, so they are `unknown`, not `unexpected`")
    if epoch_total:
        envelope.warn(f"{epoch_total} line(s) sit in a cold-boot epoch window and are excluded "
                      f"from every duration")
    if countdowns:
        envelope.warn(f"`Device will reboot in N minutes` is present ({len(countdowns)} lines, "
                      f"min {min(countdowns)}) but is NOT used to classify: in the corpus the "
                      f"scheduled reboots cut at 1439 and 1437 minutes")

    counts = {}
    for row in rows:
        counts[row["class"]] = counts.get(row["class"], 0) + 1

    body = ["# Sessions", "",
            f"- {len(rows)} boot(s) in {len(target.files)} file(s)",
            "- " + " · ".join(f"**{k}** {v}" for k, v in sorted(counts.items())), "",
            "| File | # | Boot | Reason | Class | First | Last | Uptime | Support |",
            "|---|---|---|---|---|---|---|---|---|"]
    for row in cli.paginate(rows, args.offset, args.limit):
        uptime = f"{row['duration_s'] // 3600}h {row['duration_s'] % 3600 // 60}m" \
            if row["duration_s"] is not None else "—"
        body.append(f"| `{row['file']}` | {row['n']} | `{row['boot']}` | {row['reason']} "
                    f"| `{row['class']}` | {row['first']} | {row['last']} | {uptime} "
                    f"| {row['support']} |")
    body += ["", "Only an explicit `System will reboot. Reason:` line classifies a boot. "
                 "`All tasks were finished` appears in 3 of 4 reasoned reboots, so it is shown "
                 "as support and never used as the criterion."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args, {"sessions": rows, "classes": counts})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
