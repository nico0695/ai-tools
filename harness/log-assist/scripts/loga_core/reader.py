"""Reading log files so that line numbers match what an editor shows.

Files are read as bytes and split on b"\\n". That keeps numbering exact regardless
of encoding damage, and it is why a citation of `file:1234` can be trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DISPLAY_LIMIT = 300      # a line longer than this is cut for display, never for matching
EXCERPT_LIMIT = 200      # what an artifact may quote


@dataclass(frozen=True)
class Line:
    number: int          # 1-based, matches the editor
    text: str            # without the trailing newline or carriage return


def read_lines(path: str | Path) -> list[Line]:
    """Read a file into numbered lines. Undecodable bytes are replaced, not dropped."""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    chunks = raw.split(b"\n")
    if chunks and chunks[-1] == b"":
        chunks.pop()                      # a trailing newline is not an empty last line
    return [Line(i + 1, c.decode("utf-8", errors="replace").rstrip("\r"))
            for i, c in enumerate(chunks)]


def read_line(path: str | Path, number: int) -> Line | None:
    """One line by number, without holding the file in memory twice."""
    lines = read_lines(path)
    return lines[number - 1] if 1 <= number <= len(lines) else None


def truncate(text: str, limit: int = DISPLAY_LIMIT) -> str:
    """Cut for display, always saying how much was cut."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"…[+{len(text) - limit} chars]"


def excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    """What an artifact quotes: verbatim, only shortened."""
    return truncate(text, limit)
