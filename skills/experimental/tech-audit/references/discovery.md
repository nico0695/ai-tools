# Discovery

Understand the repository before reading code. Everything here is read-only: listing, reading
manifests and configs, `git` queries. Nothing in this phase executes project scripts.

## 1. Collect

| Item | Where to look |
|---|---|
| Manifest | `package.json` at the target root (the path the user named, else the repository root); `name`, `private`, `type`, `main`/`module`/`exports`/`types`/`bin`, `files`, `engines`, `scripts`, dependency groups |
| Package manager | lockfile: `package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn (`.yarnrc.yml` → berry), `bun.lockb`/`bun.lock` → bun; none → note it |
| Workspaces | `workspaces` in `package.json`, `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json` |
| Runtime | `engines`, `.nvmrc`, `.node-version`, `Dockerfile` base image |
| TypeScript | `tsconfig*.json` or `jsconfig.json` (follow `extends`): `strict` and the individual strict flags, `allowJs`, `checkJs`, `noEmit`, `incremental`/`composite`, `paths` |
| Lint / format | `eslint.config.*`, `.eslintrc*`, `biome.json`, `.prettierrc*`, `oxlint` config |
| Tests | runner config (`vitest.config.*`, `jest.config.*`, `.mocharc*`, `playwright.config.*`, `cypress.config.*`), test file locations and counts by kind (unit, integration, e2e) |
| Coverage | an existing coverage report or thresholds in the runner config. Read only; never generate one |
| Bundler / framework | `vite.config.*`, `webpack.config.*`, `next.config.*`, `nuxt.config.*`, `astro.config.*`, `svelte.config.*`, `angular.json`, `rollup.config.*`, `tsup.config.*` |
| CI | `.github/workflows/*`, `.gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`: which checks run and on what |
| Containers / infra | `Dockerfile`, `docker-compose*.yml`, `.env.example` |
| Entrypoints | `main`/`bin`/`exports`, framework conventions (`src/main.*`, `src/index.*`, `app/`, `pages/`, `server.*`), `index.html` |
| Docs | `README*`, `docs/`, `CONTRIBUTING*`, ADR folders, `CHANGELOG*` |

Read configs, do not interpret them yet beyond what the inventory needs. When the target is a
subdirectory, look for the lockfile, CI, workspaces and Docker at the repository root too, and say
which level each one came from.

## 2. Exclusions

Default exclusions, applied to every later phase: `node_modules`, `dist`, `build`, `out`, `.next`,
`.nuxt`, `.svelte-kit`, `.astro`, `.turbo`, `coverage`, `vendor`, `.cache`, minified files (`*.min.*`),
source maps, lockfiles, snapshot files (`__snapshots__`, `*.snap`), and files marked generated (a
`@generated` / `DO NOT EDIT` header, or paths like `generated/`, `__generated__/`).

Exceptions: include a default-excluded path when it is versioned **and** something the project runs
or ships depends on it as source (e.g. `main` points into a committed `dist/` with no `src/`, or a
`vendor/` folder with local modifications). Record each exception and why.

`include_paths` narrows the universe; `exclude_paths` adds to the exclusions. Both win over defaults.

## 3. Project type

Classify each package (the root, or each workspace in a monorepo). First match wins.

| # | Test | Type |
|---|---|---|
| 1 | a content-oriented framework (`astro` without a server adapter, `@11ty/eleventy`, `gatsby`, `vitepress`, `@docusaurus/core`), a Next.js config with `output: 'export'`, or no frontend framework and no server framework or server entry, with `index.html` plus plain JS/CSS | `static` |
| 2 | a full-stack framework (`next`, `nuxt`, `@remix-run/*`, `@sveltejs/kit`, `@solidjs/start`) with server code present (`app/**/route.*`, `pages/api/`, `server/`, `+server.*`, server actions), or a frontend framework and a backend framework in the same package | `fullstack` |
| 3 | `exports`/`main`/`module` present, no app entry (`index.html`, a server `listen`, a framework app dir), and UI frameworks only in `peerDependencies` if at all | `library` |
| 4 | a server framework or server entry: `express`, `fastify`, `@nestjs/core`, `koa`, `@hapi/hapi`, `hono`, `@apollo/server`, `graphql-yoga`, or a `bin`/entry that starts a long-running process | `backend` |
| 5 | a UI framework (`react`, `vue`, `@angular/core`, `svelte`, `solid-js`, `preact`, `lit`) in `dependencies` with a bundler or framework dev server | `frontend` |
| — | none matched: a CLI or script collection → `backend (cli)`; otherwise `library` if it has `exports`/`main`; otherwise `unknown` | — |

`backend (cli)` uses the backend weights and profile, minus the profile items that only apply to a
server (HTTP, health, shutdown, request transactions), and the Operability exemption in `scoring.md`.

`unknown` uses the fullstack/backend weight row and is stated in the report header.

**Monorepo.** Record every workspace with its type and its role (`app`, `package`, `shared`). The
overall type is: `fullstack` when at least one workspace is `frontend` or `fullstack` and another is
`backend`; otherwise the type shared by the apps; otherwise the type of the majority of workspaces.
Record internal dependencies between workspaces (`workspace:` protocol, matching names) and any
workspace that imports another's internals instead of its public entry.

## 4. Repository state

Signals that change how findings are judged, not findings in themselves:

- branch name and dirty or clean tree (from Phase 0);
- JS/TS coexistence: count of `.js`/`.jsx` vs `.ts`/`.tsx` under source dirs, `allowJs`, `checkJs`;
- partial strictness: `strict: false` with some strict flags on, or strictness that differs per tsconfig;
- migration in progress: a branch or doc naming one, codemods, parallel old/new directories,
  deprecation notices in code or docs;
- recent activity, only in `deep` or `focus: technical-debt`: `git log --since=6.months --name-only`
  aggregated per file, to tell active hotspots from stable legacy.

## 5. Inventory output

Keep it compact; it goes into every worker prompt.

```yaml
reference: <sha | none> · branch: <name> · tree: clean | dirty
type: <type> (detected | user) · notes: [<disagreement, unknown, exceptions>]
workspaces: [{path, type, role, depends_on: [...]}]   # empty when not a monorepo
stack: {runtime, package_manager, frameworks: [...], typescript: {strict, allowJs, notes}}
tooling: {lint, format, tests: {runner, unit, integration, e2e}, bundler, ci: [checks], docker}
scripts: {name: command}                               # only the ones relevant to checks
entrypoints: [...]
docs: [...]
state: [<coexistence, partial strictness, migration in progress>]
exclusions: [...]
```
