from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

from .common import EvalError, file_manifest, manifest_delta, read_yaml


CANONICAL_SKILLS = [
    "sddl-init",
    "sddl-proposal",
    "sddl-spec",
    "sddl-design",
    "sddl-plan",
    "sddl-executor",
    "sddl-qa-review",
]

MAIN_ARTIFACT_TEMPLATES = [
    "proposal.md",
    "spec.md",
    "design.md",
    "plan.md",
    "execution-log.md",
    "qa-report.md",
]

REQUIRED_PACKAGE_PATHS = [
    "orchestrator/SDDL-RUNTIME.md",
    "orchestrator/modules/review-runtime.md",
    "orchestrator/modules/closeout-runtime.md",
    "orchestrator/modules/exceptional-recovery.md",
    "schemas/config.schema.yaml",
    "schemas/state.schema.yaml",
    "templates/wrappers/agents-orchestrator.md",
    "templates/wrappers/claude-orchestrator.md",
]

REQUIRED_BOOTSTRAP_PATHS = [
    "openspec/config.yaml",
    "project-context.md",
    "skill-catalog.md",
]

ROUTE_MARKERS = [
    "sddl-proposal",
    "sddl-spec",
    "sddl-design",
    "sddl-plan",
    "sddl-executor",
    "sddl-qa-review",
]

BYPASS_MARKERS = [
    "sddl_role",
    "stage",
    "orchestration_allowed: false",
    "runtime_loading_allowed: false",
]


