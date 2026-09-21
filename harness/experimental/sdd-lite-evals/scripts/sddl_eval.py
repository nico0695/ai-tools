#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from lib.common import EvalError, read_json, workspace_path, write_json
from lib.reporting import compare_runs, rebuild_history, render_campaign, render_comparison
from lib.runner import (
    attach_analysis,
    init_workspace,
    level2_plan,
    level3_plan,
    resume_level3,
    run_level1,
    run_level2,
    start_level3,
)


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def find_run(workspace: Path, run_id: str) -> Dict[str, Any]:
    matches = list((workspace / "runs").rglob("%s/run.json" % run_id))
    if len(matches) != 1:
        raise EvalError("Expected exactly one run %s, found %d" % (run_id, len(matches)))
    return read_json(matches[0])


def command_init(args: argparse.Namespace) -> int:
    result = init_workspace(
        Path(args.project_root),
        args.provider,
        args.workspace_id,
        args.sdd_root,
        args.install_method,
        args.language,
        args.skill_dir,
        args.declared_sdd_version,
    )
    emit(result)
    return 2 if result["status"] == "blocked" else 0


def command_level1(args: argparse.Namespace) -> int:
    run = run_level1(args.workspace, args.campaign)
    emit({"run_id": run["run_id"], "verdict": run["verdict"], "run_dir": run["run_dir"]})
    return 1 if run["verdict"] in ("FAIL", "BLOCKED") else 0


def command_level2(args: argparse.Namespace) -> int:
    plan = level2_plan(args.workspace, args.case, args.profile)
    if not args.execute:
        plan["dry_run"] = True
        plan["next_command"] = "Repeat with --execute after reviewing the warning."
        emit(plan)
        return 0
    run = run_level2(args.workspace, args.case, args.provider, args.profile, args.campaign, args.timeout)
    emit({"run_id": run["run_id"], "verdict": run["verdict"], "run_dir": run["run_dir"], "usage": run["usage"]})
    return 1 if run["verdict"] in ("FAIL", "BLOCKED") else 0


def command_level3(args: argparse.Namespace) -> int:
    if args.resume_run:
        if not args.approve_stage:
            raise EvalError("--approve-stage is required with --resume-run")
        if not args.execute:
            emit(
                {
                    "dry_run": True,
                    "run_id": args.resume_run,
                    "approved_stage": args.approve_stage,
                    "child_sessions": 1,
                    "warning": "This records human approval and starts a fresh CLI process. Repeat with --execute.",
                }
            )
            return 0
        run = resume_level3(args.workspace, args.resume_run, args.approve_stage, args.timeout)
    else:
        if not args.case or not args.provider:
            raise EvalError("--case and --provider are required when starting level 3")
        plan = level3_plan(args.workspace, args.case)
        if not args.execute:
            plan["dry_run"] = True
            plan["next_command"] = "Repeat with --execute to start the planning checkpoint."
            emit(plan)
            return 0
        run = start_level3(args.workspace, args.case, args.provider, args.campaign, args.timeout)
    emit(
        {
            "run_id": run["run_id"],
            "status": run["status"],
            "verdict": run["verdict"],
            "run_dir": run["run_dir"],
            "state_summary": run.get("state_summary"),
            "next": "Review plan and rerun with --resume-run/--approve-stage" if run["status"] == "awaiting_approval" else None,
        }
    )
    return 1 if run["verdict"] in ("FAIL", "BLOCKED") else 0


