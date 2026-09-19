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
install.sh           skills installer
```

## Installing skills

```bash
git clone https://github.com/nico0695/ai-tools.git
cd your-project
/path/to/ai-tools/install.sh
```

Run the installer from the target project to install into its Git root, or pass
`--user` for a user-wide installation. The interactive menu asks for the scope, the
skills (stable first, experimental below a divider), and the providers (Claude Code and
Agents are always offered; Cursor, Continue, and OpenCode appear when detected).

Skills are always copied, so installations survive changes to this repository. Running the
installer again updates them: before confirming, it compares each destination with the
catalog and shows one state per skill:

- `nueva`: not installed yet.
- `al dia`: identical to the catalog; left untouched.
- `actualizar`: installed by this script (or an old symlink to this repo) and outdated; replaced.
- `distinta`: a folder with the same name that this script did not install; skipped unless you
  choose to overwrite it (or pass `--force`).

Anything replaced is moved to `~/.config/ai-tools/backups/<timestamp>/` first.

Installations are recorded in `~/.config/ai-tools/manifest` by default. Override that path
with `AI_TOOLS_MANIFEST=/path/to/manifest`.

Non-interactive usage:

```bash
./install.sh --list                        # available skills, stable and experimental
./install.sh --status                      # what is installed, and whether it is up to date
./install.sh --user --all -y               # every stable skill, user-wide
./install.sh --user --all --experimental -y
./install.sh --project ~/app --skills doc-writer,grill-me --providers claude,agents -y
./install.sh --dry-run --user --all -y     # show what it would do
./install.sh --project ~/app --uninstall --skills doc-writer
```

Options:

- `--project PATH` installs in the project scope; `--user` installs user-wide.
- `--skills a,b,c` selects skills from either stage; `--all` selects every stable skill,
  and `--experimental` adds the experimental ones.
- `--providers a,b` selects providers; without it, Claude Code plus Agents when `.agents/` exists.
- `--list` lists available skills; `--status` shows installations and their state.
- `--uninstall` removes only entries recorded for the selected destination.
- `--dry-run` previews writes; `--force` overwrites `distinta` entries.
- `-y` or `--yes` skips prompts and skips `distinta` entries; `--help` prints the complete reference.

`--uninstall` only removes what the installer recorded at the selected destination, so
removing a skill from one project leaves other projects and user-wide installations untouched.

The catalog is `skills/stable/` and `skills/experimental/` (see [skills/README.md](./skills/README.md)).
A directory is a skill when it contains `SKILL.md`; when a name exists in both stages, the
stable one is installed. `evals/` and `*-workspace` folders are not copied.
