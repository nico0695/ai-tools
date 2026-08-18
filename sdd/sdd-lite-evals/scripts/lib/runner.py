from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .common import (
    HARNESS_ROOT,
    TEMPLATES_ROOT,
    EvalError,
    file_manifest,
    hash_tree,
    infer_language,
    manifest_delta,
    new_run_id,
    overlay_working_copy,
    prepare_fixture,
    project_git_metadata,
    read_json,
    read_yaml,
    schema_errors,
    slugify,
    summarize_state,
    find_state_files,
    utc_now,
    workspace_path,
    write_json,
    write_yaml,
)
from .providers import PROVIDERS, provider_spec, provider_version, run_child
from .reporting import derive_verdict, render_campaign, save_run
from .validators import assertion, evaluate_probe_assertions, finding, fingerprint, level1_validate


EVAL_SKILLS = [
    "sddl-eval",
    "sddl-eval-init",
    "sddl-eval-level-1",
    "sddl-eval-level-2",
    "sddl-eval-level-3",
    "sddl-eval-report",
]


def _copy_template(name: str) -> Dict[str, Any]:
    return read_yaml(TEMPLATES_ROOT / name)


def _quality_commands(project_root: Path, sdd_root: str) -> List[str]:
    config = project_root / sdd_root / "openspec" / "config.yaml"
    if not config.is_file():
        return []
    try:
        data = read_yaml(config)
    except EvalError:
        return []
    commands = []
    for name in ("test", "lint", "typecheck", "build"):
        values = (data.get("quality_commands") or {}).get(name) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            if value and value not in commands:
                commands.append(str(value))
    return commands


def install_eval_skills(project_root: Path, provider: str, method: str, skill_dir_override: Optional[str] = None) -> List[str]:
    if method not in ("symlink", "copy", "none"):
        raise EvalError("install method must be symlink, copy, or none")
    if method == "none":
        return []
    target_rel = skill_dir_override or provider_spec(provider)["skill_dir"]
    target_root = project_root / target_rel
    target_root.mkdir(parents=True, exist_ok=True)
    installed = []
    conflicts = []
    for name in EVAL_SKILLS:
        source = HARNESS_ROOT / "skills" / name
        target = target_root / name
        if target.is_symlink() and target.resolve() == source.resolve() and method == "symlink":
            continue
        if target.exists() or target.is_symlink():
            conflicts.append(str(target))
    if conflicts:
        raise EvalError("Refusing to replace existing evaluator skills: %s" % ", ".join(conflicts))
    for name in EVAL_SKILLS:
        source = HARNESS_ROOT / "skills" / name
        target = target_root / name
        if target.is_symlink() and target.resolve() == source.resolve() and method == "symlink":
            installed.append(str(target))
            continue
        if target.exists() or target.is_symlink():
            raise EvalError("Refusing to replace existing evaluator skill: %s" % target)
        if method == "symlink":
            target.symlink_to(source, target_is_directory=True)
        else:
            shutil.copytree(str(source), str(target))
            (target / ".harness-root").write_text(str(HARNESS_ROOT) + "\n", encoding="utf-8")
        installed.append(str(target))
    return installed


def _detect_sdd_skill_dirs(project_root: Path, provider: str) -> List[str]:
    result = []
    canonical = ("sddl-init", "sddl-proposal", "sddl-spec", "sddl-design", "sddl-plan", "sddl-executor", "sddl-qa-review")
    candidates = {
        "codex": (Path(".agents/skills"),),
        "claude": (Path(".claude/skills"),),
        "opencode": (Path(".opencode/skills"), Path(".agents/skills")),
    }[provider]
    for relative in candidates:
        root = project_root / relative
        if root.is_dir() and all((root / skill / "SKILL.md").is_file() for skill in canonical):
            result.append(relative.as_posix())
    return result


