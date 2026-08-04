# UI Prototype

Several **structurally different** variants of the same surface, rendered on one route and switched from a floating bar. The user flips between them, picks one or steals pieces from each, and the rest is thrown away.

If the question is about logic or state, read `LOGIC.md`. If it is about something that already runs, read `PROBE.md`.

## 1. Pick the host

A variant is only judged honestly when it is butting up against the rest of the app — real header, real sidebar, real density. A throwaway route on its own is a vacuum where every variant looks fine.

**Sub-shape A — inside an existing page. This is the default.** The route already exists; variants render on it, gated by a `?variant=` search param. Existing data fetching, params and auth stay exactly as they are — only the rendered subtree swaps. Something with no page yet that would naturally live inside one (a new dashboard section, a new card, a new step in a flow) is still sub-shape A: mount it in the host.

**Sub-shape B — a new route. Last resort.** Only when the thing genuinely has nowhere to live. Follow the project's existing routing convention, put `prototype` in the path, same `?variant=` pattern. Before choosing B, check once more that there is really nowhere to embed it — an empty route hides the problems a populated one exposes.

## 2. Draft the variants

Default to **3**. Past 5 they stop being different and start being noise.

Each variant makes a **bet** — a one-line thesis about what matters most on this screen: "everything reachable without scrolling", "one primary action, the rest behind a menu", "density over hierarchy". Name the variant after its bet, not after a letter. If you cannot state the bet, the variant is wallpaper.

Variants must disagree **structurally**: different layout, different information hierarchy, different primary affordance. Three tweaked card grids is not a prototype. With 3 or more, draft each in its own subagent, blind to the others — variants written in one context converge without anyone deciding to.

Hold each to the page's real purpose, the data it actually has, and the project's existing component and styling system.

## 3. Feed them the ugly data

Over empty state all three look good and the prototype answers nothing. Layout is decided by the worst realistic case, so render every variant against it: the longest name anyone actually has, forty rows, zero rows, the loading state, the error state.

Use the page's real data where sub-shape A gives it for free. Where it does not, hand-write realistic fixtures — never lorem ipsum, whose uniform word length flatters every layout equally.

## 4. Wire the switcher

```tsx
// pseudo-code - adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <ReachableWithoutScrolling {...data} />}
    {variant === 'B' && <SidebarFirst {...data} />}
    {variant === 'C' && <DenseTable {...data} />}
    <PrototypeSwitcher variants={['A', 'B', 'C']} current={variant} />
  </>
);
```

The bar sits fixed at the bottom centre: left arrow, the current key plus its bet, right arrow, both wrapping around.

- Arrows update the search param through the framework's router, so a variant is shareable and survives reload.
- Left and right arrow keys cycle too — but not while an input, textarea or contenteditable element has focus.
- Visually distinct from the page (high-contrast pill, shadow) so it is obviously not part of the design being judged.
- Hidden outside development. Gate it on the project's env check so a stray merge cannot ship it to users.

Keep the switcher in one shared component, wherever shared UI lives.

## 5. Run it, then hand over the URL

Start the dev server and confirm the route builds and each variant renders without throwing. You may not be able to see it — say what you verified and what you did not.

Give the user the URL with the param, and the variants listed by their bets. The most useful thing they will say is "the header from B with the sidebar from C" — that combination is the actual design, and it is a fourth variant rather than a compromise.

## 6. Close it out

Return to Phase 7 of `../SKILL.md`. Sub-shape A: fold the winner into the page and drop the losers and the switcher from the working tree. Sub-shape B: promote the winner to a real route and drop the throwaway one. The full set is the primary source and belongs on the throwaway branch — variants left in the main branch rot within a week and confuse whoever reads them next.

## Anti-patterns

- **Structural disagreement, not colour.** If two variants differ by a palette, one of them is not a variant.
- **A shared header is fine; a shared layout defeats the point.** Each variant has to be free to throw the layout out.
- **Read, do not mutate.** A variant needing a mutation points at a stub — the question is what this should look like, not whether the backend works.
- **Rewrite when folding, do not promote.** The winner was written under prototype rules, with no error handling and no tests. It is a design, not an implementation.
