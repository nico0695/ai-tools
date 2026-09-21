from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .common import EvalError, TEMPLATES_ROOT, read_json, schema_errors, utc_now, write_json


SPANISH = {
    "PASS": "Todos los controles requeridos y observables pasaron.",
    "WARN": "La ejecución terminó con advertencias o evidencia no observable.",
    "FAIL": "Se detectó una violación observable del contrato.",
    "BLOCKED": "La instalación o el fixture no permiten una evaluación confiable.",
    "PENDING": "La ejecución espera una aprobación humana o una continuación.",
}

ENGLISH = {
    "PASS": "All required observable checks passed.",
    "WARN": "The run completed with warnings or unobservable evidence.",
    "FAIL": "An observable contract violation was detected.",
    "BLOCKED": "The installation or fixture cannot support a trustworthy evaluation.",
    "PENDING": "The run is waiting for human approval or continuation.",
}


def markdown_table(headers: List[str], rows: Iterable[Iterable[Any]]) -> str:
    rendered = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        rendered.append("| " + " | ".join(str(value).replace("\n", " ").replace("|", "\\|") for value in row) + " |")
    return "\n".join(rendered)


def summary_for(verdict: str, language: str) -> str:
    return (SPANISH if language == "es" else ENGLISH).get(verdict, verdict)


def derive_verdict(assertions: List[Dict[str, Any]], findings: List[Dict[str, Any]], status: str = "complete") -> str:
    if status == "blocked":
        return "BLOCKED"
    if status == "awaiting_approval":
        return "PENDING"
    if any(item.get("status") == "failed" for item in assertions):
        return "FAIL"
    if any(item.get("status") in ("warning", "not_observable") for item in assertions):
        return "WARN"
    if findings:
        return "WARN"
    return "PASS"


def render_run_report(run: Dict[str, Any], language: str = "es") -> str:
    environment = dict(run.get("environment", {}))
    environment.update(
        {
            "level": run.get("level"),
            "provider": run.get("provider"),
            "case": run.get("case_id"),
            "sdd_hash": run.get("inputs", {}).get("sdd_hash"),
            "project_hash": run.get("inputs", {}).get("project_hash"),
        }
    )
    env_table = markdown_table(["Campo", "Valor"], ((key, value) for key, value in environment.items()))
    assertion_table = markdown_table(
        ["Assertion", "Estado", "Evidencia"],
        ((item.get("id"), item.get("status"), item.get("evidence", "")) for item in run.get("assertions", [])),
    )
    findings = run.get("findings", [])
    if findings:
        finding_text = "\n".join(
            "- **%s — %s:** %s  \n  Evidencia: %s  \n  Recomendación: %s"
            % (
                item.get("severity", "info").upper(),
                item.get("title", item.get("id")),
                item.get("path") or "sin path",
                item.get("evidence", ""),
                item.get("recommendation", ""),
            )
            for item in findings
        )
    else:
        finding_text = "- Sin hallazgos." if language == "es" else "- No findings."
    usage = run.get("usage", {})
    evidence_rows = [
        ("Run directory", run.get("run_dir", "")),
        ("Status", run.get("status")),
        ("Started", run.get("started_at")),
        ("Completed", run.get("completed_at")),
        ("Usage", json.dumps(usage, ensure_ascii=False, sort_keys=True)),
    ]
    recommendations = [item.get("recommendation") for item in findings if item.get("recommendation")]
    recommendation_text = "\n".join("- " + value for value in recommendations) or (
        "- No se requieren acciones." if language == "es" else "- No action required."
    )
    template = (TEMPLATES_ROOT / "run-report.md").read_text(encoding="utf-8")
    return template.format(
        run_id=run.get("run_id"),
        verdict=run.get("verdict"),
        summary=summary_for(run.get("verdict", "WARN"), language),
        environment_table=env_table,
        assertions_table=assertion_table,
        findings=finding_text,
        analysis=run.get("analysis_summary") or ("Pendiente para este run." if language == "es" else "Pending for this run."),
        evidence=markdown_table(["Dato", "Valor"], evidence_rows),
        recommendations=recommendation_text,
    )


def save_run(run_dir: Path, run: Dict[str, Any], language: str = "es") -> None:
    run["run_dir"] = str(run_dir)
    errors = schema_errors(run, "run.schema.yaml")
    if errors:
        raise EvalError("Generated run does not satisfy run.schema.yaml: %s" % "; ".join(errors))
    write_json(run_dir / "run.json", run)
    (run_dir / "report.md").write_text(render_run_report(run, language), encoding="utf-8")


def discover_runs(workspace: Path, campaign_id: Optional[str] = None) -> List[Tuple[Path, Dict[str, Any]]]:
    root = workspace / "runs"
    if campaign_id:
        root = root / campaign_id
    result = []
    if not root.is_dir():
        return result
    for path in sorted(root.rglob("run.json")):
        try:
            result.append((path.parent, read_json(path)))
        except Exception:
            continue
    return result


