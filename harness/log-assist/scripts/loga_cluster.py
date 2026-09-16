#!/usr/bin/env python3
"""Sync group health: who is master, who is there, and whether the group is well formed."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, logset, reader, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_cluster",
    "question": "who is the master, who is in the group, and is it well formed",
    "use_when": "screens of one group are out of step, or a master is in doubt",
    "not_for": "a single screen with no group — it will say so",
    "args": "--analysis <id> | --path <dir> [--snapshots]",
    "columns": "file, citation, group, members, masters, verdict",
    "size": "one row per snapshot",
    "group": "query",
}

MEMBERS_RE = re.compile(r"^Version: (?P<sync>\S+) - Group: (?P<group>.*?) - Members:(?P<members>.*)$")
ROW_RE = re.compile(r"^(?P<ip>(?:\d{1,3}\.){3}\d{1,3}) \| (?P<state>\w+) \|")
MASTER_ROW = "(MASTER)"


def verdict(group: str, members: list[str], masters: list[str]) -> str:
    if group == "undefined" and not members:
        return "no-group"
    if len(masters) > 1:
        return "split-brain"
    if members and not masters:
        return "no-master"
    if len(masters) == 1:
        return "healthy"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--snapshots", action="store_true", help="show the member rows too")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    rows, silent = [], []
    for item in target.files:
        found = False
        for event in item.events:
            match = logfmt.search(MEMBERS_RE, event)
            if not match:
                continue
            found = True
            members, masters = logset.members_and_masters(match.group("members"))
            group = (match.group("group") or "").strip()
            # The member table lives in the lines after this one, when it exists at all.
            table = []
            for follower in item.events:
                if not event.number < follower.number <= event.number + len(members) + 3:
                    continue
                row = ROW_RE.match(follower.text) or ROW_RE.match(follower.raw_message)
                if row:
                    table.append({
                        "ip": row.group("ip"), "state": row.group("state"),
                        "master": MASTER_ROW in follower.raw_message,
                        "citation": tg.cite(item, follower.number, target),
                    })
            rows.append({
                "file": item.alias,
                "citation": tg.cite(item, event.number, target),
                "group": group or "—",
                "members": members,
                "masters": masters,
                "verdict": verdict(group, members, masters),
                "own_ip": item.identity.own_ip,
                "own_is_master": item.identity.own_ip in masters if item.identity.own_ip else None,
                "table": table,
            })
        if not found:
            silent.append(item.alias)

    envelope.total = envelope.returned = len(rows)
    if silent:
        envelope.warn(f"{', '.join(silent)} emit no `Members:` line at all: their group state is "
                      f"unknown, which is not the same as being alone")
    bad = [r for r in rows if r["verdict"] in ("split-brain", "no-master")]
    if bad:
        envelope.warn(f"{len(bad)} snapshot(s) are malformed: "
                      + ", ".join(f"{r['citation']} {r['verdict']}" for r in bad[:5]))
    missing_table = sum(1 for r in rows if not r["table"])
    if missing_table:
        envelope.warn(f"{missing_table} snapshot(s) have no member table; the master count comes "
                      f"from the `Members:` line, which is why that line is the one counted")
    unknown_ip = [r["file"] for r in rows if not r["own_ip"]]
    if unknown_ip:
        envelope.warn(f"own IP unresolved for {', '.join(sorted(set(unknown_ip)))}: cannot say "
                      f"whether this screen is the master")

    body = ["# Cluster", "",
            f"- {len(rows)} snapshot(s) across {len(target.files)} file(s)", "",
            "| File | Citation | Group | Members | Masters | This screen | Verdict |",
            "|---|---|---|---|---|---|---|"]
    for row in cli.paginate(rows, args.offset, args.limit):
        self_role = "—"
        if row["own_is_master"] is True:
            self_role = "**master**"
        elif row["own_is_master"] is False:
            self_role = "member"
        body.append(f"| `{row['file']}` | `{row['citation']}` | {cli.md_cell(row['group'])} "
                    f"| {len(row['members'])} | {len(row['masters'])} | {self_role} "
                    f"| `{row['verdict']}` |")

    if args.snapshots:
        for row in cli.paginate(rows, args.offset, args.limit):
            body += ["", f"### `{row['citation']}` — {row['verdict']}"]
            if row["table"]:
                body += ["", "| IP | State | Master | Citation |", "|---|---|---|---|"]
                body += [f"| `{t['ip']}` | {t['state']} | {'yes' if t['master'] else ''} "
                         f"| `{t['citation']}` |" for t in row["table"]]
            else:
                body.append("")
                body.append("No member table in this snapshot.")

    body += ["", "Masters are counted on the `Members:` line, not on the `(MASTER)` rows: that "
                 "line exists in every file that has a group, while the table is often absent.",
             "`no-group` (the node is not in a group) and `no-master` (a populated group with "
             "nobody coordinating) are different findings."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args,
             {"snapshots": [{k: v for k, v in r.items() if k != "table"} for r in rows]})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