def init_workspace(
    project_root: Path,
    provider: str,
    workspace_id: Optional[str] = None,
    sdd_root: str = "sdd-lite",
    install_method: str = "symlink",
    report_language: str = "auto",
    skill_dir_override: Optional[str] = None,
    declared_sdd_version: Optional[str] = None,
) -> Dict[str, Any]:
    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise EvalError("Project root is not a directory: %s" % project_root)
    if provider not in PROVIDERS:
        raise EvalError("Unsupported provider: %s" % provider)
    validation = level1_validate(project_root, sdd_root)
    if validation["verdict"] == "BLOCKED":
        return {"status": "blocked", "validation": validation, "workspace": None}
    detected_sdd_skill_dirs = _detect_sdd_skill_dirs(project_root, provider)
    if not detected_sdd_skill_dirs:
        return {
            "status": "blocked",
            "validation": validation,
            "workspace": None,
            "reason": "No complete sdd-lite skill installation was found for provider %s" % provider,
        }
    workspace_id = slugify(workspace_id or project_root.name)
    workspace = workspace_path(workspace_id)
    existing_profile_path = workspace / "project.yaml"
    if existing_profile_path.exists():
        profile = read_yaml(existing_profile_path)
        if Path(profile.get("project_root", "")).resolve() != project_root or profile.get("sdd_root") != sdd_root:
            raise EvalError("Existing workspace points to a different project or sdd root: %s" % workspace)
        workspace_status = "updated"
    else:
        workspace.mkdir(parents=True)
        profile = _copy_template("project.yaml")
        profile.update(
            {
                "id": workspace_id,
                "project_root": str(project_root),
                "sdd_root": sdd_root,
                "declared_sdd_version": declared_sdd_version,
                "report_language": report_language,
                "quality_commands": _quality_commands(project_root, sdd_root),
                "providers": {},
            }
        )
        workspace_status = "created"
    for name in ("cases", "campaigns", "runs", "reports", "history", "fixtures"):
        (workspace / name).mkdir(exist_ok=True)
    provider_config = {
        "skill_dir": skill_dir_override or provider_spec(provider)["skill_dir"],
        "sdd_skill_dirs": detected_sdd_skill_dirs,
    }
    profile.setdefault("providers", {})[provider] = provider_config
    observed = profile.setdefault("observed", {})
    observed.setdefault("created_at", utc_now())
    observed.update({
        "updated_at": utc_now(),
        "language": infer_language(project_root, report_language),
        "git": project_git_metadata(project_root),
        "project_hash": hash_tree(project_root, [project_root / sdd_root]),
        "sdd_hash": hash_tree(project_root / sdd_root),
    })
    observed.setdefault("provider_versions", {})[provider] = provider_version(provider)
    # Observations are intentionally allowed by the runtime even though the reusable template is minimal.
    write_yaml(workspace / "project.yaml", profile)
    case = _copy_template("case.yaml")
    case_path = workspace / "cases" / ("%s.yaml" % case["id"])
    if not case_path.exists():
        write_yaml(case_path, case)
    campaign = _copy_template("campaign.yaml")
    campaign["project"] = workspace_id
    campaign["providers"] = sorted(profile["providers"])
    campaign_path = workspace / "campaigns" / "default.yaml"
    if not campaign_path.exists():
        write_yaml(campaign_path, campaign)
    else:
        existing_campaign = read_yaml(campaign_path)
        if existing_campaign.get("id") == "default" and existing_campaign.get("project") == workspace_id:
            existing_campaign["providers"] = sorted(profile["providers"])
            write_yaml(campaign_path, existing_campaign)
    installed = install_eval_skills(project_root, provider, install_method, skill_dir_override)
    result = {
        "status": "ready",
        "workspace_status": workspace_status,
        "workspace": str(workspace),
        "project_profile": str(workspace / "project.yaml"),
        "installed_skills": installed,
        "validation": validation,
    }
    write_json(workspace / "init-result.json", result)
    return result


