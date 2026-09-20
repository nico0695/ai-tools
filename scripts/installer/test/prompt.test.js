import assert from 'node:assert/strict';
import { test } from 'node:test';
import { initialState, reduce } from '../ui/prompt.js';

const OPTIONS = [
  { value: 'a', label: 'a' },
  { value: 'b', label: 'b' },
  { value: 'exp', label: 'experimental', header: true },
  { value: 'c', label: 'c' },
];
const press = (state, ...keys) => keys.reduce(reduce, state);

test('defaults are preselected and the cursor skips headers', () => {
  const state = initialState(OPTIONS, { multiple: true, initial: ['c', 'a'] });
  assert.deepEqual(state.selected, ['a', 'c']);
  assert.equal(press(state, 'down', 'down').cursor, 3);
  assert.equal(press(state, 'up').cursor, 3);
});

test('space toggles and a selects all or none', () => {
  const state = initialState(OPTIONS, { multiple: true });
  assert.deepEqual(press(state, 'down', 'space').selected, ['b']);
  assert.deepEqual(press(state, 'a').selected, ['a', 'b', 'c']);
  assert.deepEqual(press(state, 'a', 'a').selected, []);
});

test('select starts on the initial value; enter and esc finish', () => {
  const state = initialState(OPTIONS, { initial: ['b'] });
  assert.equal(state.cursor, 1);
  assert.equal(press(state, 'return').status, 'done');
  assert.equal(press(state, 'escape').status, 'cancelled');
});