def command_report(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    report = render_campaign(workspace, args.campaign)
    result: Dict[str, Any] = {"campaign_report": str(report), "history": str(workspace / "history" / "index.json")}
    if args.candidate_run or args.baseline_run:
        if not args.candidate_run or not args.baseline_run:
            raise EvalError("Both --candidate-run and --baseline-run are required for comparison")
        candidate = find_run(workspace, args.candidate_run)
        baseline = find_run(workspace, args.baseline_run)
        comparison = compare_runs(candidate, baseline)
        output = workspace / "reports" / args.campaign / ("comparison-%s-vs-%s.json" % (args.candidate_run, args.baseline_run))
        write_json(output, comparison)
        result["comparison"] = str(output)
        markdown_output = output.with_suffix(".md")
        markdown_output.write_text(render_comparison(candidate, baseline, comparison), encoding="utf-8")
        result["comparison_report"] = str(markdown_output)
        result["comparability"] = comparison["comparability"]
    emit(result)
    return 0


def command_history(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    result = rebuild_history(workspace)
    emit({"runs": len(result["runs"]), "findings": len(result["findings"]), "path": str(workspace / "history" / "index.json")})
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    run = attach_analysis(args.workspace, args.run_id, Path(args.analysis_file))
    emit(
        {
            "run_id": run["run_id"],
            "verdict": run["verdict"],
            "analysis_status": run.get("analysis_status"),
            "run_dir": run["run_dir"],
        }
    )
    return 1 if run["verdict"] in ("FAIL", "BLOCKED") else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Provider-aware local evaluations for an installed sdd-lite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Validate a project and create a local evaluation workspace")
    init.add_argument("--project-root", required=True)
    init.add_argument("--provider", required=True, choices=["codex", "claude", "opencode"])
    init.add_argument("--workspace-id")
    init.add_argument("--sdd-root", default="sdd-lite")
    init.add_argument("--install-method", choices=["symlink", "copy", "none"], default="symlink")
    init.add_argument("--skill-dir")
    init.add_argument("--language", choices=["auto", "es", "en"], default="auto")
    init.add_argument("--declared-sdd-version")
    init.set_defaults(func=command_init)

    level1 = subparsers.add_parser("level1", help="Run deterministic contract and installation checks")
    level1.add_argument("--workspace", required=True)
    level1.add_argument("--campaign", default="level1")
    level1.set_defaults(func=command_level1)

    level2 = subparsers.add_parser("level2", help="Plan or run isolated behavioral probes")
    level2.add_argument("--workspace", required=True)
    level2.add_argument("--case", required=True)
    level2.add_argument("--provider", required=True, choices=["codex", "claude", "opencode"])
    level2.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    level2.add_argument("--campaign", default="level2")
    level2.add_argument("--timeout", type=int, default=3600)
    level2.add_argument("--execute", action="store_true")
    level2.set_defaults(func=command_level2)

    level3 = subparsers.add_parser("level3", help="Plan, start, or continue the main end-to-end flow")
    level3.add_argument("--workspace", required=True)
    level3.add_argument("--case")
    level3.add_argument("--provider", choices=["codex", "claude", "opencode"])
    level3.add_argument("--campaign", default="level3")
    level3.add_argument("--resume-run")
    level3.add_argument("--approve-stage")
    level3.add_argument("--timeout", type=int, default=3600)
    level3.add_argument("--execute", action="store_true")
    level3.set_defaults(func=command_level3)

    report = subparsers.add_parser("report", help="Rebuild campaign reports and optionally compare an explicit baseline")
    report.add_argument("--workspace", required=True)
    report.add_argument("--campaign", required=True)
    report.add_argument("--candidate-run")
    report.add_argument("--baseline-run")
    report.set_defaults(func=command_report)

    analyze = subparsers.add_parser("analyze", help="Attach normalized active-CLI analysis to an existing run")
    analyze.add_argument("--workspace", required=True)
    analyze.add_argument("--run-id", required=True)
    analyze.add_argument("--analysis-file", required=True)
    analyze.set_defaults(func=command_analyze)

    history = subparsers.add_parser("history", help="Rebuild the local immutable run index")
    history.add_argument("--workspace", required=True)
    history.set_defaults(func=command_history)
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except EvalError as exc:
        emit({"error": str(exc), "status": "blocked"})
        return 2
    except KeyboardInterrupt:
        emit({"error": "Interrupted", "status": "blocked"})
        return 130


if __name__ == "__main__":
    sys.exit(main())