def load_workspace(workspace_id: str) -> Tuple[Path, Dict[str, Any], Path, str]:
    workspace = workspace_path(workspace_id)
    profile = read_yaml(workspace / "project.yaml")
    errors = schema_errors({key: value for key, value in profile.items() if key != "observed"}, "project.schema.yaml")
    if errors:
        raise EvalError("Invalid project profile: %s" % "; ".join(errors))
    project_root = Path(profile["project_root"]).resolve()
    sdd_root = str(profile["sdd_root"])
    return workspace, profile, project_root, sdd_root


def load_case(workspace: Path, case_id: str) -> Dict[str, Any]:
    case = read_yaml(workspace / "cases" / (slugify(case_id) + ".yaml"))
    errors = schema_errors(case, "case.schema.yaml")
    if errors:
        raise EvalError("Invalid case: %s" % "; ".join(errors))
    return case


def _inputs(project_root: Path, sdd_root: str, case: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "project_hash": hash_tree(project_root, [project_root / sdd_root]),
        "sdd_hash": hash_tree(project_root / sdd_root),
        "case_hash": fingerprint(json.dumps(case, sort_keys=True, ensure_ascii=False)) if case else None,
        "git": project_git_metadata(project_root),
    }


def run_level1(workspace_id: str, campaign_id: str = "level1") -> Dict[str, Any]:
    workspace, profile, project_root, sdd_root = load_workspace(workspace_id)
    run_id = new_run_id("level1")
    run_dir = workspace / "runs" / slugify(campaign_id) / "none" / run_id
    run_dir.mkdir(parents=True)
    started = utc_now()
    validation = level1_validate(project_root, sdd_root)
    run = {
        "version": "0.1",
        "run_id": run_id,
        "level": 1,
        "campaign_id": slugify(campaign_id),
        "project_id": profile["id"],
        "case_id": None,
        "provider": "none",
        "status": "blocked" if validation["verdict"] == "BLOCKED" else "complete",
        "verdict": validation["verdict"],
        "started_at": started,
        "completed_at": utc_now(),
        "inputs": _inputs(project_root, sdd_root),
        "environment": {"language": profile.get("observed", {}).get("language", "es")},
        "usage": {"model_calls": 0},
        "assertions": validation["assertions"],
        "findings": validation["findings"],
    }
    save_run(run_dir, run, profile.get("observed", {}).get("language", "es"))
    render_campaign(workspace, slugify(campaign_id))
    return run


def level2_plan(workspace_id: str, case_id: str, profile_name: str) -> Dict[str, Any]:
    workspace, _, _, _ = load_workspace(workspace_id)
    case = load_case(workspace, case_id)
    probes = list(case.get("probes", {}).get("smoke", []))
    if profile_name == "full":
        probes.extend(case.get("probes", {}).get("full", []))
    return {
        "level": 2,
        "profile": profile_name,
        "case": case_id,
        "child_sessions": len(probes),
        "probes": [probe["id"] for probe in probes],
        "warning": "This uses the active CLI default model and has no automatic cost cap.",
    }


def _provider_override(profile: Dict[str, Any], provider: str) -> Optional[str]:
    return (profile.get("providers", {}).get(provider) or {}).get("executable")


