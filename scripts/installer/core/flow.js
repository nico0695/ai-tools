import { existsSync, lstatSync } from 'node:fs';
import path from 'node:path';
import { bold, dim, fit, log, ok, tilde, warn } from '../ui/output.js';
import { confirm, isCancel, isInteractive, multiselect, select } from '../ui/prompt.js';
import { createContext, dataHome, projectRoot, REPO, resolveBase, samePath, targetDir, targetId } from './context.js';
import { installUnit, remove } from './fsops.js';
import { listTargets, loadManifest, relPath, removeEntry, saveManifest, setEntry } from './manifest.js';
import { MARKS, buildPlan, unitState } from './plan.js';
import { defaultProviders, offeredProviders } from './providers.js';

const STATE_ORDER = ['up to date', 'update', 'unmanaged', 'missing', 'new'];
const MARK_PRIORITY = ['unmanaged', 'update', 'missing', 'up to date'];
const LEGEND = '  = up to date · * update available · ~ unmanaged (not installed by this tool) · ! missing on disk';
const HINTS = 'See --status · remove with --uninstall';

const cols = () => process.stdout.columns || 100;
const defaultGroups = (installer) => new Set((installer.groups ?? []).filter((g) => g.default).map((g) => g.id));
const tag = (installer, item) => (!item.group || defaultGroups(installer).has(item.group) ? '' : item.group.slice(0, 3));

function orderedItems(installer) {
  const items = installer.items();
  const groups = installer.groups ?? [];
  return [...items.filter((i) => !groups.some((g) => g.id === i.group)), ...groups.flatMap((g) => items.filter((i) => i.group === g.id))];
}

function groupStates(states) {
  return STATE_ORDER.map((state) => {
    const providers = states.filter((s) => s.state === state).map((s) => s.provider);
    return providers.length ? `${state}: ${providers.join(', ')}` : '';
  }).filter(Boolean).join(' · ');
}

function openTarget(scope, base, { readOnly = false } = {}) {
  const dir = targetDir(targetId(scope, base));
  return { dir, manifest: loadManifest(dir, { scope, base }, { readOnly }) };
}

function presence(installer, item, scope, base, manifest) {
  const ctx = createContext({ scope, base, repo: REPO, providers: installer.providers });
  return installer.units(item, ctx)
    .map((unit) => ({ provider: unit.provider, state: unitState(unit, manifest, base) }))
    .filter((p) => p.state !== 'new');
}

async function chooseScope(installer, args, interactive) {
  const flag = args.user ? 'user' : args.project !== undefined ? 'project' : undefined;
  if (flag && !installer.scopes.includes(flag)) throw new Error(`${installer.id} cannot be installed with --${flag}`);
  if (flag) return flag;
  if (installer.scopes.length === 1) return installer.scopes[0];
  if (!interactive) throw new Error('use --user or --project PATH');
  const project = projectRoot(process.cwd());
  const isSelf = samePath(project, REPO);
  return select({
    message: 'Where to install?',
    options: [
      { value: 'project', label: 'project', hint: `${tilde(project)}${isSelf ? '  (this is the ai-tools repo)' : ''}` },
      { value: 'user', label: 'user', hint: `${tilde(resolveBase('user'))} (all your projects)` },
    ],
    initialValue: isSelf ? 'user' : 'project',
  });
}

async function chooseItems(installer, args, interactive, scope, base, manifest) {
  const items = orderedItems(installer);
  if (args.skills) {
    const unknown = args.skills.find((id) => !items.some((i) => i.id === id));
    if (unknown) throw new Error(`unknown item: ${unknown} (try --list)`);
    return items.filter((i) => args.skills.includes(i.id));
  }
  if (args.all) return items.filter((i) => args.experimental || !tag(installer, i));
  if (!interactive) throw new Error('use --skills or --all');
  const options = [];
  let marked = false;
  for (const item of items) {
    const group = installer.groups?.find((g) => g.id === item.group);
    if (group && !group.default && !options.some((o) => o.value === group.id)) {
      options.push({ value: group.id, label: group.note ?? group.id, header: true });
    }
    const states = presence(installer, item, scope, base, manifest);
    const worst = MARK_PRIORITY.find((s) => states.some((p) => p.state === s));
    marked ||= Boolean(worst);
    const providers = states.length ? `[${states.map((s) => s.provider).join(',')}] ` : '';
    options.push({ value: item.id, label: item.id, mark: worst && MARKS[worst], hint: providers + item.description });
  }
  const picked = await multiselect({
    message: `${installer.label} to install in ${tilde(base)}`,
    options,
    initialValues: items.filter((i) => !tag(installer, i)).map((i) => i.id),
    footer: marked ? LEGEND : undefined,
  });
  return isCancel(picked) ? picked : items.filter((i) => picked.includes(i.id));
}

