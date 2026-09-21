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

test('existing update never reports unmanaged', () => {
  const root = tempDir();
  const base = path.join(root, 'project');
  const src = writeTree(path.join(root, 'src'), { 'README.md': 'v2', 'skills/s/SKILL.md': 's' });
  const dest = path.join(base, 'sdd-lite');
  writeTree(dest, {
    'README.md': 'v1',
    'skills/s/SKILL.md': 's',
    'openspec/changes/x/state.yaml': 'st',
    'project-context.md': 'ctx',
  });
  const manifest = { version: 1, scope: 'project', base, entries: [] };
  const unit = {
    item: 'sdd-lite',
    kind: 'sync-dir',
    src,
    dest,
    preserve: ['project-context.md', 'skill-catalog.md', 'openspec'],
  };
  assert.equal(unitState(unit, manifest, base, 'update'), 'update');
  writeTree(dest, { 'README.md': 'v2' });
  assert.equal(unitState(unit, manifest, base, 'update'), 'up to date');
  symlinkSync(src, path.join(base, 'link'));
  assert.equal(unitState({ ...unit, dest: path.join(base, 'link') }, manifest, base, 'update'), 'update');
  assert.equal(unitState({ ...unit, dest: path.join(base, 'missing') }, manifest, base, 'update'), 'new');
});
