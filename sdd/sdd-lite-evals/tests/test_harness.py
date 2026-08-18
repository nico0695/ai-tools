from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.common import file_manifest, hash_tree, manifest_delta, prepare_fixture, schema_errors
from lib.providers import child_command, extract_assistant_text, parse_observations
from lib.reporting import compare_runs, derive_verdict
from lib.runner import attach_analysis, init_workspace, resume_level3, run_level1, run_level2, start_level3
from lib.validators import CANONICAL_SKILLS, evaluate_probe_assertions, level1_validate


def write(path: Path, content: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fake_project(root: Path) -> None:
    sdd = root / "sdd-lite"
    required = [
        "orchestrator/modules/review-runtime.md",
        "orchestrator/modules/closeout-runtime.md",
        "orchestrator/modules/exceptional-recovery.md",
        "templates/wrappers/agents-orchestrator.md",
        "templates/wrappers/claude-orchestrator.md",
        "project-context.md",
        "skill-catalog.md",
    ]
    for name in required:
        write(sdd / name)
    wrapper_template = '<!-- sdd-lite:start generated_at="x" version="0.2" package_root="sdd-lite" -->\n<!-- sdd-lite:end -->\n'
    write(sdd / "templates/wrappers/agents-orchestrator.md", wrapper_template)
    write(sdd / "templates/wrappers/claude-orchestrator.md", wrapper_template)
    runtime = "\n".join(
        [
            "# Runtime",
            "Do not preload modules",
            "review-runtime.md closeout-runtime.md exceptional-recovery.md",
            "sddl-proposal sddl-spec sddl-design sddl-plan sddl-executor sddl-qa-review",
        ]
    )
    write(sdd / "orchestrator/SDDL-RUNTIME.md", runtime)
    schema = yaml.safe_dump({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"})
    write(sdd / "schemas/config.schema.yaml", schema)
    write(sdd / "schemas/state.schema.yaml", schema)
    write(sdd / "openspec/config.yaml", "{}\n")
    artifacts = {
        "sddl-proposal": "proposal.md",
        "sddl-spec": "spec.md",
        "sddl-design": "design.md",
        "sddl-plan": "plan.md",
        "sddl-executor": "execution-log.md",
        "sddl-qa-review": "qa-report.md",
    }
    for skill in CANONICAL_SKILLS:
        artifact = artifacts.get(skill, "config.yaml")
        write(sdd / "skills" / skill / "SKILL.md", "---\nname: %s\n---\n%s\n" % (skill, artifact))
        write(root / ".agents" / "skills" / skill / "SKILL.md", "---\nname: %s\n---\n" % skill)
        write(root / ".claude" / "skills" / skill / "SKILL.md", "---\nname: %s\n---\n" % skill)
    for artifact in artifacts.values():
        write(sdd / "templates" / "artifacts" / artifact)
    wrapper = """<!-- sdd-lite:start generated_at="x" version="0.2" package_root="sdd-lite" -->
sddl_role
stage
orchestration_allowed: false
runtime_loading_allowed: false
orchestrator/SDDL-RUNTIME.md
<!-- sdd-lite:end -->
"""
    write(root / "AGENTS.md", wrapper)


class LevelOneTests(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_project(root)
            result = level1_validate(root, "sdd-lite")
            self.assertEqual("PASS", result["verdict"], result)

    def test_missing_installation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = level1_validate(Path(temp), "sdd-lite")
            self.assertEqual("BLOCKED", result["verdict"])

    def test_duplicate_claude_wrapper_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_project(root)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            write(root / "CLAUDE.md", "@AGENTS.md\n" + agents)
            result = level1_validate(root, "sdd-lite")
            self.assertEqual("WARN", result["verdict"])
            self.assertIn("claude-duplicate-wrapper", [item["id"] for item in result["findings"]])


class CommonTests(unittest.TestCase):
    def test_hash_ignores_evaluator_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src.txt", "one")
            write(root / ".agents/skills/sddl-eval/SKILL.md", "first")
            before = hash_tree(root)
            write(root / ".agents/skills/sddl-eval/SKILL.md", "second")
            self.assertEqual(before, hash_tree(root))

    def test_manifest_delta(self) -> None:
        self.assertEqual(
            {"added": ["c"], "deleted": ["b"], "modified": ["a"]},
            manifest_delta({"a": "1", "b": "2"}, {"a": "3", "c": "4"}),
        )

    def test_fixture_contains_working_copy_but_not_eval_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            fixture = base / "fixture"
            source.mkdir()
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.email", "eval@example.com"], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.name", "Eval"], check=True)
            write(source / "README.md", "base")
            subprocess.run(["git", "-C", str(source), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-qm", "base"], check=True)
            write(source / "deleted.txt", "tracked")
            subprocess.run(["git", "-C", str(source), "add", "deleted.txt"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-qm", "tracked deletion fixture"], check=True)
            (source / "deleted.txt").unlink()
            write(source / "working.txt", "uncommitted")
            write(source / ".agents/skills/sddl-eval/SKILL.md", "control")
            prepare_fixture(source, fixture)
            self.assertTrue((fixture / "working.txt").is_file())
            self.assertFalse((fixture / "deleted.txt").exists())
            self.assertFalse((fixture / ".agents/skills/sddl-eval").exists())


class AssertionTests(unittest.TestCase):
    def test_probe_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            results = evaluate_probe_assertions(
                [
                    {"type": "output_contains_any", "values": ["proposal"]},
                    {"type": "output_not_contains_any", "values": ["worker mode"]},
                    {"type": "source_unchanged"},
                ],
                "Next: sddl-proposal",
                "",
                "",
                0,
                root,
                {"a": "1"},
                {"a": "1"},
            )
            self.assertEqual(["passed", "passed", "passed"], [item["status"] for item in results])

    def test_warning_drives_warn_verdict(self) -> None:
        self.assertEqual("WARN", derive_verdict([{"status": "warning"}], []))


class ProviderTests(unittest.TestCase):
    def test_commands_use_clean_session_flags(self) -> None:
        fixture = Path("/tmp/fixture")
        self.assertIn("--ephemeral", child_command("codex", "codex", fixture, "prompt"))
        self.assertIn("--no-session-persistence", child_command("claude", "claude", fixture, "prompt"))
        self.assertNotIn("--continue", child_command("opencode", "opencode", fixture, "prompt"))

    def test_usage_parser(self) -> None:
        output = "\n".join(
            [
                json.dumps({"usage": {"input_tokens": 10, "output_tokens": 2}, "model": "m1"}),
                json.dumps({"usage": {"input_tokens": 15, "output_tokens": 5}, "model": "m1"}),
            ]
        )
        parsed = parse_observations(output)
        self.assertEqual(15, parsed["tokens"]["input_tokens"])
        self.assertEqual(["m1"], parsed["models"])

    def test_assistant_text_excludes_user_prompt(self) -> None:
        output = "\n".join(
            [
                json.dumps({"type": "user", "message": {"role": "user", "content": "preflight"}}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "next stage"}}),
            ]
        )
        self.assertEqual("next stage", extract_assistant_text("codex", output))


class SchemaAndInitTests(unittest.TestCase):
    def test_all_evaluator_skills_have_matching_frontmatter(self) -> None:
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(6, len(skills))
        for path in skills:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            frontmatter = yaml.safe_load(text.split("---", 2)[1])
            self.assertEqual(path.parent.name, frontmatter["name"])
            self.assertTrue(frontmatter["description"].strip())

    def test_shipped_templates_validate(self) -> None:
        pairs = [
            ("project.yaml", "project.schema.yaml"),
            ("case.yaml", "case.schema.yaml"),
            ("campaign.yaml", "campaign.schema.yaml"),
            ("provider-analysis.yaml", "analysis.schema.yaml"),
        ]
        for template, schema in pairs:
            data = yaml.safe_load((ROOT / "templates" / template).read_text(encoding="utf-8"))
            self.assertEqual([], schema_errors(data, schema), template)

    def test_run_schema_resolves_finding_reference(self) -> None:
        run = {
            "version": "0.1",
            "run_id": "run",
            "level": 1,
            "campaign_id": "campaign",
            "project_id": "project",
            "provider": "none",
            "status": "complete",
            "verdict": "WARN",
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
            "inputs": {},
            "environment": {},
            "assertions": [{"id": "a", "status": "warning", "evidence": "e"}],
            "findings": [
                {
                    "id": "f",
                    "fingerprint": "fingerprint",
                    "severity": "medium",
                    "title": "title",
                    "evidence": "evidence",
                    "recommendation": "recommendation",
                    "path": None,
                    "assertion_id": "a",
                }
            ],
        }
        self.assertEqual([], schema_errors(run, "run.schema.yaml"))

    def test_init_creates_independent_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as project_temp, tempfile.TemporaryDirectory() as workspace_temp:
            project = Path(project_temp)
            fake_project(project)
            target_workspace = Path(workspace_temp) / "sample"
            with mock.patch("lib.runner.workspace_path", return_value=target_workspace):
                result = init_workspace(project, "codex", "sample", install_method="none")
                updated = init_workspace(project, "claude", "sample", install_method="none")
                level1 = run_level1("sample")
            self.assertEqual("ready", result["status"])
            self.assertEqual("updated", updated["workspace_status"])
            self.assertTrue((target_workspace / "project.yaml").is_file())
            self.assertTrue((target_workspace / "cases/main-flow-example.yaml").is_file())
            profile = yaml.safe_load((target_workspace / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual({"codex", "claude"}, set(profile["providers"]))
            self.assertEqual("PASS", level1["verdict"])

    def test_level2_runs_with_provider_adapter_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as project_temp, tempfile.TemporaryDirectory() as workspace_temp:
            project = Path(project_temp)
            fake_project(project)
            fake_cli = project / "fake-codex"
            write(
                fake_cli,
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print('fake-codex 1.0' if '--version' in sys.argv else json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'probe ok'}}))\n",
            )
            fake_cli.chmod(0o755)
            target_workspace = Path(workspace_temp) / "sample"
            with mock.patch("lib.runner.workspace_path", return_value=target_workspace):
                init_workspace(project, "codex", "sample", install_method="none")
                profile = yaml.safe_load((target_workspace / "project.yaml").read_text(encoding="utf-8"))
                profile["providers"]["codex"]["executable"] = str(fake_cli)
                write(target_workspace / "project.yaml", yaml.safe_dump(profile, sort_keys=False))
                case = yaml.safe_load((target_workspace / "cases/main-flow-example.yaml").read_text(encoding="utf-8"))
                case["probes"]["smoke"] = [
                    {
                        "id": "adapter",
                        "prompt": "Run probe",
                        "assertions": [{"type": "output_contains_any", "values": ["probe ok"]}],
                    }
                ]
                write(target_workspace / "cases/main-flow-example.yaml", yaml.safe_dump(case, sort_keys=False))
                run = run_level2("sample", "main-flow-example", "codex")
                analysis_path = target_workspace / "analysis.yaml"
                write(
                    analysis_path,
                    yaml.safe_dump(
                        {
                            "version": "0.1",
                            "run_id": run["run_id"],
                            "summary": "Provider prompt is compatible.",
                            "limitations": ["Tool reads were not observable."],
                            "findings": [
                                {
                                    "id": "provider-warning",
                                    "severity": "low",
                                    "title": "Provider-specific warning",
                                    "evidence": "Observed in final output.",
                                    "recommendation": "Keep monitoring.",
                                    "path": None,
                                    "assertion_id": None,
                                }
                            ],
                        },
                        sort_keys=False,
                    ),
                )
                analyzed = attach_analysis("sample", run["run_id"], analysis_path)
            self.assertEqual("PASS", run["verdict"])
            self.assertTrue(Path(run["run_dir"]).joinpath("report.md").is_file())
            self.assertEqual(1, run["usage"]["model_calls"])
            self.assertEqual("complete", analyzed["analysis_status"])
            self.assertEqual("cli-analysis", analyzed["findings"][-1]["source"])
            self.assertEqual("WARN", analyzed["verdict"])

    def test_level3_requires_then_records_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as project_temp, tempfile.TemporaryDirectory() as workspace_temp:
            project = Path(project_temp)
            fake_project(project)
            fake_cli = project / "fake-codex"
            write(
                fake_cli,
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                "if '--version' in sys.argv:\n"
                "    print('fake-codex 1.0')\n"
                "    raise SystemExit(0)\n"
                "root=pathlib.Path.cwd()\n"
                "change=root/'sdd-lite/openspec/changes/test-change'\n"
                "change.mkdir(parents=True, exist_ok=True)\n"
                "prompt=' '.join(sys.argv)\n"
                "if 'explicitly approves' in prompt:\n"
                "    (root/'feature.txt').write_text('implemented\\n')\n"
                "    (change/'execution-log.md').write_text('# execution\\n')\n"
                "    (change/'qa-report.md').write_text('# qa\\n')\n"
                "    lifecycle='completed'\n"
                "else:\n"
                "    [(change/name).write_text('# '+name+'\\n') for name in ['proposal.md','spec.md','design.md','plan.md']]\n"
                "    lifecycle='planned'\n"
                "(change/'state.yaml').write_text('lifecycle_status: '+lifecycle+'\\n')\n"
                "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':lifecycle}}))\n",
            )
            fake_cli.chmod(0o755)
            target_workspace = Path(workspace_temp) / "sample"
            with mock.patch("lib.runner.workspace_path", return_value=target_workspace):
                init_workspace(project, "codex", "sample", install_method="none")
                profile = yaml.safe_load((target_workspace / "project.yaml").read_text(encoding="utf-8"))
                profile["providers"]["codex"]["executable"] = str(fake_cli)
                write(target_workspace / "project.yaml", yaml.safe_dump(profile, sort_keys=False))
                started = start_level3("sample", "main-flow-example", "codex")
                self.assertEqual("awaiting_approval", started["status"])
                finished = resume_level3("sample", started["run_id"], "implementation-stage-1")
            self.assertEqual("complete", finished["status"])
            self.assertEqual("PASS", finished["verdict"])
            self.assertEqual("human-confirmation", finished["approvals"][0]["source"])
            self.assertEqual(2, finished["usage"]["model_calls"])


class ComparisonTests(unittest.TestCase):
    def test_model_difference_confounds_baseline(self) -> None:
        base = {
            "provider": "codex",
            "case_id": "case",
            "inputs": {"project_hash": "same"},
            "environment": {"models": ["a"]},
            "assertions": [],
            "findings": [],
        }
        candidate = dict(base)
        candidate["environment"] = {"models": ["b"]}
        self.assertEqual("confounded", compare_runs(candidate, base)["comparability"])

    def test_finding_delta_uses_stable_fingerprints(self) -> None:
        baseline = {
            "provider": "codex",
            "case_id": "case",
            "inputs": {"project_hash": "same"},
            "environment": {"models": []},
            "assertions": [],
            "findings": [{"fingerprint": "old", "severity": "medium"}],
        }
        candidate = dict(baseline)
        candidate["findings"] = [{"fingerprint": "new", "severity": "high"}]
        delta = compare_runs(candidate, baseline)["finding_delta"]
        self.assertEqual(["new"], delta["new"])
        self.assertEqual(["old"], delta["resolved"])


if __name__ == "__main__":
    unittest.main()
