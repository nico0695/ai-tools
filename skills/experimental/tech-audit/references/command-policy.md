# Command policy

Run only what is clearly an analysis, clearly safe, and already part of the project. When in doubt,
do not run it: record the check as `not_executed` with the reason. A check that exists and was not run
costs a line in Analysis Limits; a check that changed the repository costs the audit its premise.

## 1. Classes

| Class | Commands | Rule |
|---|---|---|
| Always allowed | `git status`, `git log`, `git ls-files`, `git rev-parse`, `git diff --stat`; `ls`, `cat`, `head`, `wc`, `grep`, `rg`, `find` | Any depth, as long as they only read: no `find -delete`/`-exec`/`-fprint`, no `--output=<file>`, no redirection (`>`, `>>`, `tee`) into the repository |
| Allowed when vetted (§2) | lint without fixing; typecheck; unit tests in run mode; a dependency-cycle tool already installed (`deep` only) | `standard` and `deep` |
| Allowed, network | `npm audit --json`, `pnpm audit --json`, `yarn npm audit --json` (berry), `yarn audit --json` (v1) | `standard` and `deep`, only with a lockfile. Never `audit fix`. Bun has no audit command: record it as `not_executed` |
| Exists, not executed | build, e2e, integration, benchmarks, custom scripts, anything §2 rejects | Record it with the reason |
| Never | `install`, `ci`, `add`, `update`, `upgrade`, `dedupe`, `audit fix`, `--fix`, `--write`, `format`, `migrate`, `seed`, `db push`/`db reset`, `deploy`, `publish`, `release`, `version`, `prepare`, `postinstall`, any `rm`/`mv`/`cp` into the repo, `git` writes | Never, at any depth, even if the user asks during the audit. Answer with a recommendation instead |

## 2. Vetting a check

Apply in order; the first failing test rejects the check.

1. `node_modules` exists at the package root (or the workspace root for a monorepo), or the package
   declares no dependencies of any kind (nothing to install; e.g. `node --test` on a zero-dependency
   package). Otherwise nothing in this class runs: the audit never installs to make a check possible. The dependency audit only
   needs the lockfile.
2. The script exists in `package.json`, or the check can run through a tool already in
   `node_modules/.bin` with the safe arguments in §3.
3. Read the script body. Reject it when it contains any of: `--fix`, `--write`, `--apply`,
   `--apply-unsafe`, `-w ` with a formatter, `--cache`, `-u`/`--updateSnapshot`, `--coverage`, `--watch`,
   `-b`/`--build`, `migrate`, `seed`, `prisma db`, `deploy`, `publish`, `rm `, `>` redirection into a
   file, a task runner that fans out with declared dependencies (`turbo`, `nx`, `lerna run`; they run
   `dependsOn` tasks such as builds), or chains (`&&`, `;`, `npm-run-all`, `concurrently`) that include
   an unvetted step.
4. Vet what the script pulls in, with these same tests: every `npm|pnpm|yarn|bun run <x>` it calls, and
   the `pre<name>` and `post<name>` scripts that npm, yarn v1 and bun run automatically around it. If
   any of them fails, reject the script.
5. Reject when the script, or anything step 4 pulls in, runs a local file (`node scripts/x.js`,
   `tsx tools/y.ts`, `bash ./z.sh`): its behavior is not visible from `package.json`. A test runner
   discovering test files (`node --test`, `vitest run`, `jest`) is the runner, not a local script.
6. Tests only: reject when the script name, the runner config or the test paths point at integration
   or e2e (`e2e`, `integration`, `int`, `cypress`, `playwright`, `testcontainers`), when a
   `globalSetup` starts services or containers, or when tests need a database or external service
   that the repository does not mock. Skim the test helpers first: reject when tests write outside a
   temporary directory (home, real config paths) without redirecting it. When the runner config enables coverage (`coverage.enabled` in
   vitest, `collectCoverage` in jest), run the direct form with coverage turned off (§3).
7. Typecheck only: when the tsconfig the script uses sets `composite`, record typecheck as
   `not_executed` (§3). When it sets `incremental` without `composite`, the script would write
   `.tsbuildinfo`; use the direct form instead.

A rejected script may still be replaced by the tool's own binary with the safe arguments of §3, as
long as tests 1 and 6 pass. Record which one ran: "script `lint`" or "`eslint .` (script rejected:
contains `--fix`)".

## 3. How to run

| Check | Preferred form | Safe direct form |
|---|---|---|
| Lint | the `lint` script | `eslint .` / `biome lint .` / `oxlint`, no `--fix`, no `--cache` |
| Typecheck | `typecheck` / `type-check` / `tsc` script with `--noEmit` | `tsc --noEmit --incremental false -p <tsconfig or jsconfig>`, only if `tsc` is in `node_modules/.bin`; in a project-references setup (`composite`), do not run `tsc -b`: record it as `not_executed` |
| Unit tests | the `test` / `test:unit` script | `vitest run --coverage.enabled=false`, `jest --ci --watchAll=false --coverage=false`, `mocha`, `node --test`; never `-u` |
| Cycles (`deep`) | — | `madge --circular --extensions ts,tsx,js,jsx <src>` or `dpdm --no-tree --circular <entry>`, only if already in `node_modules/.bin` |
| Dependency audit | — | the package manager's audit with `--json` (see §1) |

Always:

- prefix with `CI=true` so runners neither watch nor prompt;
- use the package manager from the lockfile (`npm run`, `pnpm run`, `yarn run`, `bun run`);
- run from the package root; in a monorepo, run per workspace, for the apps and the shared packages
  only, never through a fan-out task runner;
- set a timeout: 5 minutes per lint, typecheck or audit, 10 minutes per test run, through the agent's
  own command timeout, or `timeout`/`gtimeout` when present (never install one). A timeout is
  recorded as `not_executed (timeout)`, never as a pass or a fail;
- run sequentially, never in parallel.

## 4. What to record

Per check: the exact command, the exit code, the status (`passed`, `failed`, `not_executed`, `absent`),
counts when the tool prints them (errors and warnings; tests passed, failed and skipped; vulnerabilities
by severity), and at most 20 lines of output that support a finding. Never summarize a failure you did
not see in the output.

A failing check is evidence, not a verdict: lint errors in generated code or a single flaky test are
weighed by the lens that owns them.

## 5. No-write check

Compare `git status --porcelain` before and after the commands (SKILL.md, Phase 2). The comparison only
sees files Git tracks or would show as untracked; caches inside ignored paths (`node_modules/.cache`,
`.eslintcache`, `.tsbuildinfo` when ignored) are invisible to it. That is why §2 and §3 avoid the flags
that write them. Analysis Limits states the comparison result, and, when commands ran, that writes into
ignored cache paths cannot be ruled out.
