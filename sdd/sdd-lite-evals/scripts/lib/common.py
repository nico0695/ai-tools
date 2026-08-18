from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from jsonschema import Draft202012Validator, RefResolver


HARNESS_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_ROOT = HARNESS_ROOT / "schemas"
TEMPLATES_ROOT = HARNESS_ROOT / "templates"
WORKSPACES_ROOT = HARNESS_ROOT / "workspaces"

IGNORED_DIRS = {
    ".git",
    ".next",
    ".cache",
    ".turbo",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".sdd-lite-evals",
    "sdd-lite-evals",
}


class EvalError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not value:
        raise EvalError("A non-empty lowercase project or case id is required")
    return value


def new_run_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    entropy = hashlib.sha256(os.urandom(16)).hexdigest()[:8]
    return "%s-%s-%s" % (slugify(prefix), stamp, entropy)


def read_yaml(path: Path) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalError("Missing YAML file: %s" % path) from exc
    except yaml.YAMLError as exc:
        raise EvalError("Invalid YAML in %s: %s" % (path, exc)) from exc
    if not isinstance(data, dict):
        raise EvalError("Expected a mapping in %s" % path)
    return data


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    atomic_write(path, text)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalError("Missing JSON file: %s" % path) from exc
    except json.JSONDecodeError as exc:
        raise EvalError("Invalid JSON in %s: %s" % (path, exc)) from exc
    if not isinstance(data, dict):
        raise EvalError("Expected a JSON object in %s" % path)
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temp_name, str(path))
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def schema_errors(instance: Dict[str, Any], schema_name: str) -> List[str]:
    schema_path = SCHEMAS_ROOT / schema_name
    schema = read_yaml(schema_path)
    resolver = RefResolver(base_uri=SCHEMAS_ROOT.as_uri() + "/", referrer=schema)
    validator = Draft202012Validator(schema, resolver=resolver)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append("%s: %s" % (location, error.message))
    return errors


def workspace_path(workspace_id: str) -> Path:
    return WORKSPACES_ROOT / slugify(workspace_id)


def is_evaluator_skill(path: Path) -> bool:
    return any(part.startswith("sddl-eval") for part in path.parts)


def should_ignore(relative: Path) -> bool:
    if any(part in IGNORED_DIRS for part in relative.parts):
        return True
    if is_evaluator_skill(relative):
        return True
    return False


