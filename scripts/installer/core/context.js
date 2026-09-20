import { createHash } from 'node:crypto';
import { existsSync, realpathSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { providerDir } from './providers.js';

const isWindows = process.platform === 'win32';

export const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');

export const dataHome = () => process.env.AI_TOOLS_HOME || path.join(os.homedir(), '.config', 'ai-tools');
export const targetDir = (id, home = dataHome()) => path.join(home, 'targets', id);
export const samePath = (a, b) => (isWindows ? a.toLowerCase() === b.toLowerCase() : a === b);

export function canonical(p) {
  try {
    return realpathSync.native(path.resolve(p));
  } catch {
    throw new Error(`path not found: ${p}`);
  }
}

export function projectRoot(cwd) {
  const start = canonical(cwd);
  for (let dir = start; ; dir = path.dirname(dir)) {
    if (existsSync(path.join(dir, '.git'))) return dir;
    if (path.dirname(dir) === dir) return start;
  }
}

export function resolveBase(scope, project, cwd = process.cwd()) {
  if (scope === 'user') return canonical(os.homedir());
  return project ? canonical(project) : projectRoot(cwd);
}

export function targetId(scope, base) {
  if (scope === 'user') return 'user';
  const hash = createHash('sha1').update(isWindows ? base.toLowerCase() : base).digest('hex').slice(0, 8);
  return `${path.basename(base).replace(/[^A-Za-z0-9._-]/g, '-')}-${hash}`;
}

export function createContext({ scope, base, repo, providers }) {
  return { scope, base, repo, providers, providerDir: (id) => providerDir(id, scope, base) };
}