def _aggregate_usage(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    token_totals: Dict[str, float] = {}
    costs = 0.0
    has_cost = False
    models = []
    duration = 0.0
    for session in sessions:
        record = session.get("record", session)
        observation = record.get("observations", {})
        for name, value in observation.get("tokens", {}).items():
            token_totals[name] = token_totals.get(name, 0) + value
        if observation.get("cost_usd") is not None:
            costs += observation["cost_usd"]
            has_cost = True
        for model in observation.get("models", []):
            if model not in models:
                models.append(model)
        duration += float(record.get("duration_seconds", 0))
    return {
        "model_calls": len(sessions),
        "tokens": token_totals,
        "cost_usd": round(costs, 6) if has_cost else None,
        "duration_seconds": round(duration, 3),
        "models": models,
    }


def _apply_probe_fixture_setup(workspace: Path, fixture: Path, probe: Dict[str, Any]) -> None:
    setup = probe.get("fixture_setup") or {}
    overlay_dir = setup.get("overlay_dir") or probe.get("fixture_overlay")
    if overlay_dir:
        overlay = (workspace / overlay_dir).resolve()
        if workspace.resolve() not in overlay.parents:
            raise EvalError("Probe overlay must stay inside the workspace: %s" % overlay)
        if not overlay.is_dir():
            raise EvalError("Probe overlay does not exist: %s" % overlay)
        overlay_working_copy(overlay, fixture)
    for value in setup.get("remove_paths", []):
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise EvalError("Probe remove path must be fixture-relative: %s" % value)
        target = fixture / relative
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(str(target))
        elif target.exists() or target.is_symlink():
            target.unlink()


def run_level2(
    workspace_id: str,
    case_id: str,
    provider: str,
    profile_name: str = "smoke",
    campaign_id: str = "level2",
    timeout_seconds: int = 3600,
) -> Dict[str, Any]:
    workspace, profile, project_root, sdd_root = load_workspace(workspace_id)
    if provider not in profile.get("providers", {}):
        raise EvalError("Provider is not configured in project profile: %s" % provider)
    if not profile["providers"][provider].get("sdd_skill_dirs"):
        raise EvalError("No complete sdd-lite skill directory was recorded for provider %s; rerun eval init" % provider)
    validation = level1_validate(project_root, sdd_root)
    if validation["verdict"] in ("BLOCKED", "FAIL"):
        raise EvalError("Level 1 must not be BLOCKED or FAIL before level 2")
    case = load_case(workspace, case_id)
    probes = list(case.get("probes", {}).get("smoke", []))
    if profile_name == "full":
        probes.extend(case.get("probes", {}).get("full", []))
    run_id = new_run_id("level2-%s" % case_id)
    run_dir = workspace / "runs" / slugify(campaign_id) / provider / run_id
    run_dir.mkdir(parents=True)
    all_assertions = []
    all_findings = []
    sessions = []
    for probe in probes:
        probe_dir = run_dir / "probes" / probe["id"]
        fixture = workspace / "fixtures" / run_id / probe["id"]
        prepare_fixture(project_root, fixture)
        _apply_probe_fixture_setup(workspace, fixture, probe)
        sdd_path = fixture / sdd_root
        before = file_manifest(fixture, sdd_path)
        child = run_child(
            provider,
            fixture,
            probe["prompt"],
            probe_dir,
            _provider_override(profile, provider),
            timeout_seconds,
        )
        sessions.append(child["record"])
        after = file_manifest(fixture, sdd_path)
        assertions = evaluate_probe_assertions(
            probe.get("assertions", []),
            child["assistant_text"],
            child["stderr"],
            child["stdout"],
            child["record"]["exit_code"],
            fixture,
            before,
            after,
        )
        for item in assertions:
            item["id"] = "%s/%s" % (probe["id"], item["id"])
            all_assertions.append(item)
            if item["status"] == "failed":
                all_findings.append(
                    finding(
                        "probe-failed-%s" % item["id"].replace("/", "-"),
                        "high",
                        "Behavioral probe assertion failed",
                        item["evidence"],
                        "Inspect the child events and the active provider wrapper before changing the prompt contract.",
                        str(probe_dir),
                        item["id"],
                    )
                )
        write_json(probe_dir / "assertions.json", assertions)
        write_json(probe_dir / "source-delta.json", manifest_delta(before, after))
    usage = _aggregate_usage(sessions)
    verdict = derive_verdict(all_assertions, all_findings)
    run = {
        "version": "0.1",
        "run_id": run_id,
        "level": 2,
        "campaign_id": slugify(campaign_id),
        "project_id": profile["id"],
        "case_id": case["id"],
        "provider": provider,
        "status": "complete",
        "verdict": verdict,
        "started_at": sessions[0]["started_at"] if sessions else utc_now(),
        "completed_at": utc_now(),
        "inputs": _inputs(project_root, sdd_root, case),
        "environment": {
            "provider_version": provider_version(provider, _provider_override(profile, provider)),
            "models": usage["models"],
            "profile": profile_name,
            "language": profile.get("observed", {}).get("language", "es"),
        },
        "usage": usage,
        "sessions": sessions,
        "assertions": all_assertions,
        "findings": all_findings,
        "analysis_status": "pending",
    }
    save_run(run_dir, run, profile.get("observed", {}).get("language", "es"))
    analysis_template = read_yaml(TEMPLATES_ROOT / "provider-analysis.yaml")
    analysis_template["run_id"] = run_id
    write_yaml(run_dir / "analysis-template.yaml", analysis_template)
    render_campaign(workspace, slugify(campaign_id))
    return run


def level3_plan(workspace_id: str, case_id: str) -> Dict[str, Any]:
    workspace, profile, _, _ = load_workspace(workspace_id)
    case = load_case(workspace, case_id)
    return {
        "level": 3,
        "case": case["id"],
        "project": profile["id"],
        "initial_child_sessions": 1,
        "later_sessions": "one fresh process per human-approved checkpoint",
        "optional_protocols": "4R, Judgment Day, delivery, and archive are excluded",
        "warning": "Uses the active CLI default model without an automatic cost cap.",
    }


def _planning_prompt(case: Dict[str, Any]) -> str:
    return """Use the installed sdd-lite main flow for this task:\n\n%s\n\nSession choices: auto pacing and native workers when supported. Treat this as a normal bounded change, not a planner-only objective. Run proposal, spec, design, and plan, then stop at the mandatory implementation approval gate. Do not edit project source code. Do not run optional 4R review, Judgment Day, delivery, or archive. Persist every required artifact and state so a completely new session can resume without chat history.""" % case["task_prompt"]


def _execution_prompt(case: Dict[str, Any], approved_stage: str) -> str:
    return """Resume the single active sdd-lite change exclusively from persisted state and artifacts. The human explicitly approves implementation checkpoint `%s` after reviewing the persisted plan. Execute only the currently approved plan stage, then perform the mandatory sdd-lite QA routing until the next approval gate or final completion. If another approval is required, persist state and stop. Decline/skip optional 4R review, Judgment Day, delivery, and archive. Never use prior CLI conversation history. Original task:\n\n%s""" % (approved_stage, case["task_prompt"])


def _active_change_dir(fixture: Path, sdd_root: str) -> Optional[Path]:
    root = fixture / sdd_root / "openspec" / "changes"
    if not root.is_dir():
        return None
    states = sorted(root.glob("*/state.yaml"))
    return states[0].parent if len(states) == 1 else None


def _artifact_assertions(change_dir: Optional[Path], names: List[str], prefix: str) -> List[Dict[str, str]]:
    result = []
    for name in names:
        exists = bool(change_dir and (change_dir / name).is_file())
        result.append(assertion("%s-%s" % (prefix, name), "passed" if exists else "failed", str(change_dir / name) if change_dir else "No unambiguous active change"))
    return result


def _state_lifecycle(change_dir: Optional[Path]) -> Optional[str]:
    if not change_dir or not (change_dir / "state.yaml").is_file():
        return None
    try:
        return read_yaml(change_dir / "state.yaml").get("lifecycle_status")
    except EvalError:
        return None


def _copy_evidence(fixture: Path, sdd_root: str, run_dir: Path) -> None:
    source = fixture / sdd_root / "openspec" / "changes"
    destination = run_dir / "artifacts"
    if destination.exists():
        shutil.rmtree(str(destination))
    if source.is_dir():
        shutil.copytree(str(source), str(destination))
    git_diff = subprocess.run(
        ["git", "-C", str(fixture), "diff", "--binary"],
        text=True,
        capture_output=True,
        check=False,
    )
    (run_dir / "repository.patch").write_text(git_diff.stdout, encoding="utf-8")


def start_level3(
    workspace_id: str,
    case_id: str,
    provider: str,
    campaign_id: str = "level3",
    timeout_seconds: int = 3600,
) -> Dict[str, Any]:
    workspace, profile, project_root, sdd_root = load_workspace(workspace_id)
    if provider not in profile.get("providers", {}):
        raise EvalError("Provider is not configured in project profile: %s" % provider)
    if not profile["providers"][provider].get("sdd_skill_dirs"):
        raise EvalError("No complete sdd-lite skill directory was recorded for provider %s; rerun eval init" % provider)
    validation = level1_validate(project_root, sdd_root)
    if validation["verdict"] in ("BLOCKED", "FAIL"):
        raise EvalError("Level 1 must not be BLOCKED or FAIL before level 3")
    case = load_case(workspace, case_id)
    if case.get("requires_no_active_changes", True) and find_state_files(project_root, sdd_root):
        raise EvalError("Level 3 case requires a fixture with no active sdd-lite changes")
    run_id = new_run_id("level3-%s" % case_id)
    run_dir = workspace / "runs" / slugify(campaign_id) / provider / run_id
    run_dir.mkdir(parents=True)
    fixture = workspace / "fixtures" / run_id / "project"
    fixture_meta = prepare_fixture(project_root, fixture)
    source_before = file_manifest(fixture, fixture / sdd_root)
    write_json(run_dir / "source-before.json", source_before)
    child = run_child(
        provider,
        fixture,
        _planning_prompt(case),
        run_dir / "sessions" / "planning",
        _provider_override(profile, provider),
        timeout_seconds,
    )
    source_after = file_manifest(fixture, fixture / sdd_root)
    delta = manifest_delta(source_before, source_after)
    change_dir = _active_change_dir(fixture, sdd_root)
    assertions = _artifact_assertions(change_dir, case.get("expected", {}).get("planning_artifacts", []), "planning-artifact")
    assertions.append(assertion("source-unchanged-before-approval", "passed" if not any(delta.values()) else "failed", json.dumps(delta)))
    lifecycle = _state_lifecycle(change_dir)
    expected_lifecycle = case.get("expected", {}).get("planning_lifecycle", [])
    assertions.append(
        assertion(
            "planning-lifecycle",
            "passed" if lifecycle in expected_lifecycle else "failed",
            "lifecycle=%r expected=%r" % (lifecycle, expected_lifecycle),
        )
    )
    findings = []
    for item in assertions:
        if item["status"] == "failed":
            findings.append(
                finding(
                    "level3-planning-%s" % item["id"],
                    "critical" if item["id"] == "source-unchanged-before-approval" else "high",
                    "Level 3 planning checkpoint failed",
                    item["evidence"],
                    "Inspect planning events and persisted state before approving implementation.",
                    str(run_dir),
                    item["id"],
                )
            )
    status = "complete" if any(item["status"] == "failed" for item in assertions) else "awaiting_approval"
    usage = _aggregate_usage([child["record"]])
    run = {
        "version": "0.1",
        "run_id": run_id,
        "level": 3,
        "campaign_id": slugify(campaign_id),
        "project_id": profile["id"],
        "case_id": case["id"],
        "provider": provider,
        "status": status,
        "verdict": derive_verdict(assertions, findings, status),
        "started_at": child["record"]["started_at"],
        "completed_at": utc_now() if status == "complete" else None,
        "inputs": _inputs(project_root, sdd_root, case),
        "environment": {
            "provider_version": provider_version(provider, _provider_override(profile, provider)),
            "models": usage["models"],
            "language": profile.get("observed", {}).get("language", "es"),
        },
        "usage": usage,
        "fixture": fixture_meta,
        "checkpoint_count": 1,
        "approvals": [],
        "state_summary": summarize_state(fixture, sdd_root),
        "assertions": assertions,
        "findings": findings,
        "analysis_status": "pending",
    }
    save_run(run_dir, run, profile.get("observed", {}).get("language", "es"))
    _copy_evidence(fixture, sdd_root, run_dir)
    render_campaign(workspace, slugify(campaign_id))
    return run


def _find_run(workspace: Path, run_id: str) -> Tuple[Path, Dict[str, Any]]:
    matches = list((workspace / "runs").rglob("%s/run.json" % run_id))
    if len(matches) != 1:
        raise EvalError("Expected one run named %s, found %d" % (run_id, len(matches)))
    return matches[0].parent, read_json(matches[0])


def attach_analysis(workspace_id: str, run_id: str, analysis_path: Path) -> Dict[str, Any]:
    workspace, profile, _, _ = load_workspace(workspace_id)
    run_dir, run = _find_run(workspace, run_id)
    analysis = read_yaml(analysis_path.resolve())
    errors = schema_errors(analysis, "analysis.schema.yaml")
    if errors:
        raise EvalError("Invalid CLI analysis: %s" % "; ".join(errors))
    if analysis["run_id"] != run_id:
        raise EvalError("Analysis run_id does not match the target run")
    deterministic = [item for item in run.get("findings", []) if item.get("source", "deterministic") != "cli-analysis"]
    semantic = []
    for item in analysis.get("findings", []):
        semantic.append(
            {
                "id": item["id"],
                "fingerprint": fingerprint(item["id"], item.get("path") or "", item["title"]),
                "severity": item["severity"],
                "title": item["title"],
                "evidence": item["evidence"],
                "recommendation": item["recommendation"],
                "path": item.get("path"),
                "assertion_id": item.get("assertion_id"),
                "source": "cli-analysis",
            }
        )
    run["findings"] = deterministic + semantic
    run["analysis_status"] = "complete"
    run["analysis_summary"] = analysis["summary"]
    run["analysis_limitations"] = analysis.get("limitations", [])
    run["verdict"] = derive_verdict(run.get("assertions", []), run["findings"], run.get("status", "complete"))
    write_yaml(run_dir / "analysis.yaml", analysis)
    analysis_lines = ["# Provider analysis", "", analysis["summary"]]
    if analysis.get("limitations"):
        analysis_lines.extend(["", "## Limitations", ""] + ["- " + value for value in analysis["limitations"]])
    if semantic:
        analysis_lines.extend(["", "## Findings", ""] + ["- **%s:** %s" % (item["severity"].upper(), item["title"]) for item in semantic])
    (run_dir / "analysis.md").write_text("\n".join(analysis_lines) + "\n", encoding="utf-8")
    save_run(run_dir, run, profile.get("observed", {}).get("language", "es"))
    render_campaign(workspace, run["campaign_id"])
    return run


def _run_quality(fixture: Path, commands: List[str], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, command in enumerate(commands):
        args = shlex.split(command)
        if not args:
            continue
        result = subprocess.run(args, cwd=str(fixture), text=True, capture_output=True, check=False, timeout=1800)
        (output_dir / ("%02d-stdout.txt" % (index + 1))).write_text(result.stdout, encoding="utf-8")
        (output_dir / ("%02d-stderr.txt" % (index + 1))).write_text(result.stderr, encoding="utf-8")
        results.append({"command": command, "exit_code": result.returncode})
    return results


def resume_level3(
    workspace_id: str,
    run_id: str,
    approved_stage: str,
    timeout_seconds: int = 3600,
) -> Dict[str, Any]:
    workspace, profile, _, sdd_root = load_workspace(workspace_id)
    run_dir, run = _find_run(workspace, run_id)
    if run.get("level") != 3 or run.get("status") != "awaiting_approval":
        raise EvalError("Run is not an awaiting-approval level-3 run")
    if run.get("provider") not in profile.get("providers", {}):
        raise EvalError("Run provider is no longer configured in the project profile")
    case = load_case(workspace, run["case_id"])
    fixture = Path(run["fixture"]["fixture_root"])
    if not fixture.is_dir():
        raise EvalError("Level 3 fixture is missing: %s" % fixture)
    approval = {"stage": approved_stage, "approved_at": utc_now(), "source": "human-confirmation"}
    run.setdefault("approvals", []).append(approval)
    checkpoint = int(run.get("checkpoint_count", 1)) + 1
    session_dir = run_dir / "sessions" / ("checkpoint-%02d" % checkpoint)
    child = run_child(
        run["provider"],
        fixture,
        _execution_prompt(case, approved_stage),
        session_dir,
        _provider_override(profile, run["provider"]),
        timeout_seconds,
    )
    change_dir = _active_change_dir(fixture, sdd_root)
    lifecycle = _state_lifecycle(change_dir)
    final_lifecycle = case.get("expected", {}).get("final_lifecycle", [])
    completed = lifecycle in final_lifecycle
    assertions = list(run.get("assertions", []))
    forbidden = case.get("expected", {}).get("forbidden_optional_artifacts", [])
    for name in forbidden:
        exists = bool(change_dir and (change_dir / name).exists())
        assertions.append(assertion("optional-artifact-absent-%s-cp%d" % (name, checkpoint), "failed" if exists else "passed", str(change_dir / name) if change_dir else "No active change"))
    if completed:
        assertions.extend(_artifact_assertions(change_dir, case.get("expected", {}).get("final_artifacts", []), "final-artifact"))
    assertions.append(
        assertion(
            "checkpoint-lifecycle-%d" % checkpoint,
            "passed" if lifecycle else "failed",
            "lifecycle=%r" % lifecycle,
        )
    )
    findings = list(run.get("findings", []))
    existing_ids = {item["assertion_id"] for item in findings if item.get("assertion_id")}
    for item in assertions:
        if item["status"] == "failed" and item["id"] not in existing_ids:
            findings.append(
                finding(
                    "level3-checkpoint-%s" % item["id"],
                    "high",
                    "Level 3 checkpoint assertion failed",
                    item["evidence"],
                    "Inspect the fresh-session events and persisted artifacts before another approval.",
                    str(run_dir),
                    item["id"],
                )
            )
    quality = []
    if completed:
        commands = list(case.get("quality_commands") or profile.get("quality_commands") or [])
        quality = _run_quality(fixture, commands, run_dir / "quality")
        for index, result in enumerate(quality):
            assertions.append(
                assertion(
                    "quality-%02d" % (index + 1),
                    "passed" if result["exit_code"] == 0 else "failed",
                    "%s exit_code=%d" % (result["command"], result["exit_code"]),
                )
            )
    run["checkpoint_count"] = checkpoint
    run["status"] = "complete" if completed or any(item["status"] == "failed" for item in assertions) else "awaiting_approval"
    run["completed_at"] = utc_now() if run["status"] == "complete" else None
    run["assertions"] = assertions
    run["findings"] = findings
    run["state_summary"] = summarize_state(fixture, sdd_root)
    run["quality"] = quality
    prior_sessions = []
    for path in sorted((run_dir / "sessions").glob("*/session.json")):
        prior_sessions.append(read_json(path))
    run["usage"] = _aggregate_usage(prior_sessions)
    run["environment"]["models"] = run["usage"]["models"]
    run["verdict"] = derive_verdict(assertions, findings, run["status"])
    save_run(run_dir, run, profile.get("observed", {}).get("language", "es"))
    _copy_evidence(fixture, sdd_root, run_dir)
    render_campaign(workspace, run["campaign_id"])
    return run
