import readline from 'node:readline';
import { bold, cyan, dim, fit } from './output.js';

const CANCEL = Symbol('cancel');
const HELP_MULTI = 'up/down move · space toggle · a all · enter confirm · esc cancel';
const HELP_SINGLE = 'up/down move · enter confirm · esc cancel';

export const isCancel = (value) => value === CANCEL;
export const isInteractive = () => Boolean(process.stdin.isTTY && process.stdout.isTTY);

const selectable = (options) => options.flatMap((o, i) => (o.header ? [] : [i]));

export function initialState(options, { multiple = false, initial = [] } = {}) {
  const indexes = selectable(options);
  const cursor = multiple ? indexes[0] : (indexes.find((i) => options[i].value === initial[0]) ?? indexes[0]);
  const selected = multiple ? indexes.map((i) => options[i].value).filter((v) => initial.includes(v)) : [];
  return { options, multiple, cursor, selected, status: 'active' };
}

export function reduce(state, key) {
  const indexes = selectable(state.options);
  const values = indexes.map((i) => state.options[i].value);
  const pos = indexes.indexOf(state.cursor);
  const current = state.options[state.cursor].value;
  switch (key) {
    case 'up':
      return { ...state, cursor: indexes[(pos - 1 + indexes.length) % indexes.length] };
    case 'down':
      return { ...state, cursor: indexes[(pos + 1) % indexes.length] };
    case 'space': {
      if (!state.multiple) return state;
      const on = state.selected.includes(current);
      return { ...state, selected: values.filter((v) => (v === current ? !on : state.selected.includes(v))) };
    }
    case 'a':
      if (!state.multiple) return state;
      return { ...state, selected: state.selected.length === values.length ? [] : values };
    case 'return':
      return { ...state, status: 'done' };
    case 'escape':
      return { ...state, status: 'cancelled' };
    default:
      return state;
  }
}

export function render(state, { message, footer, rows = 24, cols = 80 }) {
  const { options } = state;
  // Keep the whole menu under the terminal height, or redraws land one line off.
  const height = Math.max(3, rows - 5 - (footer ? 1 : 0));
  const start = Math.min(Math.max(0, state.cursor - Math.floor(height / 2)), Math.max(0, options.length - height));
  const width = Math.max(...options.filter((o) => !o.header).map((o) => o.label.length));
  const lines = [`${cyan('?')} ${bold(fit(message, cols - 3))}`];
  options.slice(start, start + height).forEach((option, k) => {
    if (option.header) return lines.push(dim(fit(`  -- ${option.label} --`, cols - 1)));
    const active = start + k === state.cursor;
    const box = state.multiple ? (state.selected.includes(option.value) ? '[x] ' : '[ ] ') : '';
    const prefix = fit(`  ${active ? '>' : ' '} ${box}${option.label.padEnd(width)} ${option.mark ?? ' '} `, cols - 1);
    const hint = fit(option.hint ?? '', cols - 1 - prefix.length);
    lines.push((active ? cyan(prefix) : prefix) + dim(hint));
  });
  if (options.length > height) lines.push(dim(`  (${options.length - height} more, scroll with up/down)`));
  if (footer) lines.push(dim(fit(footer, cols - 1)));
  lines.push(dim(fit(`  ${state.multiple ? HELP_MULTI : HELP_SINGLE}`, cols - 1)));
  return lines;
}

function summary(state, message, cols) {
  const labels = state.multiple
    ? state.options.filter((o) => state.selected.includes(o.value)).map((o) => o.label)
    : [state.options[state.cursor].label];
  const text = state.status === 'cancelled' ? 'cancelled' : labels.join(', ') || 'none';
  return `${cyan('?')} ${bold(message)} ${dim(fit(text, cols - message.length - 4))}`;
}

function run({ message, options, footer }, init) {
  if (!isInteractive()) throw new Error('interactive prompt needs a terminal');
  if (!selectable(options).length) throw new Error(`no options for: ${message}`);
  const { stdin, stdout } = process;
  let state = initialState(options, init);
  let drawn = 0;
  const size = () => ({ message, footer, rows: stdout.rows || 24, cols: stdout.columns || 80 });
  const first = render(state, size());
  const draw = (lines) => {
    stdout.write(`${drawn ? `\x1b[${drawn}A\r` : ''}\x1b[0J${lines.join('\n')}\n`);
    drawn = lines.length;
  };
  return new Promise((resolve, reject) => {
    const restore = () => {
      stdin.off('keypress', onKey);
      stdin.setRawMode(false);
      stdin.pause();
      stdout.write('\x1b[?25h');
    };
    const onKey = (_text, key = {}) => {
      try {
        if (key.ctrl && key.name === 'c') {
          restore();
          draw([summary({ ...state, status: 'cancelled' }, message, size().cols)]);
          process.exit(130);
        }
        state = reduce(state, key.name === 'enter' ? 'return' : key.name);
        if (state.status === 'active') return draw(render(state, size()));
        restore();
        draw([summary(state, message, size().cols)]);
        if (state.status === 'cancelled') resolve(CANCEL);
        else resolve(state.multiple ? state.selected : state.options[state.cursor].value);
      } catch (err) {
        restore();
        reject(err);
      }
    };
    readline.emitKeypressEvents(stdin);
    stdin.setRawMode(true);
    stdin.resume();
    stdin.on('keypress', onKey);
    stdout.write('\x1b[?25l');
    draw(first);
  });
}

export const select = ({ initialValue, ...opts }) => run(opts, { initial: [initialValue] });

export const multiselect = ({ initialValues = [], ...opts }) => run(opts, { multiple: true, initial: initialValues });

export const confirm = ({ message, initialValue = true }) =>
  run({ message, options: [{ value: true, label: 'Yes' }, { value: false, label: 'No' }] }, { initial: [initialValue] });