def fingerprint(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def finding(
    finding_id: str,
    severity: str,
    title: str,
    evidence: str,
    recommendation: str,
    path: Optional[str] = None,
    assertion_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": finding_id,
        "fingerprint": fingerprint(finding_id, path or "", title),
        "severity": severity,
        "title": title,
        "evidence": evidence,
        "recommendation": recommendation,
        "path": path,
        "assertion_id": assertion_id,
        "source": "deterministic",
    }


def assertion(assertion_id: str, status: str, evidence: str) -> Dict[str, str]:
    return {"id": assertion_id, "status": status, "evidence": evidence}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _validate_yaml_against_schema(instance_path: Path, schema_path: Path) -> List[str]:
    instance = read_yaml(instance_path)
    schema = read_yaml(schema_path)
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append("%s: %s" % (location, error.message))
    return errors


def level1_validate(project_root: Path, sdd_root_name: str) -> Dict[str, Any]:
    sdd_root = (project_root / sdd_root_name).resolve()
    assertions: List[Dict[str, str]] = []
    findings: List[Dict[str, Any]] = []

    if not sdd_root.is_dir():
        assertions.append(assertion("sdd-root-present", "failed", "Missing %s" % sdd_root))
        findings.append(
            finding(
                "missing-sdd-root",
                "critical",
                "sdd-lite is not installed",
                str(sdd_root),
                "Initialize sdd-lite outside this evaluator, then rerun init.",
                str(sdd_root),
                "sdd-root-present",
            )
        )
        return {"verdict": "BLOCKED", "assertions": assertions, "findings": findings}
    assertions.append(assertion("sdd-root-present", "passed", str(sdd_root)))

    missing = [path for path in REQUIRED_PACKAGE_PATHS if not (sdd_root / path).is_file()]
    missing += [path for path in REQUIRED_BOOTSTRAP_PATHS if not (sdd_root / path).is_file()]
    for skill in CANONICAL_SKILLS:
        if not (sdd_root / "skills" / skill / "SKILL.md").is_file():
            missing.append("skills/%s/SKILL.md" % skill)
    for artifact in MAIN_ARTIFACT_TEMPLATES:
        if not (sdd_root / "templates" / "artifacts" / artifact).is_file():
            missing.append("templates/artifacts/%s" % artifact)
    if missing:
        assertions.append(assertion("required-files", "failed", "Missing: %s" % ", ".join(sorted(missing))))
        findings.append(
            finding(
                "missing-required-files",
                "critical",
                "Required sdd-lite files are missing",
                ", ".join(sorted(missing)),
                "Install a complete matching sdd-lite package before behavioral tests.",
                sdd_root_name,
                "required-files",
            )
        )
    else:
        assertions.append(assertion("required-files", "passed", "All core package and bootstrap files exist"))

    config_path = sdd_root / "openspec" / "config.yaml"
    config_schema = sdd_root / "schemas" / "config.schema.yaml"
    if config_path.is_file() and config_schema.is_file():
        try:
            errors = _validate_yaml_against_schema(config_path, config_schema)
        except EvalError as exc:
            errors = [str(exc)]
        status = "failed" if errors else "passed"
        assertions.append(assertion("config-schema", status, "; ".join(errors) if errors else "config.yaml is valid"))
        if errors:
            findings.append(
                finding(
                    "invalid-config",
                    "high",
                    "Installed config does not satisfy its schema",
                    "; ".join(errors),
                    "Refresh the bootstrap config with the matching sdd-lite version.",
                    str(config_path.relative_to(project_root)),
                    "config-schema",
                )
            )

    state_schema = sdd_root / "schemas" / "state.schema.yaml"
    states = sorted((sdd_root / "openspec" / "changes").glob("*/state.yaml")) if (sdd_root / "openspec" / "changes").is_dir() else []
    state_errors = []
    for state in states:
        try:
            errors = _validate_yaml_against_schema(state, state_schema)
        except EvalError as exc:
            errors = [str(exc)]
        state_errors.extend("%s: %s" % (state.relative_to(project_root), error) for error in errors)
    assertions.append(
        assertion(
            "state-schemas",
            "failed" if state_errors else "passed",
            "; ".join(state_errors) if state_errors else "%d state file(s) valid" % len(states),
        )
    )
    if state_errors:
        findings.append(
            finding(
                "invalid-state",
                "high",
                "Persisted state violates the installed schema",
                "; ".join(state_errors),
                "Resolve state/schema drift before resume or end-to-end tests.",
                sdd_root_name + "/openspec/changes",
                "state-schemas",
            )
        )

    runtime_path = sdd_root / "orchestrator" / "SDDL-RUNTIME.md"
    runtime = _read(runtime_path) if runtime_path.is_file() else ""
    route_missing = [marker for marker in ROUTE_MARKERS if marker not in runtime]
    assertions.append(
        assertion(
            "main-route-markers",
            "failed" if route_missing else "passed",
            "Missing: %s" % ", ".join(route_missing) if route_missing else "All canonical main-route stages are referenced",
        )
    )
    if "SDDL-ORCHESTRATOR.md" in runtime:
        findings.append(
            finding(
                "legacy-runtime-reference",
                "high",
                "Runtime still references the retired monolithic orchestrator",
                "SDDL-ORCHESTRATOR.md appears in SDDL-RUNTIME.md",
                "Replace the legacy path with SDDL-RUNTIME.md or a lazy module path.",
                str(runtime_path.relative_to(project_root)),
                "main-route-markers",
            )
        )

    lazy_markers = ["Do not preload modules", "review-runtime.md", "closeout-runtime.md", "exceptional-recovery.md"]
    lazy_missing = [marker for marker in lazy_markers if marker not in runtime]
    assertions.append(
        assertion(
            "lazy-module-contract",
            "failed" if lazy_missing else "passed",
            "Missing: %s" % ", ".join(lazy_missing) if lazy_missing else "Runtime declares lazy module loading and all three triggers",
        )
    )

    skill_contract_errors = []
    artifact_by_skill = {
        "sddl-proposal": "proposal.md",
        "sddl-spec": "spec.md",
        "sddl-design": "design.md",
        "sddl-plan": "plan.md",
        "sddl-executor": "execution-log.md",
        "sddl-qa-review": "qa-report.md",
    }
    for skill in CANONICAL_SKILLS:
        skill_path = sdd_root / "skills" / skill / "SKILL.md"
        if not skill_path.is_file():
            continue
        text = _read(skill_path)
        if ("name: %s" % skill) not in text[:1000]:
            skill_contract_errors.append("%s frontmatter name mismatch" % skill)
        artifact = artifact_by_skill.get(skill)
        if artifact and artifact not in text:
            skill_contract_errors.append("%s does not reference %s" % (skill, artifact))
    assertions.append(
        assertion(
            "canonical-skill-contracts",
            "failed" if skill_contract_errors else "passed",
            "; ".join(skill_contract_errors) if skill_contract_errors else "Canonical skill names and primary artifacts align",
        )
    )

    wrapper_files = [project_root / "AGENTS.md", project_root / "CLAUDE.md"]
    wrapper_template_versions = []
    for template_name in ("agents-orchestrator.md", "claude-orchestrator.md"):
        template_path = sdd_root / "templates" / "wrappers" / template_name
        if not template_path.is_file():
            continue
        match = re.search(r'<!-- sdd-lite:start[^\n]*version="([^"]+)"', _read(template_path))
        if match:
            wrapper_template_versions.append(match.group(1))
    expected_wrapper_version = wrapper_template_versions[0] if len(set(wrapper_template_versions)) == 1 else None
    assertions.append(
        assertion(
            "wrapper-template-version",
            "passed" if expected_wrapper_version else "failed",
            "version=%s" % expected_wrapper_version if expected_wrapper_version else "Wrapper templates do not declare one matching contract version",
        )
    )
    present_wrappers = [path for path in wrapper_files if path.is_file()]
    if not present_wrappers:
        assertions.append(assertion("installed-wrapper", "failed", "Neither AGENTS.md nor CLAUDE.md exists"))
        findings.append(
            finding(
                "missing-installed-wrapper",
                "critical",
                "No installed AI wrapper was found",
                "Expected AGENTS.md and/or CLAUDE.md",
                "Install the wrapper outside this evaluator before behavioral tests.",
                str(project_root),
                "installed-wrapper",
            )
        )
    else:
        wrapper_failures = []
        for wrapper_path in present_wrappers:
            text = _read(wrapper_path)
            if "<!-- sdd-lite:start" not in text or "<!-- sdd-lite:end -->" not in text:
                wrapper_failures.append("%s has no marked block" % wrapper_path.name)
                continue
            if expected_wrapper_version and ('version="%s"' % expected_wrapper_version) not in text:
                wrapper_failures.append("%s does not declare wrapper contract %s" % (wrapper_path.name, expected_wrapper_version))
            for marker in BYPASS_MARKERS:
                if marker not in text:
                    wrapper_failures.append("%s misses %s" % (wrapper_path.name, marker))
            if "orchestrator/SDDL-RUNTIME.md" not in text:
                wrapper_failures.append("%s misses SDDL-RUNTIME.md" % wrapper_path.name)
            if "SDDL-ORCHESTRATOR.md" in text:
                wrapper_failures.append("%s references legacy runtime" % wrapper_path.name)
        assertions.append(
            assertion(
                "installed-wrapper",
                "failed" if wrapper_failures else "passed",
                "; ".join(wrapper_failures) if wrapper_failures else "Installed wrappers contain runtime and bypass controls",
            )
        )
        if wrapper_failures:
            findings.append(
                finding(
                    "invalid-installed-wrapper",
                    "critical",
                    "Installed wrapper contract is incomplete or stale",
                    "; ".join(wrapper_failures),
                    "Regenerate the marked wrapper block with the installed package.",
                    ", ".join(path.name for path in present_wrappers),
                    "installed-wrapper",
                )
            )

    skill_install_candidates = []
    if (project_root / ".claude" / "skills").is_dir():
        skill_install_candidates.append(project_root / ".claude" / "skills")
    if (project_root / ".agents" / "skills").is_dir():
        skill_install_candidates.append(project_root / ".agents" / "skills")
    if (project_root / ".opencode" / "skills").is_dir():
        skill_install_candidates.append(project_root / ".opencode" / "skills")
    complete_installs = []
    incomplete_installs = []
    for root in skill_install_candidates:
        missing_skills = [skill for skill in CANONICAL_SKILLS if not (root / skill / "SKILL.md").is_file()]
        if missing_skills:
            incomplete_installs.append("%s misses %s" % (root.relative_to(project_root), ",".join(missing_skills)))
        else:
            complete_installs.append(str(root.relative_to(project_root)))
    if complete_installs:
        assertions.append(assertion("installed-skills", "passed", "Complete installs: %s" % ", ".join(complete_installs)))
    else:
        assertions.append(assertion("installed-skills", "failed", "; ".join(incomplete_installs) or "No provider skill directory found"))
        findings.append(
            finding(
                "missing-installed-skills",
                "critical",
                "No complete provider skill installation was found",
                "; ".join(incomplete_installs) or "Expected .agents/skills, .claude/skills, or .opencode/skills",
                "Install all canonical sdd-lite skill directories for at least the active provider.",
                str(project_root),
                "installed-skills",
            )
        )

    agents = project_root / "AGENTS.md"
    claude = project_root / "CLAUDE.md"
    duplicate = False
    if agents.is_file() and claude.is_file():
        claude_text = _read(claude)
        duplicate = "@AGENTS.md" in claude_text and "<!-- sdd-lite:start" in claude_text and "<!-- sdd-lite:start" in _read(agents)
    assertions.append(
        assertion(
            "claude-wrapper-duplication",
            "warning" if duplicate else "passed",
            "CLAUDE.md imports AGENTS.md and also owns a full sdd-lite block" if duplicate else "No obvious full-wrapper duplication",
        )
    )
    if duplicate:
        findings.append(
            finding(
                "claude-duplicate-wrapper",
                "medium",
                "Claude may load two complete sdd-lite wrappers",
                "CLAUDE.md imports @AGENTS.md and contains its own marked block",
                "Keep one complete runtime activation contract and only a compact provider-specific delta.",
                "CLAUDE.md",
                "claude-wrapper-duplication",
            )
        )

    failures = sum(item["status"] == "failed" for item in assertions)
    critical = any(item["severity"] == "critical" for item in findings)
    if critical:
        verdict = "BLOCKED"
    elif failures:
        verdict = "FAIL"
    elif findings:
        verdict = "WARN"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "assertions": assertions, "findings": findings}