async function chooseProviders(installer, args, interactive, scope, base) {
  const defaults = defaultProviders(scope, base).filter((id) => installer.providers.includes(id));
  if (args.providers) {
    const unknown = args.providers.find((id) => !installer.providers.includes(id));
    if (unknown) throw new Error(`unknown provider: ${unknown} (options: ${installer.providers.join(', ')})`);
    return [...new Set(args.providers)];
  }
  if (!interactive) return defaults;
  const ctx = createContext({ scope, base, repo: REPO, providers: [] });
  const offered = offeredProviders(scope, base).filter((id) => installer.providers.includes(id));
  return multiselect({
    message: 'For which agents?',
    options: offered.map((id) => {
      const detected = existsSync(ctx.providerDir(id));
      return { value: id, label: id, hint: `${tilde(ctx.providerDir(id))}${detected ? '  (detected)' : ''}` };
    }),
    initialValues: defaults,
  });
}

function printPlan(installer, plan, items, base, scope, providers) {
  log();
  log(`${bold('Plan')}  ${tilde(base)} (${scope}) · ${providers.join(', ')}`);
  for (const item of items) {
    const states = plan.filter((u) => u.item === item.id).map((u) => ({ provider: u.provider, state: u.state }));
    const line = states.every((s) => s.state === states[0].state) ? states[0].state : groupStates(states);
    log(`  ${item.id.padEnd(26)} ${tag(installer, item).padEnd(4)} ${line}`);
  }
  if (plan.some((u) => u.state === 'unmanaged')) log(dim('  unmanaged = exists with that name but was not installed by this tool'));
  log();
}

// Returns true to proceed, 'overwrite' to also replace unmanaged copies, false to stop.
async function approve(args, plan) {
  const hasUnmanaged = plan.some((u) => u.state === 'unmanaged');
  if (args.yes) return args.force ? 'overwrite' : true;
  if (!isInteractive()) throw new Error('add -y to confirm');
  if (hasUnmanaged && !args.force) {
    const answer = await select({
      message: 'Proceed?',
      options: [
        { value: true, label: 'Yes, skip unmanaged' },
        { value: 'overwrite', label: 'Overwrite (backup kept)' },
        { value: false, label: 'Cancel' },
      ],
      initialValue: true,
    });
    return isCancel(answer) ? false : answer;
  }
  const answer = await confirm({ message: 'Proceed?' });
  return isCancel(answer) || !answer ? false : args.force ? 'overwrite' : true;
}

const entryOf = (installer, unit, base) => ({
  installer: installer.id, item: unit.item, provider: unit.provider, kind: unit.kind, path: relPath(base, unit.dest),
});

export async function runInstall(installer, args) {
  const interactive = isInteractive() && !args.yes;
  const scope = await chooseScope(installer, args, interactive);
  if (isCancel(scope)) return cancelled();
  const base = resolveBase(scope, args.project);
  const { dir, manifest } = openTarget(scope, base);

  const items = await chooseItems(installer, args, interactive, scope, base, manifest);
  if (isCancel(items)) return cancelled();
  if (!items.length) return nothing('nothing selected');
  const providers = await chooseProviders(installer, args, interactive, scope, base);
  if (isCancel(providers)) return cancelled();
  if (!providers.length) return nothing('no agent selected');

  const ctx = createContext({ scope, base, repo: REPO, providers });
  const plan = buildPlan(items.flatMap((item) => installer.units(item, ctx)), manifest, base);
  printPlan(installer, plan, items, base, scope, providers);

  if (plan.every((u) => u.state === 'up to date')) {
    plan.forEach((u) => setEntry(manifest, entryOf(installer, u, base)));
    saveManifest(dir, manifest);
    log('Everything up to date.');
    return 0;
  }
  const decision = await approve(args, plan);
  if (!decision) return cancelled();
  const overwrite = decision === 'overwrite';

  const backupRoot = path.join(dir, 'backup');
  let backupCleared = false;
  let failed = 0;
  const skipped = [];
  const done = new Set();
  for (const unit of plan) {
    if (unit.state === 'up to date') {
      setEntry(manifest, entryOf(installer, unit, base));
      continue;
    }
    if (unit.state === 'unmanaged' && !overwrite) {
      skipped.push(`${unit.item} (${unit.provider})`);
      continue;
    }
    // Only this run's replacements are kept: the previous backup goes once, before the first one.
    if (!backupCleared && (unit.state === 'update' || unit.state === 'unmanaged')) {
      remove(backupRoot);
      backupCleared = true;
    }
    try {
      installUnit(unit, path.join(backupRoot, relPath(base, unit.dest)));
      setEntry(manifest, entryOf(installer, unit, base));
      done.add(unit.item);
      ok(`${unit.item} -> ${tilde(unit.dest)}`);
    } catch (err) {
      failed++;
      warn(`could not install ${unit.item} in ${tilde(unit.dest)}: ${err.message}`);
    }
  }
  saveManifest(dir, manifest);

  const upToDate = items.filter((i) => plan.filter((u) => u.item === i.id).every((u) => u.state === 'up to date')).length;
  log();
  log(`${bold('Done')}  ${done.size} installed or updated${upToDate ? ` · ${upToDate} up to date` : ''}`);
  if (skipped.length) warn(`skipped (unmanaged): ${skipped.join(', ')}  (--force to overwrite)`);
  if (backupCleared && existsSync(backupRoot)) log(dim(`Replaced copies kept in ${tilde(backupRoot)}`));
  log(dim(HINTS));
  return !done.size && (skipped.length || failed) ? 1 : 0;
}

