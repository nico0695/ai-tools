import { lstatSync } from 'node:fs';
import { sameAs, unitExclude } from './fsops.js';
import { findEntry, relPath } from './manifest.js';

export const MARKS = { 'new': ' ', 'up to date': '=', 'update': '*', 'unmanaged': '~', 'missing': '!' };

export function unitState(unit, manifest, base, existing = 'unmanaged') {
  const registered = Boolean(findEntry(manifest, relPath(base, unit.dest)));
  const stat = lstatSync(unit.dest, { throwIfNoEntry: false });
  if (!stat) return registered ? 'missing' : 'new';
  if (existing === 'unmanaged' && stat.isSymbolicLink()) return 'unmanaged';
  const opts = unit.kind === 'sync-dir' ? { allowDest: unit.preserve ?? [] } : {};
  if (sameAs(unit.src, unit.dest, unitExclude(unit), opts)) return 'up to date';
  return existing === 'update' || registered ? 'update' : 'unmanaged';
}

export const buildPlan = (units, manifest, base, existing = 'unmanaged') =>
  units.map((unit) => ({ ...unit, state: unitState(unit, manifest, base, existing) }));
