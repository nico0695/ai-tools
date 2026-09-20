import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { after } from 'node:test';

export function tempDir() {
  const dir = mkdtempSync(path.join(os.tmpdir(), 'ai-tools-test-'));
  after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

export function writeTree(root, files) {
  for (const [rel, content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
    writeFileSync(path.join(root, rel), content);
  }
  return root;
}
