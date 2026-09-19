import assert from 'node:assert/strict';
import { symlinkSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { setEntry } from '../core/manifest.js';
import { unitState } from '../core/plan.js';
import { tempDir, writeTree } from './helpers.js';

test('unit states', () => {
  const root = tempDir();
  const base = path.join(root, 'project');
  const src = writeTree(path.join(root, 'src'), { 'SKILL.md': 'v1' });
  const manifest = { version: 1, scope: 'project', base, entries: [] };
  const unit = (name) => ({ item: name, kind: 'dir', src, dest: path.join(base, '.claude/skills', name) });
  const register = (name) => setEntry(manifest, { installer: 'skills', item: name, kind: 'dir', path: `.claude/skills/${name}` });

  writeTree(base, { '.claude/skills/same/SKILL.md': 'v1', '.claude/skills/changed/SKILL.md': 'v0', '.claude/skills/foreign/SKILL.md': 'x' });
  symlinkSync(src, path.join(base, '.claude/skills/link'));
  ['changed', 'gone', 'link'].forEach(register);

  assert.equal(unitState(unit('fresh'), manifest, base), 'new');
  assert.equal(unitState(unit('same'), manifest, base), 'up to date');
  assert.equal(unitState(unit('changed'), manifest, base), 'update');
  assert.equal(unitState(unit('foreign'), manifest, base), 'unmanaged');
  assert.equal(unitState(unit('link'), manifest, base), 'unmanaged');
  assert.equal(unitState(unit('gone'), manifest, base), 'missing');
});