def iter_files(root: Path, excluded_roots: Iterable[Path] = ()) -> Iterable[Tuple[Path, Path]]:
    exclusions = [item.resolve() for item in excluded_roots]
    for path in sorted(root.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(root)
        if should_ignore(relative):
            continue
        resolved = path.resolve(strict=False)
        if any(resolved == item or item in resolved.parents for item in exclusions):
            continue
        yield path, relative


def hash_tree(root: Path, excluded_roots: Iterable[Path] = ()) -> str:
    digest = hashlib.sha256()
    for path, relative in iter_files(root, excluded_roots):
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(os.readlink(str(path)).encode("utf-8"))
        else:
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def file_manifest(root: Path, exclude_sdd_root: Optional[Path] = None) -> Dict[str, str]:
    excluded = [exclude_sdd_root] if exclude_sdd_root else []
    result: Dict[str, str] = {}
    for path, relative in iter_files(root, excluded):
        if path.is_symlink():
            payload = ("symlink:" + os.readlink(str(path))).encode("utf-8")
        else:
            payload = path.read_bytes()
        result[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
    return result


def manifest_delta(before: Dict[str, str], after: Dict[str, str]) -> Dict[str, List[str]]:
    return {
        "added": sorted(set(after) - set(before)),
        "deleted": sorted(set(before) - set(after)),
        "modified": sorted(path for path in set(before) & set(after) if before[path] != after[path]),
    }


def git_output(project_root: Path, args: List[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root)] + args,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def project_git_metadata(project_root: Path) -> Dict[str, Any]:
    top = git_output(project_root, ["rev-parse", "--show-toplevel"])
    head = git_output(project_root, ["rev-parse", "HEAD"])
    status = git_output(project_root, ["status", "--porcelain=v1"])
    return {
        "root": top,
        "head": head,
        "dirty": bool(status),
        "status": status.splitlines() if status else [],
    }


def overlay_working_copy(source: Path, destination: Path) -> None:
    for current, dirs, files in os.walk(str(source)):
        current_path = Path(current)
        relative_dir = current_path.relative_to(source)
        dirs[:] = [name for name in dirs if not should_ignore(relative_dir / name)]
        target_dir = destination / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            relative = relative_dir / name
            if should_ignore(relative):
                continue
            src = source / relative
            dst = destination / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() or dst.is_symlink():
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(str(dst))
                else:
                    dst.unlink()
            if src.is_symlink():
                dst.symlink_to(os.readlink(str(src)))
            else:
                shutil.copy2(str(src), str(dst))


def prepare_fixture(project_root: Path, fixture_root: Path) -> Dict[str, Any]:
    if fixture_root.exists():
        raise EvalError("Fixture already exists: %s" % fixture_root)
    fixture_root.parent.mkdir(parents=True, exist_ok=True)
    git = project_git_metadata(project_root)
    if git.get("root") and git.get("head"):
        result = subprocess.run(
            ["git", "clone", "--shared", "--no-hardlinks", str(project_root), str(fixture_root)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise EvalError("Could not clone project fixture: %s" % result.stderr.strip())
    else:
        fixture_root.mkdir(parents=True)
    overlay_working_copy(project_root, fixture_root)
    if git.get("root") and git.get("head"):
        deleted = subprocess.run(
            ["git", "-C", str(project_root), "diff", "--name-only", "--diff-filter=D", "-z", "HEAD"],
            capture_output=True,
            check=False,
        )
        if deleted.returncode == 0:
            for raw_name in deleted.stdout.split(b"\0"):
                if not raw_name:
                    continue
                name = raw_name.decode("utf-8", errors="surrogateescape")
                relative = Path(name)
                if relative.is_absolute() or ".." in relative.parts:
                    continue
                target = fixture_root / relative
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(str(target))
                elif target.exists() or target.is_symlink():
                    target.unlink()
    for path in sorted(fixture_root.rglob("sddl-eval*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(str(path))
        elif path.exists() or path.is_symlink():
            path.unlink()
    leaks = [
        path.relative_to(fixture_root).as_posix()
        for path in fixture_root.rglob("sddl-eval*")
        if path.exists() or path.is_symlink()
    ]
    if leaks:
        raise EvalError("Evaluator skills leaked into fixture: %s" % ", ".join(leaks))
    return {
        "source_git": git,
        "fixture_root": str(fixture_root),
        "fixture_hash": hash_tree(fixture_root),
    }


def find_state_files(project_root: Path, sdd_root: str) -> List[Path]:
    changes = project_root / sdd_root / "openspec" / "changes"
    if not changes.is_dir():
        return []
    return sorted(changes.glob("*/state.yaml"))


def summarize_state(project_root: Path, sdd_root: str) -> Dict[str, Any]:
    states = find_state_files(project_root, sdd_root)
    summaries = []
    for path in states:
        try:
            data = read_yaml(path)
        except EvalError as exc:
            summaries.append({"path": str(path), "error": str(exc)})
            continue
        summaries.append(
            {
                "path": str(path.relative_to(project_root)),
                "change_name": data.get("change_name") or path.parent.name,
                "current_stage": data.get("current_stage"),
                "lifecycle_status": data.get("lifecycle_status"),
                "next_action": data.get("next_action"),
            }
        )
    return {"count": len(states), "changes": summaries}


def infer_language(project_root: Path, requested: str) -> str:
    if requested in ("es", "en"):
        return requested
    for name in ("sdd-lite/openspec/config.yaml", "README.md", "CLAUDE.md", "AGENTS.md"):
        path = project_root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:12000].lower()
        if "chat_language: es" in text or any(word in text for word in (" proyecto ", " pruebas ", " ejecutar ")):
            return "es"
    return "en"
