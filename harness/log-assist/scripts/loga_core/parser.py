"""The Dex Player log format.

Normative source: docs/log-format.md. The rules that live here are the ones
verified over 157,100 real lines; anything corpus-specific is measured by the
calling script, never assumed here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

LEVELS = ("INFO", "SUCCESS", "ERROR", "DEBUG", "WARNING")

# Rule 1. Every line matches this or it is counted as unparsed, never dropped.
LINE_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})\.(?P<cs>\d{2}) "
    r"(?P<level>INFO|SUCCESS|ERROR|DEBUG|WARNING) (?P<message>.*)$"
)

# Rule 5. Exactly one match per boot. The 53-'=' banner works too but must be halved.
BOOT_RE = re.compile(r"^Dex Player [\d.]+$")
BANNER_RE = re.compile(r"^={53}$")
BLOCK_RE = re.compile(r"^={54}$")
SYNC_OPEN_RE = re.compile(r"^={19}SYNC GROUP INFO={20}$")

MAX_BRACKET_GROUPS = 4
_GROUP_RE = re.compile(r"\s*\[([^\]]*)\]")

# Rule 6. Epoch 0 renders as a different local date per timezone, so detect by
# distance from epoch rather than by hardcoding 1969-12-31.
_EPOCH = datetime(1970, 1, 1)
_EPOCH_TOLERANCE = timedelta(days=1)


@dataclass(frozen=True)
class Event:
    number: int              # source line number
    timestamp: datetime
    level: str               # the line level, field 4 — read positionally (rule 2)
    component: str           # bracket groups joined with "/", empty when there are none
    nested_status: str | None   # a bracket group whose content is a level name (rule 3)
    text: str                # the message after the bracket groups
    raw: str                 # the whole line, verbatim

    @property
    def effective_level(self) -> str:
        """The nested status wins when present. See docs/log-format.md 2.4."""
        return self.nested_status or self.level

    @property
    def level_differs(self) -> bool:
        return self.nested_status is not None and self.nested_status != self.level

    @property
    def is_epoch(self) -> bool:
        return abs(self.timestamp - _EPOCH) <= _EPOCH_TOLERANCE

    @property
    def raw_message(self) -> str:
        """The message before bracket groups were split off."""
        match = LINE_RE.match(self.raw)
        return match.group("message") if match else ""

    @property
    def is_boot(self) -> bool:
        return bool(BOOT_RE.match(self.raw_message))


def stamp(moment: datetime) -> str:
    """Render a timestamp the way the log writes it: centiseconds, no more."""
    return f"{moment.strftime('%Y-%m-%d %H:%M:%S')}.{moment.microsecond // 10000:02d}"


def parse_component(message: str) -> tuple[str, str | None, str]:
    """Split leading bracket groups into a component path and a nested status.

    Rule 3: at most 4 groups; a group whose content is exactly a level name is the
    nested status, wherever it sits; the rest form the component path, in order.
    Component names are an open vocabulary — never match them against a list.
    """
    parts: list[str] = []
    pos = 0
    while len(parts) < MAX_BRACKET_GROUPS:
        match = _GROUP_RE.match(message, pos)
        if not match:
            break
        parts.append(match.group(1))
        pos = match.end()

    nested: str | None = None
    component: list[str] = []
    for part in parts:
        if part in LEVELS and nested is None:
            nested = part
        else:
            component.append(part)
    return "/".join(component), nested, message[pos:].lstrip()


def parse_line(number: int, raw: str) -> Event | None:
    """Parse one line. Returns None when the line does not match the format."""
    match = LINE_RE.match(raw)
    if not match:
        return None
    try:
        stamp = datetime.strptime(f"{match.group('date')} {match.group('time')}",
                                  "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    stamp = stamp.replace(microsecond=int(match.group("cs")) * 10000)
    component, nested, text = parse_component(match.group("message"))
    return Event(number, stamp, match.group("level"), component, nested, text, raw)


def parse_lines(lines) -> tuple[list[Event], list[int]]:
    """Parse numbered lines. Returns the events and the numbers that did not parse."""
    events, unparsed = [], []
    for line in lines:
        event = parse_line(line.number, line.text)
        (events.append(event) if event else unparsed.append(line.number))
    return events, unparsed


def parse_rate(events: list[Event], unparsed: list[int]) -> float:
    total = len(events) + len(unparsed)
    return 1.0 if total == 0 else len(events) / total


def count_boots(events: list[Event]) -> int:
    """Rule 5. Counting '=' banners instead would need halving; this does not."""
    return sum(1 for e in events if BOOT_RE.match(e.raw_message))


def epoch_window(events: list[Event]) -> list[Event]:
    """Lines stamped near epoch 0: the player booted before NTP landed.

    Rule 6: exclude these from any wall-clock delta. They are not an anomaly —
    on Tizen they are the normal shape of a boot.
    """
    return [e for e in events if e.is_epoch]


def in_source_order(events: list[Event]) -> list[Event]:
    """Rule 7. Order by position in the file, never by timestamp."""
    return sorted(events, key=lambda e: e.number)


def level_note(events: list[Event]) -> str | None:
    """Rule 4's obligation: say so whenever the effective level is not the line level."""
    differing = sum(1 for e in events if e.level_differs)
    if not differing:
        return None
    return (f"counts use the effective level; {differing} line(s) carry a nested status "
            f"that differs from the line level, so a plain grep will not match these counts")


# --- stack traces -----------------------------------------------------------
# webOS emits each frame as a complete line with its own timestamp and ERROR level,
# so the line format never breaks. A frame is not an event: it belongs to the error
# above it. See docs/log-format.md 3.1.
TRACE_FRAME_RE = re.compile(r"^\s+at\s")


