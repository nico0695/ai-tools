#!/usr/bin/env python3
"""Gate 2: every `file:line` citation in a document resolves and its excerpt matches."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import citations as ct  # noqa: E402
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "loga_verify_citations",
    "question": "do the citations in this document resolve, and do their excerpts match",
    "use_when": "before any report is shown or the analysis is marked concluded",
    "not_for": "checking whether a claim is true — only that its evidence exists",
    "args": "<path-to-md> [--root PATH]",
    "columns": "citation, verdict, reason",
    "size": "one row per failing citation",
    "group": "state",
}


def resolve_root(document: Path, root: Path | None) -> Path:
    """Citations are relative to the analysis folder that holds the document."""
    if root:
        return root
    for parent in document.resolve().parents:
        if (parent / "state.toml").is_file() and parent.parent.name == an.ANALYSES_DIR:
            return parent
    return document.resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("document")
    parser.add_argument("--root", default=None, help="analysis folder, if not inferable")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    document = Path(args.document)
    if not document.is_file():
        envelope.ok = False
        envelope.warn(f"{args.document} not found")
        cli.emit(envelope, "", args, {"error": "not found"})
        return cli.EXIT_INPUT

    root = resolve_root(document, Path(args.root).resolve() if args.root else None)
    found = ct.extract(document.read_text(encoding="utf-8"))
    results = ct.verify(found, root)
    failures = [r for r in results if not r.ok]
    with_excerpt = sum(1 for c in found if c.excerpt)

    envelope.total = len(results)
    envelope.returned = len(failures)
    envelope.ok = not failures
    if not found:
        envelope.warn("the document carries no citations at all")
    if found and not with_excerpt:
        envelope.warn("no citation quotes an excerpt, so only line existence was checked")

    lines = [f"# Citations — `{document.name}`", "",
             f"- checked against `{root.as_posix()}`",
             f"- {len(results)} citation(s), {with_excerpt} with an excerpt",
             f"- **{len(failures)} failing**", ""]
    if failures:
        lines += ["| Document line | Citation | Reason |", "|---|---|---|"]
        lines += [f"| {r.citation.source_line} | `{r.citation.label}` | {r.reason} |"
                  for r in failures]
    else:
        lines.append("Every citation resolves." if found else "Nothing to verify.")
    cli.emit(envelope, "\n".join(lines), args, {
        "root": root.as_posix(), "total": len(results),
        "failures": [{"line": r.citation.source_line, "citation": r.citation.label,
                      "reason": r.reason} for r in failures],
    })
    return cli.EXIT_OK if not failures else cli.EXIT_VERIFY


if __name__ == "__main__":
    cli.run(main)
