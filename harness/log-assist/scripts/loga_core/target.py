"""Turning --analysis / --path into a loaded set of logs, the same way everywhere."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import analysis as an
from . import cli, logset


@dataclass
class Target:
    files: list
    citation_root: Path      # citations are written relative to this
    analysis_dir: Path | None


def resolve(args, envelope) -> Target | None:
    """Load the logs in scope, or explain in the envelope why there are none."""
    root = Path(args.root).resolve() if args.root else an.repo_root()
    analysis_dir = an.analyses_root(root) / args.analysis if args.analysis else None

    if not args.analysis and not args.path:
        envelope.ok = False
        envelope.warn("name the logs with --analysis <id> or --path <dir|file>")
        return None

    paths = logset.resolve_paths(args.analysis, args.path, root)
    if not paths:
        where = analysis_dir / "logs" if analysis_dir else Path(args.path or "")
        envelope.ok = False
        envelope.warn(f"no .log files under {where.as_posix()}")
        return None

    files = logset.load_all(paths)
    if args.file:
        wanted = args.file.upper()
        files = [f for f in files if f.alias == wanted]
        if not files:
            envelope.ok = False
            envelope.warn(f"no file with alias {args.file}; run loga_scan to see the aliases")
            return None

    if analysis_dir:
        citation_root = analysis_dir
    else:
        base = Path(args.path)
        citation_root = base if base.is_dir() else base.parent

    low = [f for f in files if f.parse_rate < 1.0]
    for item in low:
        envelope.warn(f"{item.alias} parse_rate {item.parse_rate:.4f} "
                      f"({len(item.unparsed)} line(s) did not match the format)")
    return Target(files, citation_root, analysis_dir)


def partial_exit(target: Target) -> int:
    """Exit 4 when any file parsed incompletely: the numbers are suspect."""
    return cli.EXIT_PARTIAL if any(f.parse_rate < 1.0 for f in target.files) else cli.EXIT_OK


def cite(item, number: int, target: Target) -> str:
    return f"{logset.relative(item.path, target.citation_root)}:{number}"


def legend(target: Target) -> list[str]:
    """The alias table, printed when more than one file is in scope."""
    if len(target.files) < 2:
        return []
    return ["", "| Alias | File |", "|---|---|",
            *[f"| `{f.alias}` | `{logset.relative(f.path, target.citation_root)}` |"
              for f in target.files]]
