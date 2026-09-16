"""Citations: `path:line` references and the excerpts that accompany them.

Gate 2 depends on this module. A citation that points at a line that exists but
whose excerpt says something else is the dangerous case: the claim looks sourced
and is not. Both halves are checked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import reader

# A citation is a backticked `path:line` or `path:start-end`. Paths are POSIX and
# relative to the analysis folder, so the same string works on every platform.
CITATION_RE = re.compile(r"`(?P<path>[^\s`:]+(?:/[^\s`:]+)*):(?P<start>\d+)(?:-(?P<end>\d+))?`")

# What follows a citation on the same line, in double quotes, is the excerpt.
EXCERPT_RE = re.compile(r'"(?P<excerpt>[^"]*)"')

TRUNCATION_RE = re.compile(r"…\[\+\d+ chars\]$")


@dataclass
class Citation:
    source_line: int          # line of the .md where the citation appears
    path: str                 # as written, relative to the analysis folder
    start: int
    end: int | None
    excerpt: str | None

    @property
    def label(self) -> str:
        span = f"{self.start}-{self.end}" if self.end else str(self.start)
        return f"{self.path}:{span}"


@dataclass
class Result:
    citation: Citation
    ok: bool
    reason: str = ""


def extract(markdown: str) -> list[Citation]:
    """Every citation in a document, in order."""
    found: list[Citation] = []
    for index, text in enumerate(markdown.split("\n"), start=1):
        for match in CITATION_RE.finditer(text):
            tail = text[match.end():]
            excerpt_match = EXCERPT_RE.search(tail)
            found.append(Citation(
                source_line=index,
                path=match.group("path"),
                start=int(match.group("start")),
                end=int(match.group("end")) if match.group("end") else None,
                excerpt=excerpt_match.group("excerpt") if excerpt_match else None,
            ))
    return found


def _matches(excerpt: str, actual: str) -> bool:
    """An excerpt matches when it is the line, or a verbatim prefix of it.

    Artifacts quote at most ~200 characters and mark the cut, so a shortened
    excerpt is legitimate. Anything else must be byte-for-byte: the double and
    trailing spaces of this format are part of the evidence.
    """
    quoted = TRUNCATION_RE.sub("", excerpt).rstrip("…")
    return actual == excerpt or actual.startswith(quoted) or quoted in actual


def verify(citations: list[Citation], root: Path) -> list[Result]:
    """Check each citation against the files under `root`."""
    results: list[Result] = []
    cache: dict[str, list[reader.Line] | None] = {}

    for citation in citations:
        if citation.path not in cache:
            target = (root / citation.path)
            cache[citation.path] = reader.read_lines(target) if target.is_file() else None
        lines = cache[citation.path]

        if lines is None:
            results.append(Result(citation, False, "file not found"))
            continue
        if not (1 <= citation.start <= len(lines)):
            results.append(Result(citation, False,
                                  f"line {citation.start} is outside the file ({len(lines)} lines)"))
            continue
        if citation.end is not None and not (citation.start <= citation.end <= len(lines)):
            results.append(Result(citation, False,
                                  f"range end {citation.end} is outside the file ({len(lines)} lines)"))
            continue
        if citation.excerpt:
            actual = lines[citation.start - 1].text
            if not _matches(citation.excerpt, actual):
                results.append(Result(citation, False, "excerpt does not match the line"))
                continue
        results.append(Result(citation, True))
    return results


def aliases(paths: list[str]) -> dict[str, str]:
    """F1, F2 … for files, so a command never carries a path with spaces."""
    return {path: f"F{index}" for index, path in enumerate(sorted(set(paths)), start=1)}
