"""Each script declares a SPEC; loga_index lists them.

SPEC is read statically with `ast`, never by importing the script: listing the
catalogue must not execute anything.

    SPEC = {
        "name": "loga_scan",
        "question": "what files are here, which screen, what range, do they parse",
        "use_when": "starting an inventory, or after new logs arrive",
        "not_for": "looking for a specific message — that is loga_grep",
        "args": "--analysis <id> [--limit N]",
        "columns": "alias, file, screen, platform, player, range, lines, parse_rate, boots",
        "size": "one row per file, tens of lines",
        "group": "query",   # state | query
    }
"""

from __future__ import annotations

import ast
from pathlib import Path

FIELDS = ("name", "question", "use_when", "not_for", "args", "columns", "size", "group")


def read_spec(path: Path) -> dict | None:
    """Pull the module-level SPEC out of a script without importing it."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "SPEC" for t in node.targets
        ):
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                return None
            return value if isinstance(value, dict) else None
    return None


def collect(scripts_dir: Path) -> list[dict]:
    """Every loga_*.py that declares a SPEC, sorted by group then name."""
    specs = []
    for path in sorted(scripts_dir.glob("loga_*.py")):
        spec = read_spec(path)
        if spec:
            spec = dict(spec)
            spec.setdefault("name", path.stem)
            spec["file"] = path.name
            specs.append(spec)
    return sorted(specs, key=lambda s: (s.get("group", "zz"), s["name"]))
