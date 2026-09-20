import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { copyDir, installUnit, sameDir, unitExclude } from '../core/fsops.js';
import { tempDir, writeTree } from './helpers.js';

const EXCLUDE = unitExclude({ exclude: ['evals', '*-workspace', 'README.md'] });

test('copy skips excluded names', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), {
    'SKILL.md': 'a', 'refs/x.md': 'b', 'README.md': 'c', '.DS_Store': 'd', 'evals/e.json': 'e', 'x-workspace/f': 'f',
  });
  copyDir(src, path.join(root, 'dest'), EXCLUDE);
  assert.ok(existsSync(path.join(root, 'dest/refs/x.md')));
  for (const name of ['README.md', '.DS_Store', 'evals', 'x-workspace']) assert.ok(!existsSync(path.join(root, 'dest', name)));
});

test('compare detects equal, changed and extra files', () => {
  const root = tempDir();
  const a = writeTree(path.join(root, 'a'), { 'SKILL.md': 'a', 'refs/x.md': 'b', 'evals/e': '1' });
  const b = writeTree(path.join(root, 'b'), { 'SKILL.md': 'a', 'refs/x.md': 'b', 'evals/e': '2' });
  assert.ok(sameDir(a, b, EXCLUDE));
  writeFileSync(path.join(b, 'refs/x.md'), 'B');
  assert.ok(!sameDir(a, b, EXCLUDE));
  writeFileSync(path.join(b, 'refs/x.md'), 'b');
  writeFileSync(path.join(b, 'extra.md'), '');
  assert.ok(!sameDir(a, b, EXCLUDE));
});

test('replacing keeps a backup and leaves the destination equal to the source', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), { 'SKILL.md': 'new' });
  const dest = writeTree(path.join(root, 'project/.claude/skills/s'), { 'SKILL.md': 'old' });
  const backup = path.join(root, 'backup/.claude/skills/s');
  assert.equal(installUnit({ item: 's', kind: 'dir', src, dest }, backup), true);
  assert.ok(sameDir(src, dest));
  assert.equal(readFileSync(path.join(backup, 'SKILL.md'), 'utf8'), 'old');
});