def is_trace_frame(event: Event) -> bool:
    return bool(TRACE_FRAME_RE.match(event.raw_message))


def fold_traces(events: list[Event]) -> tuple[list[Event], dict[int, list[Event]]]:
    """Split events into real events and the frames attached to each.

    Returns the events without frames, plus a map from an event's line number to its
    frames. Frames that are byte-identical are collapsed: the player truncates long
    frames at the line ceiling, so 253 identical frames are one frame cut 253 times.
    """
    kept: list[Event] = []
    frames: dict[int, list[Event]] = {}
    for event in events:
        if is_trace_frame(event) and kept:
            owner = kept[-1].number
            bucket = frames.setdefault(owner, [])
            if not any(f.raw_message == event.raw_message for f in bucket):
                bucket.append(event)
        else:
            kept.append(event)
    return kept, frames


# --- cadence ----------------------------------------------------------------

def deltas(events: list[Event], skip_epoch: bool = True) -> list[float]:
    """Seconds between consecutive events, in source order.

    Epoch-window events are skipped by default: a delta across that boundary is an
    artifact of the missing clock, not a gap. Negative deltas are dropped here and
    surfaced separately by whoever cares about clock corrections.
    """
    usable = [e for e in in_source_order(events) if not (skip_epoch and e.is_epoch)]
    out = []
    for before, after in zip(usable, usable[1:]):
        seconds = (after.timestamp - before.timestamp).total_seconds()
        if seconds >= 0:
            out.append(seconds)
    return out


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def cadence_of(timestamps: list) -> dict:
    """Cadence from timestamps already in the order they should be read.

    Use this when the events come from more than one file: `cadence` re-sorts by line
    number, and line numbers restart in every file, which scrambles a merged stream.
    """
    values = [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])
              if (b - a).total_seconds() >= 0]
    if not values:
        return {"samples": len(timestamps), "median": None, "mode": None,
                "mode_share": 0.0, "deltas": 0}
    rounded = [round(v) for v in values]
    mode = max(set(rounded), key=rounded.count)
    return {"samples": len(timestamps), "median": median(values), "mode": mode,
            "mode_share": rounded.count(mode) / len(rounded), "deltas": len(values)}


def cadence(events: list[Event]) -> dict:
    """The measured rhythm of a signal in ONE file. webOS and Tizen differ 5x."""
    values = deltas(events)
    if not values:
        return {"samples": len(events), "median": None, "mode": None, "deltas": 0}
    rounded = [round(v) for v in values]
    mode = max(set(rounded), key=rounded.count)
    return {
        "samples": len(events),
        "median": median(values),
        "mode": mode,
        "mode_share": rounded.count(mode) / len(rounded),
        "deltas": len(values),
    }


# --- clock corrections ------------------------------------------------------
# 4 of the 6 backward jumps in the corpus are the line right after
# `Server time offset: <N> milliseconds`, and the jump equals that offset: the player
# corrects its clock against the server on boot. Reporting those as gaps turns one
# real anomaly into six. See docs/log-format.md 2.7.
SERVER_OFFSET_RE = re.compile(r"^Server time offset: (?P<ms>-?\d+) milliseconds")


def backward_jumps(events: list[Event]) -> list[dict]:
    """Every backward step in time, each labeled as a clock correction or not."""
    ordered = in_source_order(events)
    found = []
    for before, after in zip(ordered, ordered[1:]):
        if before.is_epoch or after.is_epoch:
            continue
        seconds = (after.timestamp - before.timestamp).total_seconds()
        if seconds >= 0:
            continue
        offset_ms = None
        match = SERVER_OFFSET_RE.match(before.text)
        if match:
            offset_ms = int(match.group("ms"))
        correction = offset_ms is not None and abs(offset_ms / 1000 - seconds) < 1.0
        found.append({
            "from": before.number, "to": after.number, "seconds": seconds,
            "kind": "clock-correction" if correction else "jump",
            "offset_ms": offset_ms,
        })
    return found


# --- periodic signals -------------------------------------------------------
# Signals whose *absence* is the finding. Cadence is always measured, never assumed:
# telemetry is 60 s on Tizen and 300 s on webOS, so a fixed threshold cannot work.
# The message wording differs by platform, so each signal carries alternatives.
# A signal is the *successful* beat, not the attempt. During the 1h37m outage of the
# corpus the player kept emitting `Heartbeat Sync failed` every 60 s, so attempts show
# no gap at all; only the absence of `received` reveals the outage. Failure streaks are
# events, and belong to loga_check, not here.
SIGNALS = {
    "heartbeat": re.compile(r"Heartbeat received from server"),
    "heartbeat-attempt": re.compile(r"Heartbeat (received from server|Sync failed)"),
    "telemetry": re.compile(r"^CPU: [\d.]+%\. Used RAM: [\d.]+ Mb$"),
    "policy": re.compile(r"^Processing policies$"),
    "screenshot": re.compile(r"^Screenshot Uploaded"),
}


def signal_events(events: list[Event], name: str) -> list[Event]:
    matcher = SIGNALS.get(name)
    if matcher is None:
        return []
    return [e for e in events if matcher.search(e.text) or matcher.search(e.raw_message)]


def search(matcher: "re.Pattern", event: Event):
    """Match a catalog pattern against an event.

    A pattern is anchored against the text that follows the component, because that is
    how the reference documentation writes them (`^Fail parsing JSON\\. File:`). Some
    patterns instead include the component, so the raw message is tried as a fallback.
    Never match against the whole line: it always starts with a timestamp.
    """
    return matcher.search(event.text) or matcher.search(event.raw_message)
