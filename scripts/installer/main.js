import { readFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import { printList, printStatus, printStatusFooter, runInstall, runUninstall } from './core/flow.js';
import { projectRoot, REPO, resolveBase, samePath } from './core/context.js';
import installers from './installers/index.js';
import { fail, log } from './ui/output.js';
import { isCancel, isInteractive, select } from './ui/prompt.js';

const HELP = `Usage: ./install.sh [skills|harness] [options]

Installs skills or the sdd-lite harness from this repo into a project
(or skills into your user folder). Anything not given as a flag is asked
interactively.

Options:
  --project PATH     install into a project (default: git root of cwd, or cwd)
  --user             install into your user folder (HOME); skills only
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
  ./install.sh harness --project ~/app
  ./install.sh harness --project ~/app --providers claude -y
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

const skillFlags = (args) => Boolean(args.skills || args.all || args.experimental);

function findInstaller(id) {
  const installer = installers.find((i) => i.id === id);
  if (!installer) throw new Error(`unknown installer: ${id} (options: ${installers.map((i) => i.id).join(', ')})`);
  return installer;
}

export function offeredInstallers(args, cwd = process.cwd()) {
  let list = installers;
  if (args.user) list = list.filter((i) => i.scopes.includes('user'));
  const tentative = args.project !== undefined ? resolveBase('project', args.project) : projectRoot(cwd);
  if (samePath(tentative, REPO)) list = list.filter((i) => i.allowSelf !== false);
  return list;
}

function rejectSkillFlags(args, installer) {
  if (installer.id === 'skills' || !skillFlags(args)) return;
  const flag = args.skills ? '--skills' : args.all ? '--all' : '--experimental';
  throw new Error(`${flag} cannot be used with ${installer.id}`);
}

export async function pickInstaller(args, interactive, cwd = process.cwd()) {
  if (args.installer) {
    const installer = findInstaller(args.installer);
    rejectSkillFlags(args, installer);
    return installer;
  }
  if (skillFlags(args) || args.uninstall) return findInstaller('skills');
  if (args.list || args.status) return undefined;
  const offered = offeredInstallers(args, cwd);
  if (offered.length === 1) return offered[0];
  if (!offered.length || !interactive) throw new Error('specify skills or harness');
  const picked = await select({
    message: 'What to install?',
    options: offered.map((i) => ({ value: i.id, label: i.label })),
  });
  return isCancel(picked) ? picked : findInstaller(picked);
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
    const interactive = isInteractive() && !args.yes;
    const installer = await pickInstaller(args, interactive);
    if (isCancel(installer)) {
      log('cancelled');
      return 0;
    }
    if (args.list) {
      const list = installer ? [installer] : offeredInstallers(args);
      list.forEach((item, i) => {
        if (i) log();
        printList(item);
      });
      return 0;
    }
    if (args.status) {
      const list = installer ? [installer] : offeredInstallers(args);
      list.forEach((item, i) => printStatus(item, args, { footer: i === list.length - 1 }));
      if (!list.length) printStatusFooter();
      return 0;
    }
    if (args.uninstall) return await runUninstall(installer, args);
    return await runInstall(installer, args);
  } catch (err) {
    fail(err.message);
    return 1;
  }
}
