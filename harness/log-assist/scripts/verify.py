#!/usr/bin/env python3
"""Smoke test: every script honors its output contract against a real corpus.

This is NOT an eval. It never judges whether an answer is correct and carries no
expected outputs. It checks four mechanical things per run:

  1. the exit code is 0 (ok) or 4 (partial)
  2. the first stdout line parses as JSON and carries the seven envelope keys
  3. the envelope names the script that produced it
  4. nothing was written to stderr

Adding a script means adding one line to QUERY or STATE below.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "verify",
    "question": "do all the scripts still honor the output contract on a real corpus",
    "use_when": "after changing loga_core, and as the Windows check",
    "not_for": "judging whether an analysis is right — that is the acceptance run",
    "args": "--corpus <dir> [--corpus <dir> ...]",
    "columns": "script, exit code, rows returned, time, problem",
    "size": "one row per script per corpus",
    "group": "state",
}

ENVELOPE_KEYS = {"script", "ok", "returned", "total", "truncated", "warnings", "next"}
ALLOWED_EXITS = {cli.EXIT_OK, cli.EXIT_PARTIAL}

# Scripts that read logs, with arguments that produce output on any corpus.
QUERY = {
    "loga_scan": [], "loga_summary": ["--top", "5"], "loga_grep": ["--regex", "Heartbeat"],
    "loga_window": ["--at", "F1:50", "--before", "2", "--after", "2"],
    "loga_sessions": [], "loga_resources": [], "loga_gaps": [], "loga_check": [],
    "loga_cluster": [], "loga_compare": [],
}
# Scripts that read state, not logs: run once, without a corpus.
STATE = {"loga_doctor": [], "loga_index": [], "loga_search": []}


def run_one(name: str, extra: list[str], corpus: str | None, root: Path) -> dict:
    command = [sys.executable, str(root / "scripts" / f"{name}.py"), *extra,
               "--max-chars", "3000"]
    if corpus:
        command += ["--path", corpus]
    started = time.time()
    done = subprocess.run(command, cwd=root, capture_output=True, text=True)
    elapsed = time.time() - started

    problems, returned = [], "?"
    first = done.stdout.split("\n", 1)[0] if done.stdout else ""
    try:
        envelope = json.loads(first)
        if not ENVELOPE_KEYS <= set(envelope):
            problems.append(f"envelope is missing {sorted(ENVELOPE_KEYS - set(envelope))}")
        elif envelope["script"] != name:
            problems.append(f"envelope says script={envelope['script']!r}")
        else:
            returned = envelope["returned"]
    except json.JSONDecodeError:
        problems.append("first stdout line is not JSON")
    if done.returncode not in ALLOWED_EXITS:
        problems.append(f"exit {done.returncode}")
    if done.stderr.strip():
        problems.append("wrote to stderr")
    return {"script": name, "exit": done.returncode, "returned": returned,
            "seconds": elapsed, "problems": problems}


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("--corpus", action="append", default=[], metavar="DIR",
                        help="a directory of .log files; repeatable")
    args = parser.parse_args()
    cli.force_utf8()

    root = Path(__file__).resolve().parents[1]
    corpora = args.corpus or [str(root / "scripts" / "fixtures" / "sample.log")]
    rows = [run_one(n, e, None, root) for n, e in STATE.items()]
    for corpus in corpora:
        rows += [{**run_one(n, e, corpus, root), "corpus": Path(corpus).name}
                 for n, e in QUERY.items()]

    failed = [r for r in rows if r["problems"]]
    width = max(len(r["script"]) for r in rows)
    current = None
    for row in rows:
        label = row.get("corpus", "(no corpus)")
        if label != current:
            print(f"\n{label}")
            current = label
        status = "; ".join(row["problems"]) if row["problems"] else "ok"
        print(f"  {row['script']:<{width}}  exit={row['exit']}  "
              f"returned={str(row['returned']):>6}  {row['seconds']:5.1f}s  {status}")

    print()
    if failed:
        print(f"{len(failed)} script(s) broke the contract:")
        for row in failed:
            print(f"  {row['script']}: {'; '.join(row['problems'])}")
        return 1
    print(f"{len(rows)} run(s), every script honored the contract.")
    return 0


if __name__ == "__main__":
    cli.run(main)
