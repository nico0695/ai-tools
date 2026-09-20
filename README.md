# ai-tools

Repository for reusable AI tooling:

- `agents/`
- `skills/`

## Structure

```text
agents/              reusable agent definitions
skills/stable/       validated skills, ready to install
skills/experimental/ skills under construction and testing
skills/evals/        static routing expectations
scripts/installer/   installer source (Node, no dependencies)
install.sh           installer launcher (macOS, Linux, Git Bash)
install.cmd          installer launcher (Windows)
```

## Installing skills

Requires Node >= 20.

```bash
git clone https://github.com/nico0695/ai-tools.git
cd your-project
/path/to/ai-tools/install.sh        # Windows: \path\to\ai-tools\install.cmd
```

Run the installer from the target project to install into its Git root, or pass
`--user` for a user-wide installation. The interactive menus (arrow keys, space, enter) ask for
the scope, the skills (stable preselected, experimental below a divider), and the providers
(Claude Code and Agents are always offered; Cursor, Continue, and OpenCode appear when detected).

Skills are always copied, so installations survive changes to this repository. Running the
installer again updates them: before confirming, it compares each destination with the
catalog and shows one state per skill:

- `new`: not installed yet.
- `up to date` (`=`): identical to the catalog; left untouched.
- `update` (`*`): installed by this tool and outdated; replaced.
- `unmanaged` (`~`): something with the same name that this tool did not install; skipped unless
  you choose to overwrite it (or pass `--force`).
- `missing` (`!`): registered but deleted from disk; installed again.

Data lives in `~/.config/ai-tools/targets/<destination>/` (override the root with
`AI_TOOLS_HOME`): a `manifest.json` with what was installed there, and a `backup/` with what the
last run replaced. `README.md`, `USAGE.md`, `evals/` and `*-workspace` are not installed.

Non-interactive usage:

```bash
./install.sh --list                        # available skills, stable and experimental
./install.sh --status                      # what is installed, and whether it is up to date
./install.sh --user --all -y               # every stable skill, user-wide
./install.sh --user --all --experimental -y
./install.sh --project ~/app --skills doc-writer,grill-me --providers claude,agents -y
./install.sh --project ~/app --uninstall --skills doc-writer
```

Options (`--help` prints the complete reference):

- `--project PATH` installs in the project scope; `--user` installs user-wide.
- `--skills a,b,c` selects skills from either stage; `--all` selects every stable skill,
  and `--experimental` adds the experimental ones.
- `--providers a,b` selects providers; without it, Claude Code plus Agents when `.agents/` exists.
- `--list` lists available skills; `--status` shows installations and their state.
- `--uninstall` removes only what this tool recorded at the selected destination, so other
  projects and user-wide installations are untouched.
- `--force` overwrites `unmanaged` entries; `-y` or `--yes` skips prompts and skips them.

Flags only answer questions in advance: whatever is missing is asked interactively, or is an error
without a terminal (or with `-y`).

The catalog is `skills/stable/` and `skills/experimental/` (see [skills/README.md](./skills/README.md)).
A directory is a skill when it contains `SKILL.md`; when a name exists in both stages, the
stable one is installed. How the installer is built: [scripts/installer/README.md](./scripts/installer/README.md).
