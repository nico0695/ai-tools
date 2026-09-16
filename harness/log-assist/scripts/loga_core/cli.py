"""The output contract every loga script honors.

stdout is always: one JSON envelope line, then compact markdown (or JSON when
--format json). Nothing else is ever printed to stdout; diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict

# Exit codes. Zero results is success, not an error.
EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_ARGS = 2
EXIT_INPUT = 3
EXIT_PARTIAL = 4
EXIT_VERIFY = 5

MAX_CHARS_DEFAULT = 8000
MAX_CHARS_CEILING = 40000


def force_utf8() -> None:
    """Windows consoles default to cp1252 and would mangle log excerpts."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, ValueError):  # pragma: no cover - exotic hosts
            pass


@dataclass
class Envelope:
    script: str
    ok: bool = True
    returned: int = 0
    total: int = 0
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    next: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def suggest(self, command: str) -> None:
        if command not in self.next:
            self.next.append(command)


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS_DEFAULT,
                        help=f"output budget, capped at {MAX_CHARS_CEILING}")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--save", metavar="PATH", default=None,
                        help="also write the untruncated output to PATH")
    return parser


def md_cell(text: str) -> str:
    """Make log-derived text safe inside a markdown table.

    Sync group names really do contain pipes (`TAR PLVE | Mall Plaza | 7PV`), so any
    cell holding text that came from a log has to escape them.
    """
    return str(text).replace("|", "\\|").replace("\n", " ")


def add_target_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """How every query script names the logs it should read."""
    parser.add_argument("--analysis", default=None, help="analysis id under analyses/")
    parser.add_argument("--path", default=None, help="a log file or a directory of logs")
    parser.add_argument("--file", default=None, metavar="ALIAS",
                        help="restrict to one file by alias (F1, F2 …)")
    parser.add_argument("--root", default=None)
    return parser


def paginate(rows: list, offset: int, limit: int | None) -> list:
    """Paging is re-running with a different offset: output is deterministic."""
    rows = rows[max(0, offset):]
    return rows[:limit] if limit is not None else rows


def emit(envelope: Envelope, body: str, args, payload=None) -> None:
    """Print the envelope line and the body, truncated to the output budget."""
    budget = max(500, min(args.max_chars, MAX_CHARS_CEILING))
    if args.max_chars > MAX_CHARS_CEILING:
        envelope.warn(f"--max-chars lowered to the {MAX_CHARS_CEILING} ceiling")

    full = json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else body
    if args.save:
        with open(args.save, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(full + "\n")
        envelope.warn(f"full output saved to {args.save}")

    out = full
    if len(out) > budget:
        out = out[:budget].rstrip() + f"\n\n…[+{len(full) - budget} chars] rerun with --max-chars or --offset"
        envelope.truncated = True

    sys.stdout.write(json.dumps(asdict(envelope), ensure_ascii=False) + "\n")
    sys.stdout.write(out.rstrip("\n") + "\n")


def run(main_fn) -> None:
    """Wrap a script entry point so that no traceback ever reaches stdout."""
    force_utf8()
    try:
        sys.exit(main_fn())
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(EXIT_INTERNAL)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - the contract says exit 1, not a crash
        sys.stdout.write(json.dumps({
            "script": getattr(main_fn, "__module__", "loga"),
            "ok": False,
            "returned": 0, "total": 0, "truncated": False,
            "warnings": [f"internal error: {type(exc).__name__}: {exc}"],
            "next": [],
        }, ensure_ascii=False) + "\n")
        sys.exit(EXIT_INTERNAL)
