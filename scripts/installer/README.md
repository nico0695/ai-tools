# installer

Source of the repo's `install.sh` (macOS, Linux, Git Bash) and `install.cmd` (Windows). Plain
JavaScript for Node >= 20: no dependencies, no build step, no `npm install`.

```bash
./install.sh                                   # interactive: scope, skills, agents
./install.sh --project ~/app --all -y          # stable skills into a project, no questions
./install.sh --status                          # what is installed and whether it is up to date
node scripts/installer/cli.js --help           # same thing without the launcher
```

User options are in the [root README](../../README.md). How it is built and how a run works — pieces,
flow, states, data, adding an installer, limitations — is in [docs/installer.md](docs/installer.md).

```text
cli.js  main.js     entry: Node version check, flags, dispatch
core/               generic logic (flow, plan, file operations, manifest)
ui/                 terminal output and arrow-key menus
installers/         one module per installer (skills.js)
types.d.ts          the installer contract
test/               unit tests
```

## Tests

```bash
cd scripts/installer
npm test
source ~/.nvm/nvm.sh && nvm exec 20 npm test    # Node 20
```
