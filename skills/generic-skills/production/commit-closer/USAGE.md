# commit-closer — usage

Drafts a commit message, a PR description, or both, from changes that already exist. Reads git;
never writes to it. Requests to commit, push, or open a PR are handled as draft requests only.

## When to use it

- You want a commit message or a PR description drafted from what you actually changed, not typed
  by hand.
- You want the drafted text to stay readable — what changed and why, not a tour of every file
  touched.

## When not to

- You want the code itself reviewed — that's `code-review` or `4r-review`. This skill only drafts
  text about changes that already happened; it does not evaluate them.
- You want the change committed or pushed. This skill never runs a git command that writes — you
  apply the message yourself.

## How to invoke

Explicit invocation, or a request to write a commit message or PR description. It suggests
itself — without starting — when you ask to prepare a commit or PR without asking for the text
specifically.

If a request combines several Git actions (commit and push, commit and open a PR), it asks which drafts
you want before reading. Asking for both drafts, or for a single Git action, needs no extra question.

## What you'll be asked

One source question up front: which source to draft from (staged changes, the working tree, the
current branch against its base, or an explicit range), with a proposal based on what you've been
working on in the session. If a PR is in scope, it also asks whether to include validation steps.
A second question, only if still needed after reading the diff, asks why the change was made and
what it affects — asked once. If something is still unclear after that, the draft states the
assumption instead of asking again.

## Minimal example

> "Draft a commit message for this" — staged changes to a checkout flow

```
feat(checkout): let guests complete checkout without an account

Requiring an account before paying was the main drop-off point in checkout. Guests can now
complete payment directly; the confirmation email offers to register afterwards.
```

Alternative 1 — mechanism:

```
feat(checkout): skip the account requirement in the payment step
```

Alternative 2 — symptom:

```
feat(checkout): stop dropping guests at the account wall
```

> "Also draft the PR" — same change, branch against `main`

```
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

```
TL;DR — checkout no longer requires an account; guest orders need to be accounted for in
user-joined reports.
```

---

For how the source is resolved, what the Impact section actually gates on, and why it is shaped
this way, see [README.md](./README.md).
