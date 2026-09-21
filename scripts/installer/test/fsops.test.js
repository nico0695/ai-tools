import assert from 'node:assert/strict';
import { existsSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
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

const PRESERVE = ['project-context.md', 'skill-catalog.md', 'openspec'];
const syncUnit = (src, dest) => ({
  item: 'sdd-lite', kind: 'sync-dir', src, dest, preserve: PRESERVE,
});

test('sameDir allowDest ignores preserved names only at the root', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), { 'README.md': 'a', 'skills/s/SKILL.md': 's' });
  const dest = writeTree(path.join(root, 'dest'), {
    'README.md': 'a',
    'skills/s/SKILL.md': 's',
    'project-context.md': 'ctx',
    'skill-catalog.md': 'cat',
    'openspec/changes/x/state.yaml': 'st',
  });
  assert.ok(sameDir(src, dest, [], { allowDest: PRESERVE }));
  writeFileSync(path.join(dest, 'README.md'), 'b');
  assert.ok(!sameDir(src, dest, [], { allowDest: PRESERVE }));
});

test('sync-dir updates package files, preserves runtime, deletes orphans', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), {
    'README.md': 'new',
    'templates/delivery/commit.md': 'pkg',
    'skills/sddl-init/SKILL.md': 'init',
  });
  const dest = writeTree(path.join(root, 'dest'), {
    'README.md': 'old',
    'NOTES.md': 'keep-me-not',
    'templates/delivery/commit.md': 'custom',
    'skills/old-skill/SKILL.md': 'gone',
    'skills/sddl-init/SKILL.md': 'old-init',
    'project-context.md': 'ctx',
    'skill-catalog.md': 'cat',
    'openspec/changes/x/state.yaml': 'st',
  });
  const backup = path.join(root, 'backup/sdd-lite');
  assert.equal(installUnit(syncUnit(src, dest), backup), true);
  assert.equal(readFileSync(path.join(dest, 'README.md'), 'utf8'), 'new');
  assert.equal(readFileSync(path.join(dest, 'templates/delivery/commit.md'), 'utf8'), 'pkg');
  assert.equal(readFileSync(path.join(dest, 'skills/sddl-init/SKILL.md'), 'utf8'), 'init');
  assert.equal(readFileSync(path.join(dest, 'project-context.md'), 'utf8'), 'ctx');
  assert.equal(readFileSync(path.join(dest, 'openspec/changes/x/state.yaml'), 'utf8'), 'st');
  assert.ok(!existsSync(path.join(dest, 'NOTES.md')));
  assert.ok(!existsSync(path.join(dest, 'skills/old-skill')));
  assert.ok(sameDir(src, dest, [], { allowDest: PRESERVE }));
});

test('sync-dir replaces a symlink destination without following it', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), { 'README.md': 'new' });
  const real = writeTree(path.join(root, 'real'), {
    'README.md': 'old',
    'openspec/changes/x/state.yaml': 'st',
  });
  const dest = path.join(root, 'dest');
  symlinkSync(real, dest);
  installUnit(syncUnit(src, dest), path.join(root, 'backup/sdd-lite'));
  assert.equal(readFileSync(path.join(dest, 'README.md'), 'utf8'), 'new');
  assert.ok(!existsSync(path.join(dest, 'openspec')));
  assert.equal(readFileSync(path.join(real, 'openspec/changes/x/state.yaml'), 'utf8'), 'st');
});

test('installUnit replaces a single file', () => {
  const root = tempDir();
  const src = writeTree(path.join(root, 'src'), { 'README.md': 'new' });
  const dest = writeTree(path.join(root, 'dest'), { 'README.md': 'old' });
  const from = path.join(src, 'README.md');
  const to = path.join(dest, 'README.md');
  const backup = path.join(root, 'backup/README.md');
  assert.equal(installUnit({ item: 'sdd-lite', kind: 'dir', src: from, dest: to }, backup), true);
  assert.equal(readFileSync(to, 'utf8'), 'new');
  assert.equal(readFileSync(backup, 'utf8'), 'old');
});
