#!/usr/bin/env python3
"""Static check of the clone: runtime, layout, config, wrappers, adapters, skill copies.

No tokens are spent and no agent is launched. A check that fails says what to do.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import analysis as an  # noqa: E402
from loga_core import cli  # noqa: E402

SPEC = {
    "name": "loga_doctor",
    "question": "is this clone correctly set up, and has anything drifted",
    "use_when": "during loga-init, and whenever a worker or skill fails to load",
    "not_for": "checking that an AI actually answers — that would cost tokens",
    "args": "[--root PATH]",
    "columns": "check, verdict, detail",
    "size": "one row per check",
    "group": "state",
}

OK, PARTIAL, MISSING = "ok", "partial", "missing"

CONFIG_FIELDS = ("version", "language", "python_cmd", "validated_at")
TEMPLATES = (
    "templates/state.toml", "templates/SUMMARY.md",
    *(f"templates/record/{n}.md" for n in ("intake", "inventory", "findings", "hypotheses",
                                           "comparison", "exploration", "challenge")),
    *(f"templates/reports/{n}.md" for n in ("findings", "status")),
)
CONTRACTS = tuple(f"skills/_shared/loga-{n}-contract.md"
                  for n in ("flow", "persistence", "user-interaction"))
# Artifacts that stage S4 creates. Reported as pending, not as breakage.
STAGE_4 = {
    "orchestrator/LOGA-RUNTIME.md": "orchestrator runtime",
    ".claude/agents/loga-worker.md": "Claude worker adapter",
    ".codex/agents/loga-worker.toml": "Codex worker adapter",
}


@dataclass
class Check:
    name: str
    verdict: str
    detail: str


def check_runtime() -> Check:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        return Check("python", MISSING,
                     f"{major}.{minor} found; 3.11+ is required for tomllib")
    return Check("python", OK, f"{major}.{minor} at {Path(sys.executable).name}")


def check_config(root: Path) -> Check:
    path = root / "loga.config.toml"
    if not path.is_file():
        return Check("config", MISSING, "loga.config.toml not found; run loga-init")
    try:
        with path.open("rb") as handle:
            config = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        return Check("config", MISSING, f"loga.config.toml is not valid TOML: {exc}")
    absent = [f for f in CONFIG_FIELDS if not config.get(f)]
    if absent:
        return Check("config", PARTIAL, f"missing field(s): {', '.join(absent)}")
    setups = config.get("ai_setups", {})
    enabled = [name for name, block in setups.items() if block.get("enabled")]
    if not enabled:
        return Check("config", PARTIAL, "no AI setup is enabled")
    return Check("config", OK, f"language={config['language']}, python_cmd={config['python_cmd']}, "
                               f"ai={', '.join(sorted(enabled))}")


def check_files(root: Path, name: str, relatives) -> Check:
    absent = [r for r in relatives if not (root / r).is_file()]
    if not absent:
        return Check(name, OK, f"all {len(tuple(relatives))} present")
    if len(absent) == len(tuple(relatives)):
        return Check(name, MISSING, "none present")
    return Check(name, PARTIAL, f"missing: {', '.join(absent)}")


def check_wrappers(root: Path) -> Check:
    agents, claude = root / "AGENTS.md", root / "CLAUDE.md"
    if not agents.is_file() or not claude.is_file():
        absent = [p.name for p in (agents, claude) if not p.is_file()]
        return Check("wrappers", MISSING, f"missing: {', '.join(absent)}")
    text = claude.read_text(encoding="utf-8")
    if "@AGENTS.md" not in text:
        return Check("wrappers", PARTIAL,
                     "CLAUDE.md does not import AGENTS.md, so the shared block may have drifted")
    if "loga_role: worker" not in agents.read_text(encoding="utf-8"):
        return Check("wrappers", PARTIAL, "AGENTS.md has no worker-bypass block")
    return Check("wrappers", OK, "AGENTS.md holds the shared block; CLAUDE.md imports it")


def check_settings(root: Path) -> Check:
    path = root / ".claude" / "settings.json"
    if not path.is_file():
        return Check("permissions", MISSING, ".claude/settings.json not found")
    try:
        allow = json.loads(path.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    except json.JSONDecodeError as exc:
        return Check("permissions", MISSING, f"settings.json is not valid JSON: {exc}")
    if not any("loga_" in entry for entry in allow):
        return Check("permissions", PARTIAL, "the allowlist does not cover scripts/loga_*")
    return Check("permissions", OK, f"{len(allow)} allow rule(s)")


def check_skill_copies(root: Path) -> Check:
    source = root / "skills"
    if not source.is_dir() or not any(source.glob("loga-*/SKILL.md")):
        return Check("skill copies", MISSING, "skills/ holds no SKILL.md yet (stage S4)")
    names = {p.parent.name for p in source.glob("loga-*/SKILL.md")}
    drifted, absent = [], []
    for destination in (root / ".claude" / "skills", root / ".agents" / "skills"):
        if not destination.is_dir():
            absent.append(destination.relative_to(root).as_posix())
            continue
        for name in names:
            copy = destination / name / "SKILL.md"
            if not copy.is_file():
                absent.append(f"{destination.name}/{name}")
            elif not filecmp.cmp(source / name / "SKILL.md", copy, shallow=False):
                drifted.append(f"{destination.name}/{name}")
    if drifted:
        return Check("skill copies", PARTIAL, f"drifted, rerun loga-init: {', '.join(drifted)}")
    if absent:
        return Check("skill copies", PARTIAL, f"not copied: {', '.join(sorted(set(absent)))}")
    return Check("skill copies", OK, f"{len(names)} skill(s) in sync")


def check_inbox(root: Path) -> Check:
    """The drop zone, and whether it is safe to drop customer logs into it.

    An inbox that git would track is worse than no inbox: the whole point of the folder is
    that people paste production logs into it without thinking about it first.
    """
    inbox = root / an.INBOX
    if not inbox.is_dir():
        return Check("inbox", MISSING, f"{an.INBOX}/ not found; run loga-init")
    ignored = f"{an.INBOX}/" in (root / ".gitignore").read_text(encoding="utf-8") \
        if (root / ".gitignore").is_file() else False
    if not ignored:
        return Check("inbox", PARTIAL, f"{an.INBOX}/ is not in .gitignore — logs could be committed")
    waiting = sum(1 for p in inbox.rglob("*") if p.is_file() and not p.name.startswith("."))
    return Check("inbox", OK, f"{an.INBOX}/ ignored by git" +
                 (f", {waiting} file(s) waiting to import" if waiting else ", empty"))


def check_stage4(root: Path) -> list[Check]:
    return [Check(label, OK if (root / rel).is_file() else MISSING,
                  rel if (root / rel).is_file() else f"{rel} — expected at stage S4")
            for rel, label in STAGE_4.items()]


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    parser.add_argument("--root", default=None)
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    root = Path(args.root).resolve() if args.root else an.repo_root()

    checks = [
        check_runtime(),
        check_config(root),
        check_files(root, "templates", TEMPLATES),
        check_files(root, "contracts", CONTRACTS),
        check_wrappers(root),
        check_settings(root),
        check_skill_copies(root),
        *check_stage4(root),
        Check("analyses dir", OK if an.analyses_root(root).is_dir() else MISSING,
              an.analyses_root(root).relative_to(root).as_posix()),
        check_inbox(root),
    ]

    failed = [c for c in checks if c.verdict != OK]
    envelope.total = len(checks)
    envelope.returned = len(failed)
    envelope.ok = not failed
    for check in failed:
        envelope.warn(f"{check.name}: {check.verdict} — {check.detail}")
    if any(c.verdict == MISSING and c.name == "config" for c in checks):
        envelope.suggest("run loga-init")

    body = "\n".join([
        "# Doctor", "",
        f"- {sum(1 for c in checks if c.verdict == OK)} ok · "
        f"{sum(1 for c in checks if c.verdict == PARTIAL)} partial · "
        f"{sum(1 for c in checks if c.verdict == MISSING)} missing", "",
        "| Check | Verdict | Detail |", "|---|---|---|",
        *[f"| {c.name} | `{c.verdict}` | {c.detail} |" for c in checks],
    ])
    cli.emit(envelope, body, args, {"checks": [c.__dict__ for c in checks]})
    return cli.EXIT_OK if not failed else cli.EXIT_PARTIAL


if __name__ == "__main__":
    cli.run(main)
