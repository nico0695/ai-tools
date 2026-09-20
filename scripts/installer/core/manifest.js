import { mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { warn } from '../ui/output.js';
import { samePath } from './context.js';

const FILE = 'manifest.json';

export const relPath = (base, p) => path.relative(base, p).split(path.sep).join('/');

// `readOnly` keeps a broken file in place (--status writes nothing).
export function loadManifest(dir, { scope, base }, { readOnly = false } = {}) {
  const file = path.join(dir, FILE);
  const empty = { version: 1, scope, base, entries: [] };
  try {
    const data = JSON.parse(readFileSync(file, 'utf8'));
    if (data.version === 1 && Array.isArray(data.entries)) return data;
  } catch (err) {
    if (err.code === 'ENOENT') return empty;
  }
  if (readOnly) {
    warn(`unreadable manifest ignored: ${file}`);
  } else {
    renameSync(file, `${file}.broken`);
    warn(`unreadable manifest moved to ${file}.broken`);
  }
  return empty;
}

export function saveManifest(dir, manifest) {
  const file = path.join(dir, FILE);
  const text = `${JSON.stringify(manifest, null, 2)}\n`;
  let current = null;
  try {
    current = readFileSync(file, 'utf8');
  } catch {}
  if (current === text || (current === null && !manifest.entries.length)) return;
  mkdirSync(dir, { recursive: true });
  writeFileSync(`${file}.tmp`, text);
  renameSync(`${file}.tmp`, file);
}

export const findEntry = (manifest, rel) => manifest.entries.find((e) => samePath(e.path, rel));

export function setEntry(manifest, entry) {
  removeEntry(manifest, entry.path);
  manifest.entries.push(entry);
}

export function removeEntry(manifest, rel) {
  manifest.entries = manifest.entries.filter((e) => !samePath(e.path, rel));
}

export function listTargets(home) {
  let ids;
  try {
    ids = readdirSync(path.join(home, 'targets'));
  } catch {
    return [];
  }
  return ids.map((id) => {
    try {
      return { id, base: JSON.parse(readFileSync(path.join(home, 'targets', id, FILE), 'utf8')).base };
    } catch {
      return { id };
    }
  });
}
