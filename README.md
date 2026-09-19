# ai-tools

Repository for reusable AI tooling:

- `agents/`
- `skills/generic-skills/`

## Structure

```text
agents/              reusable agent definitions
skills/generic-skills/ reusable skills
install.sh           skills installer
```

## Installing skills

```bash
git clone https://github.com/nico0695/ai-tools.git
cd your-project
/path/to/ai-tools/install.sh
```

Run the installer from the target project to install into its Git root, or pass
`--user` for a user-wide installation. The interactive menu asks for the scope,
skills, detected providers (Claude Code, Cursor, Continue, OpenCode, or Agents),
and whether to symlink (live changes from this repository) or copy (independent files).

Project and user installations are tracked separately in
`~/.config/ai-tools/manifest` by default. Override that path with
`AI_TOOLS_MANIFEST=/path/to/manifest`.

Non-interactive usage:

```bash
./install.sh --list                        # available skills
./install.sh --status                      # what is installed, and where
./install.sh --user --all -y               # everything, user-wide
./install.sh --user --skills grill-me,4r-review --copy -y
./install.sh --project ~/app --skills grill-me --providers claude,agents --link -y
./install.sh --dry-run --user --all -y     # show what it would do
./install.sh --project ~/app --uninstall --skills grill-me
```

Options:

- `--project PATH` installs in the project scope; `--user` installs user-wide.
- `--skills a,b,c` selects skills; `--all` selects every available skill.
- `--providers a,b` selects providers; without it, detected providers are used.
- `--link` creates symlinks to this repository; `--copy` creates independent copies.
- `--list` lists available skills; `--status` shows recorded installations.
- `--uninstall` removes only entries recorded for the selected destination.
- `--dry-run` previews writes; `--force` replaces untracked destination entries.
- `-y` or `--yes` skips prompts; `--help` prints the complete command reference.

`--uninstall` only removes what the installer recorded at the selected destination, so
removing a skill from one project leaves other projects and user-wide installations
untouched. Existing skills from other tools are skipped with a warning unless `--force`
is supplied.

The installer discovers directories containing `SKILL.md`, so runtime scratch directories
and non-skill folders are ignored. The current generic skill set includes
`standard-code-review`, `4r-review`, `commit-closer`, `doc-writer`, `grill-me`,
`judgment-day`, `prototype`, `questionnaire`, and `resolving-merge-conflicts`.
