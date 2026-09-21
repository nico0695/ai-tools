import { existsSync } from 'node:fs';
import path from 'node:path';
import { REPO } from '../core/context.js';

const SRC = path.join(REPO, 'harness', 'stable', 'sdd-lite');
const PRESERVE = ['project-context.md', 'skill-catalog.md', 'openspec'];

/** @type {import('../types.js').Installer} */
export default {
  id: 'harness',
  label: 'Harness',
  scopes: ['project'],
  providers: ['claude', 'agents'],
  allowEmptyProviders: true,
  allowSelf: false,
  allowUninstall: false,
  existing: 'update',
  groups: [{ id: 'stable', default: true }],
  items: () => {
    if (!existsSync(path.join(SRC, 'skills', 'sddl-init', 'SKILL.md'))) {
      throw new Error(`sdd-lite package not found in ${SRC}`);
    }
    return [{ id: 'sdd-lite', group: 'stable', description: 'Structured workflow for bounded repo changes' }];
  },
  units: (item, ctx) => [
    {
      item: item.id,
      kind: 'sync-dir',
      src: SRC,
      dest: path.join(ctx.base, 'sdd-lite'),
      preserve: PRESERVE,
    },
    ...ctx.providers.map((provider) => ({
      item: item.id,
      provider,
      kind: 'dir',
      src: path.join(SRC, 'skills', 'sddl-init'),
      dest: path.join(ctx.providerDir(provider), 'skills', 'sddl-init'),
    })),
  ],
  nextSteps: () => [
    'Next: run sddl-init in your agent to finish project setup',
    '  skill: sdd-lite/skills/sddl-init/SKILL.md',
  ],
};
