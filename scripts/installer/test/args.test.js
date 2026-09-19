import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseCli } from '../main.js';

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
