from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .common import EvalError, utc_now, write_json


PROVIDERS: Dict[str, Dict[str, Any]] = {
    "codex": {
        "executable": "codex",
        "skill_dir": ".agents/skills",
        "version_args": ["--version"],
    },
    "claude": {
        "executable": "claude",
        "skill_dir": ".claude/skills",
        "version_args": ["--version"],
    },
    "opencode": {
        "executable": "opencode",
        "skill_dir": ".opencode/skills",
        "version_args": ["--version"],
    },
}


def provider_spec(provider: str, override_executable: Optional[str] = None) -> Dict[str, Any]:
    if provider not in PROVIDERS:
        raise EvalError("Unsupported provider: %s" % provider)
    result = dict(PROVIDERS[provider])
    if override_executable:
        result["executable"] = override_executable
    return result


def executable_path(provider: str, override_executable: Optional[str] = None) -> Optional[str]:
    spec = provider_spec(provider, override_executable)
    return shutil.which(spec["executable"])


def provider_version(provider: str, override_executable: Optional[str] = None) -> Optional[str]:
    spec = provider_spec(provider, override_executable)
    executable = executable_path(provider, override_executable)
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable] + spec["version_args"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    output = result.stdout.strip() or result.stderr.strip()
    return output.splitlines()[0] if output else None


def child_command(provider: str, executable: str, fixture: Path, prompt: str) -> List[str]:
    if provider == "codex":
        return [executable, "exec", "--json", "--ephemeral", "--sandbox", "workspace-write", prompt]
    if provider == "claude":
        return [
            executable,
            "-p",
            "--output-format",
            "stream-json",
            "--no-session-persistence",
            "--permission-mode",
            "acceptEdits",
            prompt,
        ]
    if provider == "opencode":
        return [executable, "run", "--format", "json", "--dir", str(fixture), prompt]
    raise EvalError("Unsupported provider: %s" % provider)


def _walk_values(value: Any, key_path: str = "") -> Iterable[tuple]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = "%s.%s" % (key_path, key) if key_path else str(key)
            yield child_path, child
            yield from _walk_values(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_values(child, "%s[%s]" % (key_path, index))


def parse_observations(stdout: str) -> Dict[str, Any]:
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(parsed)
    counters: Dict[str, float] = {}
    models: List[str] = []
    cost: Optional[float] = None
    token_names = {
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "reasoning_tokens",
        "total_tokens",
    }
    for event in events:
        for key_path, value in _walk_values(event):
            name = key_path.split(".")[-1]
            if name in token_names and isinstance(value, (int, float)):
                counters[name] = max(counters.get(name, 0), value)
            if name in ("model", "model_name") and isinstance(value, str) and value not in models:
                models.append(value)
            if name in ("total_cost_usd", "cost_usd") and isinstance(value, (int, float)):
                cost = max(cost or 0, float(value))
    return {"event_count": len(events), "tokens": counters, "models": models, "cost_usd": cost}


def _content_text(value: Any) -> List[str]:
    texts: List[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            texts.extend(_content_text(item))
    elif isinstance(value, dict):
        if value.get("type") in ("text", "output_text") and isinstance(value.get("text"), str):
            texts.append(value["text"])
        elif isinstance(value.get("content"), (list, dict, str)):
            texts.extend(_content_text(value["content"]))
    return texts


def extract_assistant_text(provider: str, stdout: str) -> str:
    texts: List[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message" and isinstance(item.get("text"), str):
            texts.append(item["text"])
        message = event.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            texts.extend(_content_text(message.get("content")))
        if event.get("role") == "assistant":
            texts.extend(_content_text(event.get("content")))
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            texts.append(event["result"])
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
    # Streaming providers can repeat cumulative content. Preserve order but remove exact duplicates.
    unique = []
    for value in texts:
        if value and value not in unique:
            unique.append(value)
    return "\n".join(unique)


def run_child(
    provider: str,
    fixture: Path,
    prompt: str,
    output_dir: Path,
    executable_override: Optional[str] = None,
    timeout_seconds: int = 3600,
) -> Dict[str, Any]:
    executable = executable_path(provider, executable_override)
    if not executable:
        raise EvalError("Provider executable not found: %s" % provider_spec(provider, executable_override)["executable"])
    output_dir.mkdir(parents=True, exist_ok=True)
    command = child_command(provider, executable, fixture, prompt)
    started_at = utc_now()
    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(fixture),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        result = subprocess.CompletedProcess(command, 124, stdout, stderr)
        timed_out = True
    duration = time.monotonic() - start
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    (output_dir / "events.jsonl").write_text(stdout, encoding="utf-8")
    (output_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    assistant_text = extract_assistant_text(provider, stdout)
    (output_dir / "final-output.txt").write_text(assistant_text, encoding="utf-8")
    observation = parse_observations(stdout)
    record = {
        "provider": provider,
        "provider_version": provider_version(provider, executable_override),
        "command": command[:-1] + ["<prompt>"],
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(duration, 3),
        "exit_code": result.returncode,
        "timed_out": timed_out,
        "observations": observation,
        "stdout_path": str(output_dir / "events.jsonl"),
        "stderr_path": str(output_dir / "stderr.txt"),
    }
    write_json(output_dir / "session.json", record)
    return {"record": record, "stdout": stdout, "stderr": stderr, "assistant_text": assistant_text}
