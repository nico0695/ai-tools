import { readFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import { printList, printStatus, runInstall, runUninstall } from './core/flow.js';
import installers from './installers/index.js';
import { fail, log } from './ui/output.js';

const HELP = `Usage: ./install.sh [installer] [options]

Installs skills from this repo into a project or your user folder.
Anything not given as a flag is asked interactively.

Options:
  --project PATH     install into a project (default: git root of cwd, or cwd)
  --user             install into your user folder (HOME)
  --skills a,b       these skills (stable or experimental); commas or repeated flag
  --all              all stable skills
  --experimental     with --all, also the experimental ones
  --providers a,b    claude, agents, cursor, continue, opencode; commas or repeated flag
  --list             show the catalog and exit
  --status           show what is installed in the project and user folder
  --uninstall        remove what this installer registered (accepts --skills)
  --force            overwrite unmanaged copies
  -y, --yes          no questions; unmanaged copies are skipped
  -h, --help         show this help
  --version          show the version

Examples:
  ./install.sh
  ./install.sh --project ~/app --skills 4r-review,commit-closer
  ./install.sh --user --all --experimental --providers claude,agents -y
  ./install.sh --status

Windows: install.cmd, same options.
`;

const OPTIONS = /** @type {const} */ ({
  project: { type: 'string' },
  user: { type: 'boolean' },
  skills: { type: 'string', multiple: true },
  all: { type: 'boolean' },
  experimental: { type: 'boolean' },
  providers: { type: 'string', multiple: true },
  list: { type: 'boolean' },
  status: { type: 'boolean' },
  uninstall: { type: 'boolean' },
  force: { type: 'boolean' },
  yes: { type: 'boolean', short: 'y' },
  help: { type: 'boolean', short: 'h' },
  version: { type: 'boolean' },
});

function splitList(flag, values) {
  if (!values) return undefined;
  const list = values.flatMap((v) => v.split(',')).map((v) => v.trim()).filter(Boolean);
  if (!list.length) throw new Error(`--${flag} requires a value`);
  return list;
}

export function parseCli(argv) {
  const { values, positionals } = parseArgs({ args: argv, options: OPTIONS, allowPositionals: true });
  if (values.user && values.project !== undefined) throw new Error('--user and --project cannot be combined');
  if (values.project === '') throw new Error('--project requires a path');
  if (positionals.length > 1) throw new Error(`unexpected argument: ${positionals[1]}`);
  return {
    ...values,
    installer: positionals[0],
    skills: splitList('skills', values.skills),
    providers: splitList('providers', values.providers),
  };
}

function pickInstaller(id) {
  if (id === undefined && installers.length === 1) return installers[0];
  const installer = installers.find((i) => i.id === id);
  if (!installer) throw new Error(`unknown installer: ${id} (options: ${installers.map((i) => i.id).join(', ')})`);
  return installer;
}

export async function main(argv) {
  try {
    const args = parseCli(argv);
    if (args.help) {
      log(HELP.trimEnd());
      return 0;
    }
    if (args.version) {
      const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'));
      log(pkg.version);
      return 0;
    }
    const installer = pickInstaller(args.installer);
    if (args.list) return printList(installer);
    if (args.status) return printStatus(installer, args);
    if (args.uninstall) return await runUninstall(installer, args);
    return await runInstall(installer, args);
  } catch (err) {
    fail(err.message);
    return 1;
  }
}
