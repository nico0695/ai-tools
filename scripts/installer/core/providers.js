import { statSync } from 'node:fs';
import path from 'node:path';

export const PROVIDERS = [
  { id: 'claude', user: '.claude', project: '.claude' },
  { id: 'agents', user: '.agents', project: '.agents' },
  { id: 'cursor', user: '.cursor', project: '.cursor' },
  { id: 'continue', user: '.continue', project: '.continue' },
  { id: 'opencode', user: '.config/opencode', project: '.opencode' },
];

const ALWAYS_OFFERED = ['claude', 'agents'];

export function providerDir(id, scope, base) {
  const provider = PROVIDERS.find((p) => p.id === id);
  if (!provider) throw new Error(`unknown provider: ${id} (options: ${PROVIDERS.map((p) => p.id).join(', ')})`);
  return path.join(base, provider[scope]);
}

export const isDetected = (id, scope, base) => Boolean(statSync(providerDir(id, scope, base), { throwIfNoEntry: false })?.isDirectory());

export const offeredProviders = (scope, base) =>
  PROVIDERS.map((p) => p.id).filter((id) => ALWAYS_OFFERED.includes(id) || isDetected(id, scope, base));

export const defaultProviders = (scope, base) => (isDetected('agents', scope, base) ? ['claude', 'agents'] : ['claude']);
