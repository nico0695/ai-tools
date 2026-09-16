# PR description template

Fill each section in plain language. Skip a section only where `SKILL.md` says to (Impact is
conditional; How to validate is opt-in).

```markdown
## What
{changes grouped by topic — what a reviewer needs to understand the change, not a file list}

## Why
{the problem or motivation, in a sentence or two}

## Impact
{only if SKILL.md's Impact condition is met — what else this touches or changes}

## How to validate
{only if the user chose to include this in Step 2 — short numbered steps, each with what to do
and what result confirms it worked}
```

## Example

```markdown
## What
- Guests can now finish checkout without creating an account
- Order confirmation email includes a link to register afterwards

## Why
Requiring an account before paying was the main drop-off point in checkout.

## Impact
- Orders can now exist without a user; reports that join orders to users will skip guest orders

## How to validate
1. Add an item and go to checkout logged out
2. Complete payment as guest — an order is created and the confirmation email arrives
```

Notice what's absent: no file paths, no function or component names, no exhaustive file table. A
name appears only when it identifies something a reviewer would recognize — an endpoint, a
command, a flag — never an internal detail.
