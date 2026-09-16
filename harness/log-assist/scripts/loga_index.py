#!/usr/bin/env python3
"""List the scripts, from the SPEC each one declares, plus the catalog contents."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import cli  # noqa: E402
from loga_core import spec as sp  # noqa: E402

SPEC = {
    "name": "loga_index",
    "question": "which scripts exist, what does each answer, and what is in the catalog",
    "use_when": "a worker needs to choose a script",
    "not_for": "running anything",
    "args": "[--catalog] [--detail NAME]",
    "columns": "name, group, question, use when",
    "size": "one row per script",
    "group": "state",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("--catalog", action="store_true", help="list catalog.toml instead")
    parser.add_argument("--detail", default=None, help="show every SPEC field for one script")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    scripts_dir = Path(__file__).resolve().parent

    if args.catalog:
        catalog_path = scripts_dir / "catalog.toml"
        if not catalog_path.is_file():
            envelope.warn("scripts/catalog.toml does not exist yet (it arrives with S3)")
            cli.emit(envelope, "# Catalog\n\nNot present yet.", args, {"patterns": [], "signatures": []})
            return cli.EXIT_OK
        with catalog_path.open("rb") as handle:
            catalog = tomllib.load(handle)
        patterns = catalog.get("patterns", [])
        signatures = catalog.get("signatures", [])
        envelope.total = envelope.returned = len(patterns) + len(signatures)
        body = "\n".join([
            "# Catalog", "", f"- {len(patterns)} pattern(s), {len(signatures)} signature(s)", "",
            "| id | kind | component | platforms | noise |", "|---|---|---|---|---|",
            *[f"| `{p.get('id')}` | pattern | {p.get('component', '—')} "
              f"| {', '.join(p.get('platforms', [])) or 'any'} | {p.get('noise', False)} |"
              for p in patterns],
            *[f"| `{s.get('id')}` | signature | — | {', '.join(s.get('platforms', [])) or 'any'} | — |"
              for s in signatures],
        ])
        cli.emit(envelope, body, args, catalog)
        return cli.EXIT_OK

    specs = sp.collect(scripts_dir)
    if args.detail:
        match = next((s for s in specs if s["name"] == args.detail), None)
        if not match:
            envelope.ok = False
            envelope.warn(f"no script named {args.detail!r}")
            cli.emit(envelope, "", args, {"error": "unknown script"})
            return cli.EXIT_ARGS
        envelope.total = envelope.returned = 1
        body = "\n".join([f"# `{match['name']}`", ""] +
                         [f"- **{f}**: {match[f]}" for f in sp.FIELDS if f in match])
        cli.emit(envelope, body, args, match)
        return cli.EXIT_OK

    envelope.total = len(specs)
    page = cli.paginate(specs, args.offset, args.limit)
    envelope.returned = len(page)
    missing = [p.name for p in sorted(scripts_dir.glob("loga_*.py"))
               if not sp.read_spec(p)]
    for name in missing:
        envelope.warn(f"{name} declares no SPEC, so it is not listed")
    envelope.suggest("loga_index.py --detail <name>")

    body = "\n".join([
        "# Scripts", "",
        "| name | group | answers | use when |", "|---|---|---|---|",
        *[f"| `{s['name']}` | {s.get('group', '—')} | {s.get('question', '')} "
          f"| {s.get('use_when', '')} |" for s in page],
        "", f"Root: `{an.repo_root().name}/scripts/`. Run one with the configured Python command.",
    ])
    cli.emit(envelope, body, args, {"scripts": page})
    return cli.EXIT_OK


if __name__ == "__main__":
    cli.run(main)
