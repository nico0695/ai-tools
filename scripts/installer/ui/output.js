import os from 'node:os';
import path from 'node:path';

const paint = (stream, open, close, text) =>
  stream.isTTY && !process.env.NO_COLOR ? `\x1b[${open}m${text}\x1b[${close}m` : String(text);
const wrap = (open, close) => (text) => paint(process.stdout, open, close, text);

export const bold = wrap(1, 22);
export const dim = wrap(2, 22);
export const red = wrap(31, 39);
export const green = wrap(32, 39);
export const yellow = wrap(33, 39);
export const cyan = wrap(36, 39);

export function fit(text, width) {
  if (text.length <= width) return text;
  return width < 4 ? text.slice(0, Math.max(0, width)) : `${text.slice(0, width - 3)}...`;
}

export function tilde(p) {
  const home = os.homedir();
  if (p === home) return '~';
  return p.startsWith(home + path.sep) ? `~${p.slice(home.length)}` : p;
}

export const log = (text = '') => process.stdout.write(`${text}\n`);
export const ok = (text) => log(`${green('  ok')}  ${text}`);
export const warn = (text) => process.stderr.write(`${paint(process.stderr, 33, 39, 'warning:')} ${text}\n`);
export const fail = (text) => process.stderr.write(`${paint(process.stderr, 31, 39, 'error:')} ${text}\n`);