def rebuild_history(workspace: Path) -> Dict[str, Any]:
    runs = discover_runs(workspace)
    fingerprints: Dict[str, Dict[str, Any]] = {}
    entries = []
    for path, run in runs:
        entries.append(
            {
                "run_id": run.get("run_id"),
                "campaign_id": run.get("campaign_id"),
                "level": run.get("level"),
                "provider": run.get("provider"),
                "case_id": run.get("case_id"),
                "verdict": run.get("verdict"),
                "started_at": run.get("started_at"),
                "path": str(path),
            }
        )
        for item in run.get("findings", []):
            value = fingerprints.setdefault(
                item["fingerprint"],
                {"title": item.get("title"), "severity": item.get("severity"), "runs": []},
            )
            value["runs"].append(run.get("run_id"))
    history = {"version": "0.1", "generated_at": utc_now(), "runs": entries, "findings": fingerprints}
    write_json(workspace / "history" / "index.json", history)
    return history


def compare_runs(candidate: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    confounders = []
    checks = [
        ("provider", candidate.get("provider"), baseline.get("provider")),
        ("case", candidate.get("case_id"), baseline.get("case_id")),
        ("project_hash", candidate.get("inputs", {}).get("project_hash"), baseline.get("inputs", {}).get("project_hash")),
        ("model", candidate.get("environment", {}).get("models"), baseline.get("environment", {}).get("models")),
    ]
    for name, current, old in checks:
        if current != old:
            confounders.append("%s differs: candidate=%r baseline=%r" % (name, current, old))
    candidate_counts = {
        "passed": sum(item.get("status") == "passed" for item in candidate.get("assertions", [])),
        "failed": sum(item.get("status") == "failed" for item in candidate.get("assertions", [])),
        "findings": len(candidate.get("findings", [])),
    }
    baseline_counts = {
        "passed": sum(item.get("status") == "passed" for item in baseline.get("assertions", [])),
        "failed": sum(item.get("status") == "failed" for item in baseline.get("assertions", [])),
        "findings": len(baseline.get("findings", [])),
    }
    candidate_findings = {item["fingerprint"]: item for item in candidate.get("findings", [])}
    baseline_findings = {item["fingerprint"]: item for item in baseline.get("findings", [])}
    shared = set(candidate_findings) & set(baseline_findings)
    severity_rank = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    finding_delta = {
        "new": sorted(set(candidate_findings) - set(baseline_findings)),
        "resolved": sorted(set(baseline_findings) - set(candidate_findings)),
        "persisting": sorted(shared),
        "regressed": sorted(
            value
            for value in shared
            if severity_rank.get(candidate_findings[value].get("severity"), 0)
            > severity_rank.get(baseline_findings[value].get("severity"), 0)
        ),
    }
    return {
        "comparability": "confounded" if confounders else "comparable",
        "confounders": confounders,
        "candidate": candidate_counts,
        "baseline": baseline_counts,
        "finding_delta": finding_delta,
    }


def render_comparison(candidate: Dict[str, Any], baseline: Dict[str, Any], comparison: Dict[str, Any]) -> str:
    rows = []
    for metric in ("passed", "failed", "findings"):
        current = comparison["candidate"][metric]
        old = comparison["baseline"][metric]
        rows.append((metric, old, current, current - old))
    template = (TEMPLATES_ROOT / "baseline-comparison.md").read_text(encoding="utf-8")
    finding_delta = comparison.get("finding_delta", {})
    delta_text = "\n".join(
        "- %s: %s" % (name, ", ".join(values) if values else "none")
        for name, values in finding_delta.items()
    )
    return template.format(
        candidate_run=candidate.get("run_id"),
        baseline_run=baseline.get("run_id"),
        comparability=comparison["comparability"],
        comparison_table=markdown_table(["Métrica", "Baseline", "Candidate", "Delta"], rows),
        confounders="\n".join("- " + value for value in comparison["confounders"]) or "- Ninguno detectado.",
        finding_delta=delta_text,
    )


def render_campaign(workspace: Path, campaign_id: str) -> Path:
    runs = discover_runs(workspace, campaign_id)
    rows = []
    verdicts = []
    for path, run in runs:
        verdicts.append(run.get("verdict"))
        rows.append(
            (
                run.get("run_id"),
                run.get("provider"),
                run.get("level"),
                run.get("case_id"),
                run.get("verdict"),
                path,
            )
        )
    if not runs:
        summary = "No runs found."
    elif "FAIL" in verdicts or "BLOCKED" in verdicts:
        summary = "La campaña contiene fallos o bloqueos."
    elif "WARN" in verdicts or "PENDING" in verdicts:
        summary = "La campaña terminó con advertencias o pasos pendientes."
    else:
        summary = "Todas las ejecuciones pasaron."
    template = (TEMPLATES_ROOT / "campaign-report.md").read_text(encoding="utf-8")
    content = template.format(
        campaign_id=campaign_id,
        summary=summary,
        runs_table=markdown_table(["Run", "Provider", "Level", "Case", "Verdict", "Path"], rows),
        patterns="- Revisar los findings repetidos en `history/index.json`.",
        recommendations="- Comparar sólo contra el baseline explícito de la campaña.",
    )
    output = workspace / "reports" / campaign_id / "campaign-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    rebuild_history(workspace)
    return output