export async function runUninstall(installer, args) {
  const interactive = isInteractive() && !args.yes;
  const scope = await chooseScope(installer, args, interactive);
  if (isCancel(scope)) return cancelled();
  const base = resolveBase(scope, args.project);
  const { dir, manifest } = openTarget(scope, base);
  const targets = manifest.entries.filter((e) => e.installer === installer.id && (!args.skills || args.skills.includes(e.item)));
  if (!targets.length) {
    throw new Error(`nothing installed by this tool in ${tilde(base)}${args.skills ? ` for: ${args.skills.join(', ')}` : ''}`);
  }

  log(bold(`Will remove from ${tilde(base)}`));
  targets.forEach((e) => log(`  ${e.path}`));
  if (!args.yes) {
    if (!isInteractive()) throw new Error('add -y to confirm');
    const answer = await confirm({ message: 'Remove?' });
    if (isCancel(answer) || !answer) return cancelled();
  }
  for (const entry of targets) {
    const abs = path.join(base, entry.path);
    if (lstatSync(abs, { throwIfNoEntry: false })) {
      remove(abs);
      ok(`removed ${tilde(abs)}`);
    } else {
      warn(`not on disk, dropped from the manifest: ${tilde(abs)}`);
    }
    removeEntry(manifest, entry.path);
  }
  saveManifest(dir, manifest);
  log('Done.');
  if (manifest.entries.length) log(dim('Other entries remain registered: see --status'));
  return 0;
}

export function printList(installer) {
  const items = orderedItems(installer);
  const groups = installer.groups ?? [];
  const sections = [
    { title: installer.label, isDefault: true, members: items.filter((i) => !groups.some((g) => g.id === i.group)) },
    ...groups.map((g) => ({
      title: `${installer.label} · ${g.note ?? g.id}`,
      isDefault: g.default,
      members: items.filter((i) => i.group === g.id),
    })),
  ].filter((s) => s.members.length);
  sections.forEach((section, i) => {
    if (i) log();
    log(bold(section.title));
    section.members.forEach((item) => log(fit(`  ${item.id.padEnd(26)} ${item.description}`, cols() - 1)));
    if (!section.isDefault) log(dim('  (install with --skills or with --all --experimental)'));
  });
  return 0;
}

export function printStatus(installer, args) {
  const targets = [
    ['Project', 'project', resolveBase('project', args.project)],
    ['User', 'user', resolveBase('user')],
  ];
  for (const [label, scope, base] of targets) {
    const { manifest } = openTarget(scope, base, { readOnly: true });
    log(`${bold(label)}  ${tilde(base)}`);
    let count = 0;
    for (const item of orderedItems(installer)) {
      const states = presence(installer, item, scope, base, manifest);
      if (!states.length) continue;
      count++;
      log(`  ${item.id.padEnd(26)} ${tag(installer, item).padEnd(4)} ${groupStates(states)}`);
    }
    if (!count) log(dim('  (nothing installed)'));
    log();
  }
  const stale = listTargets(dataHome()).filter((t) => t.base && !existsSync(t.base));
  stale.forEach((t) => warn(`destination no longer exists: ${tilde(t.base)} (data in ${tilde(targetDir(t.id))})`));
  log(dim('unmanaged = exists with that name but was not installed by this tool'));
  log(dim(`Data: ${tilde(dataHome())}`));
  return 0;
}

function cancelled() {
  log('cancelled');
  return 0;
}

function nothing(message) {
  log(message);
  return 0;
}
