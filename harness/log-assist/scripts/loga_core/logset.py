"""Resolving a set of log files, their aliases, and the identity of each screen.

Identity always comes from the content. Two files are the same screen when their
identity says so, never because their names or line counts look alike.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import analysis as an
from . import parser, reader

MANIFEST = "record/runs/manifest.json"

_MACHINE = re.compile(r"^Machine: (?P<value>.+)$")
_PLATFORM = re.compile(r'^Initializing Dex Player\. Platform "(?P<value>[^"]+)"')
_HOSTNAME = re.compile(r"^Hostname: (?P<ip>\S+) (?P<mac>\S+)$")
_HB = re.compile(r"^Machine HB Interval: (?P<value>\d+) seconds")
_GROUP = re.compile(r"Version: (?P<sync>\S+) - Group: (?P<group>.*?) - Members:(?P<members>.*)$")
_MACHINE_ID = re.compile(r"^Machine ID: (?P<value>\S+)")
_CLIENT_IP = re.compile(r"^Client IP: (?P<value>\S+)")
_DISCOVERED = re.compile(r"^New member discovered: (?P<ip>\S+)")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# A Machine: value that is really "<IP> <MAC>" is not a screen name.
_IP_MAC = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3} (?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


@dataclass
class Identity:
    machine: str = ""
    machine_ambiguous: bool = False     # Machine: held an <IP> <MAC>, not a name
    machine_id: str = ""
    platform: str = ""
    player_version: list[str] = field(default_factory=list)
    sync_group: str = ""
    sync_version: str = ""
    members: list[str] = field(default_factory=list)
    masters: list[str] = field(default_factory=list)
    own_ip: str = ""
    own_ip_source: str = "unknown"      # hostname | client-ip | inferred | unknown
    hb_interval: int | None = None

    @property
    def screen_key(self) -> str:
        """What makes two files the same screen. Falls back down a ladder of evidence."""
        for candidate in (self.machine_id, "" if self.machine_ambiguous else self.machine,
                          self.own_ip):
            if candidate:
                return candidate
        return ""


@dataclass
class LogFile:
    path: Path
    alias: str
    lines: list = field(default_factory=list, repr=False)
    events: list = field(default_factory=list, repr=False)
    unparsed: list = field(default_factory=list, repr=False)
    identity: Identity = field(default_factory=Identity)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def parse_rate(self) -> float:
        return parser.parse_rate(self.events, self.unparsed)

    @property
    def boots(self) -> int:
        return parser.count_boots(self.events)

    @property
    def first(self):
        return self.events[0] if self.events else None

    @property
    def last(self):
        return self.events[-1] if self.events else None


def members_and_masters(members_text: str) -> tuple[list[str], list[str]]:
    """Parse the tail of a `Members:` line.

    Count the `[Master]` marks here, not the `(MASTER)` rows of the block: this line
    exists in every file that has a group, while the block table is often absent.
    """
    members, masters, current = [], [], None
    for token in members_text.split():
        if token == "[Master]":
            if current:
                masters.append(current)
        elif _IP.fullmatch(token):
            members.append(token)
            current = token
    return members, masters


def extract_identity(events: list) -> Identity:
    identity = Identity()
    discovered: set[str] = set()
    versions: list[str] = []

    for event in events:
        message = event.raw_message
        if parser.BOOT_RE.match(message):
            version = message.split(" ", 2)[2]
            if version not in versions:
                versions.append(version)
            continue
        text = event.text
        if (match := _MACHINE.match(text)) and not identity.machine:
            value = match.group("value")
            identity.machine = value
            identity.machine_ambiguous = bool(_IP_MAC.match(value))
        elif (match := _PLATFORM.match(text)) and not identity.platform:
            identity.platform = match.group("value")
        elif (match := _HOSTNAME.match(text)) and not identity.own_ip:
            identity.own_ip, identity.own_ip_source = match.group("ip"), "hostname"
        elif (match := _HB.match(text)) and identity.hb_interval is None:
            identity.hb_interval = int(match.group("value"))
        elif (match := _MACHINE_ID.match(message)) and not identity.machine_id:
            identity.machine_id = match.group("value")
        elif (match := _CLIENT_IP.match(message)) and not identity.own_ip:
            identity.own_ip, identity.own_ip_source = match.group("value"), "client-ip"
        elif match := _DISCOVERED.match(text):
            discovered.add(match.group("ip"))
        elif match := _GROUP.search(text):
            members, masters = members_and_masters(match.group("members"))
            if members or not identity.members:
                identity.sync_group = match.group("group")
                identity.sync_version = match.group("sync")
                identity.members, identity.masters = members, masters

    identity.player_version = versions

    # webOS writes no `Hostname:`. `New member discovered:` never lists the node's own
    # IP, so the difference against `Members:` leaves exactly one candidate.
    if not identity.own_ip and identity.members:
        candidates = [ip for ip in identity.members if ip not in discovered]
        if len(candidates) == 1:
            identity.own_ip, identity.own_ip_source = candidates[0], "inferred"
    return identity


def load(path: Path, alias: str) -> LogFile:
    lines = reader.read_lines(path)
    events, unparsed = parser.parse_lines(lines)
    return LogFile(path, alias, lines, events, unparsed, extract_identity(events))


def resolve_paths(analysis_id: str | None, path: str | None, root: Path) -> list[Path]:
    """Every log file in scope, sorted so aliases are stable across runs."""
    if analysis_id:
        base = an.analyses_root(root) / analysis_id / "logs"
    elif path:
        base = Path(path)
    else:
        return []
    if base.is_file():
        return [base]
    if not base.is_dir():
        return []
    return sorted((p for p in base.rglob("*") if p.is_file() and p.suffix.lower() == ".log"),
                  key=lambda p: p.as_posix())


def load_all(paths: list[Path]) -> list[LogFile]:
    return [load(path, f"F{index}") for index, path in enumerate(paths, start=1)]


def identity_signals(identity: Identity) -> set[str]:
    """Every value that can prove two files are the same screen."""
    signals = set()
    if identity.machine_id:
        signals.add(f"id:{identity.machine_id}")
    if identity.machine and not identity.machine_ambiguous:
        signals.add(f"name:{identity.machine}")
    if identity.own_ip and identity.own_ip_source != "inferred":
        signals.add(f"ip:{identity.own_ip}")
    return signals


def by_screen(files: list[LogFile]) -> dict[str, list[LogFile]]:
    """Group files by screen, reconciling whatever evidence each file happens to carry.

    Files do not all carry the same identity fields: a file with no status block has no
    `Machine ID:`, so keying on one field alone splits a screen in two. Two files belong
    together when they share any strong signal, and the group takes the most readable
    name available. Files with no identity at all stay separate — never merged on a
    guess.
    """
    groups: list[tuple[set[str], list[LogFile]]] = []
    for item in files:
        signals = identity_signals(item.identity)
        if not signals:
            groups.append((set(), [item]))
            continue
        merged = [g for g in groups if g[0] & signals]
        if not merged:
            groups.append((set(signals), [item]))
            continue
        keep = merged[0]
        keep[0].update(signals)
        keep[1].append(item)
        for other in merged[1:]:
            keep[0].update(other[0])
            keep[1].extend(other[1])
            groups.remove(other)

    named: dict[str, list[LogFile]] = {}
    for signals, members in groups:
        label = next((s[5:] for s in sorted(signals) if s.startswith("name:")), None) \
            or next((s[3:] for s in sorted(signals) if s.startswith("id:")), None) \
            or next((s[3:] for s in sorted(signals) if s.startswith("ip:")), None) \
            or f"?{members[0].alias}"
        while label in named:
            label += "'"
        named[label] = members
    return named


def relative(path: Path, root: Path) -> str:
    """A POSIX citation path, identical on every platform."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def write_manifest(analysis_dir: Path, files: list[LogFile], root: Path) -> Path:
    target = analysis_dir / MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": [{
            "alias": f.alias,
            "path": relative(f.path, analysis_dir),
            "lines": len(f.lines),
            "parse_rate": round(f.parse_rate, 6),
            "boots": f.boots,
            "identity": asdict(f.identity),
        } for f in files],
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    return target
