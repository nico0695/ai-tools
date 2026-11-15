<!-- Frontend profile. Give each lens only its own section (## structure, ## quality or ## risk), through {profile_sections}. -->

## structure

Frontend:
- Component structure: components that fetch, transform, hold business rules and render at once;
  business logic living in UI components instead of a layer they call.
- State ownership: global stores or contexts holding state from unrelated features; one oversized
  context whose consumers re-render on unrelated changes; the same server data cached in several
  places by hand.
- Prop drilling through several layers where a closer owner or composition would cut it, only when
  it forces changes across many files.
- Feature boundaries: features importing each other's internal components or hooks.

## quality

Frontend:
- Effects: `useEffect` (or equivalent) used to derive state, missing or suppressed dependencies
  (`eslint-disable react-hooks/exhaustive-deps`) on logic that reads changing values, effects
  without cleanup for subscriptions or timers.
- Data fetching: loading and error states missing on screens that fetch; race conditions on fast
  navigation; fetch logic duplicated per component instead of shared.
- Memoization: recommend it only when the code shows a concrete cost (heavy computation or large
  lists re-rendering on unrelated changes). Never as a general practice.
- Splitting: routes or heavy features loaded eagerly from the main entry; bundle size only from a
  stats artifact.
- Accessibility, statically: non-semantic clickable elements (`div` with `onClick` and no role or
  keyboard handler), images without `alt`, form inputs without labels, focus management in modals.
- Tests: component tests that only snapshot; no tests around the hooks or stores that hold logic.

## risk

Frontend:
- Secrets shipped to the client: private keys or tokens in client env variables (`VITE_`,
  `NEXT_PUBLIC_`, `REACT_APP_` prefixes with secret-looking values) or in source.
- `dangerouslySetInnerHTML` / `v-html` / `innerHTML` with data that is not sanitized.
- Authorization enforced only by hiding UI, with no indication of a server check.
- Tokens stored in `localStorage` when the app otherwise handles sensitive data; note, do not assume
  an attack.
- Docs: how to run, build and configure environments; which API it expects.