def evaluate_probe_assertions(
    specs: List[Dict[str, Any]],
    stdout: str,
    stderr: str,
    events: str,
    exit_code: int,
    fixture_root: Path,
    source_before: Dict[str, str],
    source_after: Dict[str, str],
) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    output_lower = (stdout + "\n" + stderr).lower()
    events_lower = events.lower()
    delta = manifest_delta(source_before, source_after)
    changed = delta["added"] + delta["modified"] + delta["deleted"]
    for index, spec in enumerate(specs):
        kind = spec.get("type")
        assertion_id = "%02d-%s" % (index + 1, kind)
        passed = False
        evidence = ""
        if kind == "exit_code":
            expected = int(spec.get("value", 0))
            passed = exit_code == expected
            evidence = "exit_code=%d expected=%d" % (exit_code, expected)
        elif kind in ("output_contains_any", "output_not_contains_any"):
            values = [str(value).lower() for value in spec.get("values", [])]
            matched = [value for value in values if value in output_lower]
            passed = bool(matched) if kind == "output_contains_any" else not matched
            evidence = "matched=%s" % matched
        elif kind in ("event_contains_any", "event_not_contains_any"):
            values = [str(value).lower() for value in spec.get("values", [])]
            matched = [value for value in values if value in events_lower]
            passed = bool(matched) if kind == "event_contains_any" else not matched
            evidence = "matched=%s" % matched
        elif kind in ("path_exists", "path_absent"):
            target = fixture_root / str(spec.get("path", ""))
            exists = target.exists()
            passed = exists if kind == "path_exists" else not exists
            evidence = "%s exists=%s" % (target, exists)
        elif kind == "source_unchanged":
            passed = not changed
            evidence = "changed=%s" % changed
        else:
            results.append(assertion(assertion_id, "not_observable", "Unknown assertion type: %s" % kind))
            continue
        results.append(assertion(assertion_id, "passed" if passed else "failed", evidence))
    return results
