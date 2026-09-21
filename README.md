# ai-tools

Repository for reusable AI tooling:

- `agents/`
- `skills/`
- `harness/`

## Structure

```text
agents/                 reusable agent definitions
skills/stable/          validated skills, ready to install
skills/experimental/    skills under construction and testing
skills/evals/           static routing expectations
harness/stable/         validated harnesses, ready to install into a project
harness/experimental/   harnesses under construction and testing
scripts/installer/      installer source (Node, no dependencies)
install.sh              installer launcher (macOS, Linux, Git Bash)
install.cmd             installer launcher (Windows)
```

## Installing

Requires Node >= 20.

```bash
git clone https://github.com/nico0695/ai-tools.git
cd your-project
/path/to/ai-tools/install.sh        # Windows: \path\to\ai-tools\install.cmd
```

Interactive runs start with Skills or Harness. From this catalog repo, Harness is hidden:
pass `--project` to another app. `--help` is the full flag reference. How the installer is
built: [scripts/installer/README.md](./scripts/installer/README.md).

### Skills

Run the installer from the target project (Git root) or pass `--user` for a user-wide
install. Menus (arrow keys, space, enter) ask for scope, skills (stable preselected,
experimental below a divider), and agents (Claude Code and Agents always; Cursor, Continue,
and OpenCode when detected).

Skills are copied, so they survive changes to this repository. A later run compares each
destination with the catalog:

- `new`: not installed yet.
- `up to date` (`=`): identical to the catalog; left untouched.
- `update` (`*`): installed by this tool and outdated; replaced.
- `unmanaged` (`~`): same name, not installed by this tool; skipped unless you overwrite
  (or pass `--force`).
- `missing` (`!`): registered but gone from disk; installed again.

Data lives in `~/.config/ai-tools/targets/<destination>/` (`AI_TOOLS_HOME` overrides the
root): `manifest.json` plus `backup/` of what the last run replaced. `README.md`,
`USAGE.md`, `evals/` and `*-workspace` are not installed.

```bash
./install.sh --list
./install.sh --status
./install.sh --user --all -y
./install.sh --user --all --experimental -y
./install.sh --project ~/app --skills doc-writer,grill-me --providers claude,agents -y
./install.sh --project ~/app --uninstall --skills doc-writer
```

- `--project PATH` or `--user`.
- `--skills a,b,c` from either stage; `--all` is every stable skill; `--experimental` adds
  the experimental ones.
- `--providers a,b`; default is Claude Code, plus Agents when `.agents/` exists.
- `--uninstall` removes only what this tool recorded at that destination.
- `-y` / `--yes` skips prompts and skips `unmanaged` copies.

The catalog is `skills/stable/` and `skills/experimental/`
([skills/README.md](./skills/README.md)). A folder is a skill when it has `SKILL.md`; if
the name exists in both stages, stable is installed.

### sdd-lite

```bash
./install.sh harness --project ~/app
./install.sh harness --project ~/app --providers claude -y
```

Copies `harness/stable/sdd-lite` to `./sdd-lite/` and `sddl-init` into the chosen agent.
Then run `sddl-init` in that agent. Project only: no `--user`, no `--uninstall`. An update
overwrites the package and leaves `project-context.md`, `skill-catalog.md`, and `openspec/`.
`--status` also reports harness installs.

Guide: [harness/stable/README.md](./harness/stable/README.md),
[USER-GUIDE.md](./harness/stable/sdd-lite/USER-GUIDE.md).
