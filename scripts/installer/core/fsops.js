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

export function sameDir(a, b, exclude = []) {
  const statA = statSync(a, { throwIfNoEntry: false });
  const statB = statSync(b, { throwIfNoEntry: false });
  if (!statA?.isDirectory() || !statB?.isDirectory()) return false;
  const names = listNames(a, exclude);
  if (names.join('\0') !== listNames(b, exclude).join('\0')) return false;
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

// Returns whether an existing destination was moved to `backup`.
export function installUnit(unit, backup) {
  const exclude = unitExclude(unit);
  const tmp = path.join(path.dirname(unit.dest), `.${path.basename(unit.dest)}.ai-tools-tmp`);
  remove(tmp);
  copyDir(unit.src, tmp, exclude);
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
    if (!sameDir(unit.src, unit.dest, exclude)) throw new Error(`copy differs from catalog: ${unit.dest}`);
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
