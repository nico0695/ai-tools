import assert from 'node:assert/strict';
import { existsSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { targetId } from '../core/context.js';
import { loadManifest, saveManifest, setEntry } from '../core/manifest.js';
import { tempDir } from './helpers.js';

const META = { scope: 'project', base: '/work/app' };

test('save and load round trip', () => {
  const dir = path.join(tempDir(), 'targets/app');
  const manifest = loadManifest(dir, META);
  setEntry(manifest, { installer: 'skills', item: 's', provider: 'claude', kind: 'dir', path: '.claude/skills/s' });
  saveManifest(dir, manifest);
  assert.deepEqual(loadManifest(dir, META), manifest);
});

test('a broken manifest is moved aside and loads empty', (t) => {
  t.mock.method(process.stderr, 'write', () => true);
  const dir = tempDir();
  writeFileSync(path.join(dir, 'manifest.json'), '{ nope');
  assert.deepEqual(loadManifest(dir, META).entries, []);
  assert.ok(existsSync(path.join(dir, 'manifest.json.broken')));
  assert.ok(!existsSync(path.join(dir, 'manifest.json')));
});

test('target id is folder name plus path hash', () => {
  assert.match(targetId('project', '/work/my app'), /^my-app-[0-9a-f]{8}$/);
  assert.notEqual(targetId('project', '/a/app'), targetId('project', '/b/app'));
  assert.equal(targetId('user', '/home/me'), 'user');
});
