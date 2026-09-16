#!/usr/bin/env python3
"""Which known-bug signatures match, and with what evidence."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loga_core import cli, logset, target as tg  # noqa: E402
from loga_core import parser as logfmt  # noqa: E402

SPEC = {
    "name": "loga_check",
    "question": "which known-bug signatures match these logs",
    "use_when": "the symptom sounds like something seen before",
    "not_for": "finding something new — that is loga_summary and the explorer",
    "args": "--analysis <id> | --path <dir> [--signature ID] [--domain D] [--all]",
    "columns": "signature, verdict, evidence",
    "size": "one block per signature",
    "group": "query",
}

HIT, MISS, INSUFFICIENT = "hit", "miss", "insufficient_data"


def load_catalog() -> dict:
    path = Path(__file__).resolve().parent / "catalog.toml"
    with path.open("rb") as handle:
        return tomllib.load(handle)


def compile_patterns(catalog: dict) -> dict:
    out = {}
    for entry in catalog.get("patterns", []):
        out[entry["id"]] = {**entry, "re": re.compile(entry["regex"])}
    return out


def match_fields(pattern: dict, event) -> dict | None:
    found = logfmt.search(pattern["re"], event)
    if not found:
        return None
    fields = {k: v for k, v in (found.groupdict() or {}).items()}
    if pattern.get("derive") == "sync-members":
        members, masters = logset.members_and_masters(fields.get("members") or "")
        fields["members"] = len(members)
        fields["masters"] = len(masters)
        fields["group"] = (fields.get("group") or "").strip()
    return fields


_CONDITION = re.compile(r"^(?P<field>\w+)\s*(?P<op>==|!=|>=|<=|>|<)\s*(?P<value>.+)$")


def holds(expression: str | None, fields: dict) -> bool:
    """A deliberately tiny language: `field op value`, joined with `and`."""
    if not expression:
        return True
    for clause in expression.split(" and "):
        found = _CONDITION.match(clause.strip())
        if not found:
            return False
        left = fields.get(found.group("field"))
        raw = found.group("value").strip().strip("'\"")
        try:
            left_value, right_value = float(left), float(raw)
        except (TypeError, ValueError):
            left_value, right_value = str(left), raw
        op = found.group("op")
        ok = {"==": left_value == right_value, "!=": left_value != right_value,
              ">": left_value > right_value, "<": left_value < right_value,
              ">=": left_value >= right_value, "<=": left_value <= right_value}[op]
        if not ok:
            return False
    return True


def evaluate(signature: dict, patterns: dict, files, target) -> tuple[str, list[str], str]:
    """Returns verdict, evidence citations, and why when there is no verdict."""
    rule = signature.get("rule")
    needed = signature.get("steps") or [signature.get("pattern")]
    unknown = [p for p in needed if p and p not in patterns]
    if unknown:
        return INSUFFICIENT, [], f"the catalog has no pattern {', '.join(unknown)}"

    evidence: list[str] = []

    if rule == "match":
        pattern = patterns[signature["pattern"]]
        seen = 0
        for item in files:
            for event in item.events:
                fields = match_fields(pattern, event)
                if fields is None:
                    continue
                seen += 1
                if holds(signature.get("where"), fields):
                    evidence.append(tg.cite(item, event.number, target))
        if not seen:
            return INSUFFICIENT, [], f"no line matches {signature['pattern']}, so the " \
                                     f"condition could not be evaluated"
        return (HIT if evidence else MISS), evidence, ""

    if rule == "count":
        pattern = patterns[signature["pattern"]]
        window = signature.get("window_s", 900)
        for item in files:
            hits = [e for e in item.events if match_fields(pattern, e) is not None]
            for index, anchor in enumerate(hits):
                inside = [h for h in hits[index:]
                          if (h.timestamp - anchor.timestamp).total_seconds() <= window
                          and not h.is_epoch and not anchor.is_epoch]
                if len(inside) >= signature.get("min_count", 3):
                    evidence.append(f"{tg.cite(item, anchor.number, target)}"
                                    f" … {tg.cite(item, inside[-1].number, target)}"
                                    f" ({len(inside)} in {window} s)")
                    break
        return (HIT if evidence else MISS), evidence, ""

    if rule == "streak":
        pattern = patterns[signature["pattern"]]
        breaker = patterns.get(signature.get("breaks_on", ""))
        minimum = signature.get("min_streak", 3)
        for item in files:
            run: list = []
            for event in item.events:
                if match_fields(pattern, event) is not None:
                    run.append(event)
                    continue
                if breaker and match_fields(breaker, event) is not None and run:
                    if len(run) >= minimum:
                        evidence.append(f"{tg.cite(item, run[0].number, target)}"
                                        f" … {tg.cite(item, run[-1].number, target)}"
                                        f" ({len(run)} consecutive)")
                    run = []
            if len(run) >= minimum:
                evidence.append(f"{tg.cite(item, run[0].number, target)}"
                                f" … {tg.cite(item, run[-1].number, target)}"
                                f" ({len(run)} consecutive)")
        return (HIT if evidence else MISS), evidence, ""

    if rule == "sequence":
        steps = [patterns[s] for s in signature["steps"]]
        window = signature.get("within_ms", 200) / 1000
        for item in files:
            for index, event in enumerate(item.events):
                if match_fields(steps[0], event) is None:
                    continue
                position, cursor = 1, index + 1
                while position < len(steps) and cursor < len(item.events):
                    candidate = item.events[cursor]
                    if (candidate.timestamp - event.timestamp).total_seconds() > window:
                        break
                    if match_fields(steps[position], candidate) is not None:
                        position += 1
                    cursor += 1
                if position == len(steps):
                    evidence.append(f"{tg.cite(item, event.number, target)}"
                                    f" … {tg.cite(item, item.events[cursor - 1].number, target)}")
        if not evidence:
            starts = sum(1 for item in files for e in item.events
                         if match_fields(steps[0], e) is not None)
            if not starts:
                return INSUFFICIENT, [], f"no line matches the first step " \
                                         f"({signature['steps'][0]}), so the sequence " \
                                         f"could not begin"
        return (HIT if evidence else MISS), evidence, ""

    return INSUFFICIENT, [], f"unsupported rule {rule!r}"


def main() -> int:
    parser = argparse.ArgumentParser(description=SPEC["question"])
    cli.add_target_args(parser)
    parser.add_argument("--signature", default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--all", action="store_true", help="also show misses in full")
    cli.add_common_args(parser)
    args = parser.parse_args()

    envelope = cli.Envelope(script=SPEC["name"])
    target = tg.resolve(args, envelope)
    if target is None:
        cli.emit(envelope, "", args, {"error": "no logs"})
        return cli.EXIT_INPUT

    catalog = load_catalog()
    patterns = compile_patterns(catalog)
    signatures = catalog.get("signatures", [])
    if args.signature:
        signatures = [s for s in signatures if s["id"] == args.signature]
        if not signatures:
            envelope.ok = False
            envelope.warn(f"no signature {args.signature!r}; run loga_index.py --catalog")
            cli.emit(envelope, "", args, {"error": "unknown signature"})
            return cli.EXIT_ARGS

    results = []
    for signature in signatures:
        verdict, evidence, why = evaluate(signature, patterns, target.files, target)
        results.append({"id": signature["id"], "symptom": signature.get("symptom", ""),
                        "severity": signature.get("severity", ""), "verdict": verdict,
                        "evidence": evidence[:5], "found": len(evidence), "why": why,
                        "note": signature.get("note", "")})

    hits = [r for r in results if r["verdict"] == HIT]
    unknown = [r for r in results if r["verdict"] == INSUFFICIENT]
    envelope.total = len(results)
    envelope.returned = len(hits)
    for item in unknown:
        envelope.warn(f"{item['id']}: insufficient_data — {item['why']}")
    if not hits:
        envelope.warn("no signature matched; that is a result, and it is not the same as "
                      "the screen being healthy")

    body = ["# Known-bug check", "",
            f"- {len(hits)} hit · {sum(1 for r in results if r['verdict'] == MISS)} miss "
            f"· {len(unknown)} insufficient_data", ""]
    for result in results:
        if result["verdict"] == MISS and not args.all:
            continue
        body += [f"## `{result['id']}` — {result['verdict']}",
                 f"*{result['symptom']}*" + (f" · severity `{result['severity']}`"
                                             if result["severity"] else ""), ""]
        if result["evidence"]:
            body += [f"- `{item}`" for item in result["evidence"]]
            if result["found"] > len(result["evidence"]):
                body.append(f"- … {result['found'] - len(result['evidence'])} more")
        elif result["why"]:
            body.append(f"- {result['why']}")
        if result["note"]:
            body.append(f"- note: {result['note']}")
        body.append("")
    if not args.all:
        body.append("Misses are hidden; add --all to see them.")
    body += ["", "`insufficient_data` means the logs could not answer, which is different "
                 "from the signature not matching."]
    body += tg.legend(target)
    cli.emit(envelope, "\n".join(body), args, {"results": results})
    return tg.partial_exit(target)


if __name__ == "__main__":
    cli.run(main)
