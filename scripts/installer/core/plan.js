import { lstatSync } from 'node:fs';
import { sameDir, unitExclude } from './fsops.js';
import { findEntry, relPath } from './manifest.js';

export const MARKS = { 'new': ' ', 'up to date': '=', 'update': '*', 'unmanaged': '~', 'missing': '!' };

export function unitState(unit, manifest, base) {
  const registered = Boolean(findEntry(manifest, relPath(base, unit.dest)));
  const stat = lstatSync(unit.dest, { throwIfNoEntry: false });
  if (!stat) return registered ? 'missing' : 'new';
  if (stat.isSymbolicLink()) return 'unmanaged';
  if (sameDir(unit.src, unit.dest, unitExclude(unit))) return 'up to date';
  return registered ? 'update' : 'unmanaged';
}

export const buildPlan = (units, manifest, base) => units.map((unit) => ({ ...unit, state: unitState(unit, manifest, base) }));
