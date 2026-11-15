<!-- Library profile. Give each lens only its own section (## structure, ## quality or ## risk), through {profile_sections}. -->

## structure

Library:
- Public API surface: what `exports`/`main` exposes vs what is internal; internals reachable through
  deep imports that consumers will start depending on.
- Encapsulation: internal types or helpers leaking through public signatures, widening the
  breaking-change surface.
- Entry structure: a single entry that pulls the whole library when consumers need a part
  (tree-shaking hostile patterns, side effects at import time).

## quality

Library:
- Types: published types (`types`/`typings`, `.d.ts` generation) match the runtime API; `any` in
  public signatures.
- Compatibility: `engines`, module format (`type`, dual ESM/CJS `exports` conditions) consistent with
  what is built; `peerDependencies` for frameworks the consumer provides instead of `dependencies`.
- Contract stability: public API covered by tests; behavior changes visible in a changelog.
- Dependencies: runtime dependencies kept minimal; heavy dependencies only with evidence of size.

## risk

Library:
- Consumer documentation: install, usage examples for the main API, supported environments.
- Changelog or release notes that tell consumers about breaking changes.
- Operability does not apply beyond documentation and configuration: no logging, health or shutdown
  expectations.
- Security: dynamic code execution or unsafe deserialization exposed to consumer input; dependency
  audit results.
