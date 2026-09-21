import { copyFileSync, lstatSync, mkdirSync, readdirSync, readFileSync, readlinkSync, renameSync, rmSync, statSync, symlinkSync } from 'node:fs';
import path from 'node:path';

const RETRY_CODES = ['EPERM', 'EBUSY'];

const sleep = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const toRegExp = (pattern) => new RegExp(`^${pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replaceAll('*', '.*')}$`);
const lstat = (p) => lstatSync(p, { throwIfNoEntry: false });

export const unitExclude = (unit) => [...(unit.exclude ?? []), '.DS_Store'];

function listNames(dir, exclude) {
  const patterns = exclude.map(toRegExp);
  return readdirSync(dir).filter((name) => !patterns.some((re) => re.test(name))).sort();
}

function copyInto(src, dest, exclude = []) {
  if (statSync(src).isDirectory()) copyDir(src, dest, exclude);
  else {
    mkdirSync(path.dirname(dest), { recursive: true });
    copyFileSync(src, dest);
  }
}

function sameFile(a, b) {
  const sa = statSync(a, { throwIfNoEntry: false });
  const sb = statSync(b, { throwIfNoEntry: false });
  if (!sa || !sb || sa.isDirectory() || sb.isDirectory()) return false;
  return sa.size === sb.size && readFileSync(a).equals(readFileSync(b));
}

export function sameAs(src, dest, exclude = [], opts = {}) {
  const srcStat = statSync(src, { throwIfNoEntry: false });
  const destStat = lstat(dest);
  if (!srcStat || !destStat || destStat.isSymbolicLink()) return false;
  if (srcStat.isDirectory()) return destStat.isDirectory() && sameDir(src, dest, exclude, opts);
  return !destStat.isDirectory() && sameFile(src, dest);
}

// Catalog symlinks are followed: the copy holds their content.
export function copyDir(src, dest, exclude = []) {
  mkdirSync(dest, { recursive: true });
  for (const name of listNames(src, exclude)) {
    const from = path.join(src, name);
    const to = path.join(dest, name);
    if (statSync(from).isDirectory()) copyDir(from, to, exclude);
    else copyFileSync(from, to);
  }
}

export function sameDir(a, b, exclude = [], opts = {}) {
  const allowDest = opts.allowDest ?? [];
  const statA = statSync(a, { throwIfNoEntry: false });
  const statB = statSync(b, { throwIfNoEntry: false });
  if (!statA?.isDirectory() || !statB?.isDirectory()) return false;
  const names = listNames(a, exclude);
  const destNames = listNames(b, exclude).filter((name) => !allowDest.includes(name));
  if (names.join('\0') !== destNames.join('\0')) return false;
  return names.every((name) => {
    const from = path.join(a, name);
    const to = path.join(b, name);
    const [sa, sb] = [statSync(from), statSync(to, { throwIfNoEntry: false })];
    if (!sb) return false;
    if (sa.isDirectory() || sb.isDirectory()) return sa.isDirectory() && sb.isDirectory() && sameDir(from, to, exclude);
    return sa.size === sb.size && readFileSync(from).equals(readFileSync(to));
  });
}

export function remove(p) {
  rmSync(p, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}

export function move(from, to) {
  mkdirSync(path.dirname(to), { recursive: true });
  for (let attempt = 0; ; attempt++) {
    try {
      return renameSync(from, to);
    } catch (err) {
      if (err.code === 'EXDEV') break;
      if (!RETRY_CODES.includes(err.code) || attempt >= 5) throw err;
      sleep(200);
    }
  }
  const stat = lstat(from);
  if (stat.isSymbolicLink()) symlinkSync(readlinkSync(from), to);
  else if (stat.isDirectory()) copyDir(from, to);
  else copyFileSync(from, to);
  remove(from);
}

function restoreSync(dest, backup, preserve) {
  const saved = lstat(backup);
  if (!saved) return;
  if (saved.isSymbolicLink() || !saved.isDirectory()) {
    remove(dest);
    move(backup, dest);
    return;
  }
  for (const name of readdirSync(backup)) {
    if (preserve.includes(name)) continue;
    const to = path.join(dest, name);
    remove(to);
    move(path.join(backup, name), to);
  }
}

function installReplace(unit, backup) {
  const exclude = unitExclude(unit);
  const tmp = path.join(path.dirname(unit.dest), `.${path.basename(unit.dest)}.ai-tools-tmp`);
  remove(tmp);
  copyInto(unit.src, tmp, exclude);
  const replaced = Boolean(lstat(unit.dest));
  if (replaced) {
    try {
      remove(backup);
      move(unit.dest, backup);
    } catch (err) {
      remove(tmp);
      throw err;
    }
  }
  try {
    move(tmp, unit.dest);
    if (!sameAs(unit.src, unit.dest, exclude)) throw new Error(`copy differs from catalog: ${unit.dest}`);
  } catch (err) {
    remove(tmp);
    remove(unit.dest);
    if (replaced) {
      try {
        move(backup, unit.dest);
      } catch {
        err.message += ` (previous copy kept in ${backup})`;
      }
    }
    throw err;
  }
  return replaced;
}

function installSyncDir(unit, backup) {
  const exclude = unitExclude(unit);
  const preserve = unit.preserve ?? [];
  const destStat = lstat(unit.dest);
  if (!destStat) return installReplace({ ...unit, kind: 'dir' }, backup);

  try {
    if (destStat.isSymbolicLink()) {
      remove(backup);
      move(unit.dest, backup);
      copyDir(unit.src, unit.dest, exclude);
    } else if (!destStat.isDirectory()) {
      return installReplace({ ...unit, kind: 'dir' }, backup);
    } else {
      const catalogNames = listNames(unit.src, exclude);
      const destNames = listNames(unit.dest, exclude);
      for (const name of destNames) {
        if (preserve.includes(name) || catalogNames.includes(name)) continue;
        remove(path.join(backup, name));
        move(path.join(unit.dest, name), path.join(backup, name));
      }
      for (const name of catalogNames) {
        if (preserve.includes(name)) continue;
        installReplace({
          item: unit.item,
          kind: 'dir',
          src: path.join(unit.src, name),
          dest: path.join(unit.dest, name),
          exclude: unit.exclude,
        }, path.join(backup, name));
      }
    }
    if (!sameDir(unit.src, unit.dest, exclude, { allowDest: preserve })) {
      throw new Error(`copy differs from catalog: ${unit.dest}`);
    }
  } catch (err) {
    restoreSync(unit.dest, backup, preserve);
    throw err;
  }
  return true;
}

// Returns whether an existing destination was moved to `backup`.
export function installUnit(unit, backup) {
  if (unit.kind === 'sync-dir') return installSyncDir(unit, backup);
  return installReplace(unit, backup);
}
