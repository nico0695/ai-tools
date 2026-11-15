<!-- Static profile. Give each lens only its own section (## structure, ## quality or ## risk), through {profile_sections}. -->

## structure

Static / landing:
- Proportionality first: a small site does not need layers, state management or architecture docs.
- Structure: content separated from layout and components; repeated markup that should be a
  component or partial once it repeats across many pages.
- Assets organization: where images, fonts and styles live; unused assets when evident.

## quality

Static / landing:
- Semantic HTML: landmarks (`header`, `main`, `nav`, `footer`), heading order, buttons vs links.
- Accessibility, statically: `alt` text, labels on forms, color contrast only if a tool reported it,
  keyboard reachability of interactive elements.
- Technical SEO: `title` and `meta description` per page, canonical URLs, Open Graph metadata,
  `robots.txt` and sitemap when the site has several pages.
- Assets (potential unless measured): oversized images in the repo (file size is a fact), no modern
  formats or responsive sizes, fonts loaded without `font-display`, render-blocking scripts.
- Calls to action: primary CTAs present and reachable; forms that submit somewhere real.

## risk

Static / landing:
- Third-party scripts loaded from external origins without integrity attributes, when they handle
  user data.
- Forms posting to endpoints with keys exposed in the page source.
- Docs: how to build, preview and deploy; where content is edited.
- Operability does not apply beyond documentation and configuration.
