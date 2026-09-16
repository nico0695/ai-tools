"""Reduce a message to its shape, so that repeated messages collapse into one form.

Used to find what a log is mostly made of. Order matters: the widest structures are
replaced first, so a number inside a JSON blob does not survive as `<N>`.
"""

from __future__ import annotations

import re

_RULES = (
    (re.compile(r"\{.*?\}"), "<JSON>"),
    (re.compile(r"\[[^\]]*\.json[^\]]*\]"), "<FILES>"),
    (re.compile(r"\b(?:https?|file|ws)://\S+"), "<URL>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"), "<MAC>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}[:.]\d{2}[:.]\d{2}\S*"), "<TS>"),
    (re.compile(r"\b[0-9a-f]{16,}\b"), "<HASH>"),
    (re.compile(r"(?<![\w<])[\w.\-]*/[\w./\-]+"), "<PATH>"),
    (re.compile(r'"[^"]*"'), '"<S>"'),
    (re.compile(r"'[^']*'"), "'<S>'"),
    (re.compile(r"\b\d[\d.,]*\b"), "<N>"),
)


def form(message: str) -> str:
    """The message with every variable part replaced by a placeholder."""
    shape = message
    for pattern, replacement in _RULES:
        shape = pattern.sub(replacement, shape)
    return shape.strip()


def signature(component: str, level: str, message: str) -> str:
    """A form qualified by where it came from, for counting."""
    prefix = f"[{component}] " if component else ""
    return f"{level} {prefix}{form(message)}"
