import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { REPO } from '../core/context.js';

const ROOT = path.join(REPO, 'skills');
const EXCLUDE = ['evals', '*-workspace', 'README.md', 'USAGE.md'];

let catalog;

function listTier(tier) {
  const dir = path.join(ROOT, tier);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((name) => !/^[_.]|-workspace$/.test(name) && existsSync(path.join(dir, name, 'SKILL.md')))
    .sort()
    .map((name) => ({ id: name, group: tier, src: path.join(dir, name) }));
}

function description(skillMd) {
  const lines = readFileSync(skillMd, 'utf8').split(/\r?\n/);
  if (lines[0].trim() !== '---') return '';
  const end = lines.indexOf('---', 1);
  const i = lines.slice(0, end).findIndex((l) => l.startsWith('description:'));
  if (i < 0) return '';
  const value = lines[i].slice('description:'.length).trim().replace(/^[|>]-?$/, '').replace(/^["']|["']$/g, '');
  return value || (lines[i + 1] ?? '').trim();
}

function load() {
  if (catalog) return catalog;
  const stable = listTier('stable');
  const taken = new Set(stable.map((s) => s.id));
  const experimental = listTier('experimental').filter((s) => !taken.has(s.id));
  if (!stable.length) throw new Error(`no skills with SKILL.md in ${path.join(ROOT, 'stable')}`);
  catalog = [...stable, ...experimental].map((s) => ({ ...s, description: description(path.join(s.src, 'SKILL.md')) }));
  return catalog;
}

/** @type {import('../types.js').Installer} */
export default {
  id: 'skills',
  label: 'Skills',
  scopes: ['project', 'user'],
  providers: ['claude', 'agents', 'cursor', 'continue', 'opencode'],
  groups: [
    { id: 'stable', default: true },
    { id: 'experimental', note: 'experimental: in development, not validated' },
  ],
  items: () => load().map(({ id, description, group }) => ({ id, description, group })),
  units: (item, ctx) => {
    const { src } = load().find((s) => s.id === item.id);
    return ctx.providers.map((provider) => ({
      item: item.id,
      provider,
      kind: 'dir',
      src,
      dest: path.join(ctx.providerDir(provider), 'skills', item.id),
      exclude: EXCLUDE,
    }));
  },
};
