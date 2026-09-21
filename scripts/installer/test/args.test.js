import assert from 'node:assert/strict';
import { test } from 'node:test';
import { REPO } from '../core/context.js';
import { offeredInstallers, parseCli, pickInstaller } from '../main.js';
import { tempDir } from './helpers.js';

test('lists accept commas and repeated flags', () => {
  const args = parseCli(['--skills', 'a,b', '--skills', 'c', '--providers=claude, agents']);
  assert.deepEqual(args.skills, ['a', 'b', 'c']);
  assert.deepEqual(args.providers, ['claude', 'agents']);
});

test('--user and --project cannot be combined', () => {
  assert.throws(() => parseCli(['--user', '--project', '.']), /cannot be combined/);
});

test('unknown flags are rejected', () => {
  assert.throws(() => parseCli(['--link']), { code: 'ERR_PARSE_ARGS_UNKNOWN_OPTION' });
});

test('positional harness is parsed', () => {
  assert.equal(parseCli(['harness', '--project', '/tmp']).installer, 'harness');
});

test('omitted installer with --all is skills', async () => {
  const installer = await pickInstaller(parseCli(['--all']), false);
  assert.equal(installer.id, 'skills');
});

test('skill flags cannot be used with harness', async () => {
  await assert.rejects(() => pickInstaller(parseCli(['harness', '--all']), false), /--all cannot be used with harness/);
  await assert.rejects(() => pickInstaller(parseCli(['harness', '--skills', 'x']), false), /--skills cannot be used with harness/);
});

test('non-interactive install needs an installer name when harness is offered', async () => {
  await assert.rejects(() => pickInstaller(parseCli([]), false, tempDir()), /specify skills or harness/);
});

test('omitted installer in this repo is skills', async () => {
  const installer = await pickInstaller(parseCli([]), false, REPO);
  assert.equal(installer.id, 'skills');
});

test('harness is hidden when the destination is this repo', () => {
  assert.deepEqual(offeredInstallers(parseCli([]), REPO).map((i) => i.id), ['skills']);
});

test('uninstall without an installer name is skills', async () => {
  const installer = await pickInstaller(parseCli(['--uninstall']), false);
  assert.equal(installer.id, 'skills');
});
