---
name: github-workflow
description: >
  Defines Git and GitHub workflow rules and conventions. Use this skill
  whenever performing any git operation — committing, branching, rebasing,
  squashing, opening or reviewing PRs, writing code comments, or managing
  issues and labels. Trigger on phrases like "commit", "push", "open a PR",
  "create a branch", "squash", "rebase", "review", "comment", or any
  GitHub-related action. This skill encodes personal workflow preferences
  and must be followed precisely.
license: MIT
metadata:
  author: user
  version: "1.0"
---

## Overview

This skill defines the exact Git and GitHub workflow conventions to follow
for all repository work. These rules are non-negotiable — always apply them
unless the user explicitly overrides a specific rule in the moment.

---

## Branch Naming

All branches must follow this pattern:

```
feature/issue-123-short-description
```

Rules:
- Prefix is always `feature/` regardless of the type of work (bug fix,
  chore, experiment, etc.)
- `issue-123` is the GitHub issue number. Omit the issue segment only when
  there is no associated issue: `feature/short-description`
- `short-description` is lowercase, hyphen-separated, 2–5 words max
- Never use slashes, underscores, or uppercase in the slug

Examples:
```
feature/issue-42-user-auth
feature/issue-101-migrate-db-schema
feature/update-readme
```

Create branches from `dev`, never from `main`:
```bash
git checkout dev
git pull --rebase origin dev
git checkout -b feature/issue-123-short-description
```

---

## Commit Messages

All commits must use **Conventional Commits** format with a detailed body:

```
<type>(<scope>): <short summary>

<body — explain what changed and why, enough detail for any reader to
understand the change without looking at the diff>
```

### Types

| Type       | When to use                                         |
|------------|-----------------------------------------------------|
| `feat`     | New feature or capability                           |
| `fix`      | Bug fix                                             |
| `chore`    | Maintenance, dependency updates, tooling            |
| `refactor` | Code restructuring with no behavior change          |
| `docs`     | Documentation only                                  |
| `test`     | Adding or updating tests                            |
| `style`    | Formatting, whitespace (no logic change)            |
| `perf`     | Performance improvement                             |
| `ci`       | CI/CD configuration changes                         |

### Subject line rules

- 72 characters max
- Lowercase after the colon
- No trailing period
- Use imperative mood: "add", "fix", "remove" — not "added", "fixes"

### Body rules

- For commits generated automatically by an agent, the body of the commit message must be prefixed with 'opencode:' or 'agent:' (e.g., 'opencode: Implement ...' or 'agent: Fix ...').
- Wrap at 72 characters
- Explain **what** changed and **why** — not how (the diff shows how)
- Mention any non-obvious side effects or related areas affected
- Reference the issue if one exists: `Closes #123` or `Related to #45`

### Examples

```
feat(auth): add JWT refresh token rotation

Implement sliding session refresh so users are not logged out after
the short-lived access token expires. The refresh endpoint issues a
new token pair and invalidates the previous refresh token to prevent
replay attacks.

Closes #42
```

```
fix(api): handle null response from upstream pricing service

The pricing service occasionally returns null for discontinued SKUs.
Previously this caused an unhandled TypeError in the cart total
calculation. Now falls back to a cached price with a warning log.

Related to #88
```

```
chore(deps): upgrade pydantic from 1.x to 2.x

Pydantic v2 introduces breaking changes to model validators and
field aliases. Updated all models and serializers to the new API.
No behavior changes to public-facing endpoints.
```

---

## Rebase — Never Merge

**Never use `git merge` to integrate branch changes.** Always rebase.

### Keeping a feature branch up to date with `dev`

```bash
git fetch origin
git rebase origin/dev
```

If there are conflicts, resolve them file by file, then:
```bash
git add <resolved-files>
git rebase --continue
```

### Rebase rules

- Rebase feature branches onto `dev` regularly to avoid large divergence
- Never rebase `dev` or `main` — only rebase feature branches
- Never force-push to `dev` or `main`
- Force-push to a personal feature branch is acceptable after a rebase:
  ```bash
  git push --force-with-lease origin feature/issue-123-slug
  ```
- Always use `--force-with-lease` instead of `--force` to avoid
  overwriting remote work you haven't seen

---

## Squashing Commits

Squash commits **only when a feature is stable and ready for PR** — not
during active development. This preserves the ability for others to pull
intermediate states without getting a broken version.

### When to squash

- Feature is complete and tested
- You are about to open a PR
- Never squash mid-development, even if commits are messy

### How to squash

Use the custom `git squash <n>` command to collapse the last `n` commits
into one:

```bash
git squash <n>
```

This will prompt for a single commit message. Write the final conventional
commit message for the whole feature here — not a summary of the individual
commits that were squashed.

**Target: exactly 1 commit per PR.**

After squashing, verify the history looks correct:
```bash
git log --oneline -5
```

Then force-push:
```bash
git push --force-with-lease origin feature/issue-123-slug
```

### Squash commit message

The squashed commit message should represent the entire PR's change as a
single conventional commit. It should be detailed enough for a reader to
understand the full scope of the work:

```
feat(payments): integrate Stripe checkout with webhook event handling

Added end-to-end Stripe checkout flow including session creation,
success/cancel redirect handling, and webhook processing for
payment_intent.succeeded and payment_intent.payment_failed events.
Webhook signatures are verified using the Stripe-Signature header.
Orders are updated atomically on confirmed payment to prevent
partial state.

Closes #77
```

---

## Pull Request Descriptions

PRs must use the following template structure. Include all sections;
mark sections as "N/A" if they do not apply rather than omitting them.

```markdown
## Summary

[1–3 sentences describing what this PR does and why it exists.]

## Changes

- [Specific change 1]
- [Specific change 2]
- [...]

List the meaningful changes made. Be specific — file names, function names,
and data structures are appropriate here. Do not just restate the summary.

## Testing

[Describe how the changes were tested. Include commands, test file names,
or manual steps taken. If automated tests were added, name them.]

## Screenshots

[Attach screenshots or screen recordings if there are any UI changes.
Write "N/A" if this PR has no visual changes.]

## Notes

[Optional. Anything a reviewer should know before reviewing — areas of
uncertainty, known limitations, follow-up issues, or decisions made.]
```

### PR rules

- Title must follow the same Conventional Commits format as commit messages
- If a GitHub issue exists, reference it in the Summary or Notes:
  `Closes #123` / `Related to #45`
- Issue references are not required when no issue exists
- PRs should be opened against `dev`, never directly against `main`
- Do not open a PR until commits are squashed to 1

---

## Code Comments

### Module / file header

Every module file must have a top-of-file docstring describing its purpose,
using the language-appropriate Google-style docstring format.

**Python:**
```python
"""
Module for handling Stripe webhook events.

Processes inbound webhook payloads, verifies signatures, and dispatches
events to the appropriate order and billing update handlers.
"""
```

**JavaScript / TypeScript:**
```javascript
/**
 * @fileoverview Handles Stripe webhook event processing.
 *
 * Verifies webhook signatures, parses event payloads, and routes
 * events to order and billing update handlers.
 */
```

### Function / method docstrings

Every function and method must have a Google-style docstring.

**Python:**
```python
def create_checkout_session(cart_id: str, user_id: str) -> str:
    """Creates a Stripe checkout session for the given cart.

    Args:
        cart_id: The ID of the cart to check out.
        user_id: The authenticated user initiating checkout.

    Returns:
        The Stripe session URL to redirect the user to.

    Raises:
        CartNotFoundError: If the cart does not exist.
        stripe.error.StripeError: If the Stripe API call fails.
    """
```

**JavaScript / TypeScript (JSDoc):**
```javascript
/**
 * Creates a Stripe checkout session for the given cart.
 *
 * @param {string} cartId - The ID of the cart to check out.
 * @param {string} userId - The authenticated user initiating checkout.
 * @returns {Promise<string>} The Stripe session URL.
 * @throws {CartNotFoundError} If the cart does not exist.
 */
async function createCheckoutSession(cartId, userId) {
```

### Inline block comments

Comment blocks of non-obvious logic to explain **what** the block does,
briefly. One comment per logical block — not per line.

```python
# Verify the webhook signature to reject tampered or replayed payloads
try:
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
except stripe.error.SignatureVerificationError:
    raise WebhookVerificationError("Invalid signature")

# Dispatch to the correct handler based on event type.
# Unrecognised event types are logged and silently ignored.
handler = EVENT_HANDLERS.get(event["type"])
if handler:
    handler(event["data"]["object"])
else:
    logger.info("Unhandled Stripe event type: %s", event["type"])
```

### What NOT to comment

- Do not restate what the code literally does (`i += 1  # increment i`)
- Do not comment obvious getters, setters, or trivial one-liners
- Do not put design decisions in code comments — those belong in a
  separate design document

---

## Issue Comments and Labels

When commenting on a GitHub issue:
- Be specific and actionable — reference file names, function names, or
  line numbers where relevant
- If reporting a bug, include reproduction steps and observed vs expected
  behavior
- If proposing a solution, briefly justify the approach

When applying labels, prefer these conventions:

| Label         | Meaning                                      |
|---------------|----------------------------------------------|
| `bug`         | Something is broken                          |
| `feat`        | New feature request                          |
| `chore`       | Maintenance / housekeeping                   |
| `docs`        | Documentation work                           |
| `blocked`     | Cannot proceed — waiting on something        |
| `needs-triage`| Newly opened, not yet assessed               |
| `wontfix`     | Acknowledged but will not be addressed       |

---

## Code Review Comments

When leaving review comments on a PR:
- Prefix comments with a severity indicator:

  | Prefix       | Meaning                                                  |
  |--------------|----------------------------------------------------------|
  | `nit:`       | Minor style or preference — non-blocking                 |
  | `suggestion:`| Improvement idea — non-blocking, take it or leave it     |
  | `question:`  | Asking for clarification — non-blocking                  |
  | `issue:`     | Something that must be fixed before merge — blocking     |
  | `blocker:`   | Critical problem — blocking, explain why                 |

- Be specific: reference the exact line or block, and explain the concern
- For `issue:` and `blocker:` comments, suggest a concrete fix or direction
- Approve only when all `issue:` and `blocker:` comments are resolved

---

## Gotchas

- Never run `git merge` — if you see a merge happening, stop and rebase instead
- Never squash commits on `dev` or `main`
- Never force-push to `dev` or `main`; only force-push personal feature branches using `--force-with-lease`
- Do not open a PR with more than 1 commit — squash first
- Do not rebase mid-feature if others are pulling your branch — coordinate first
- `git squash <n>` is a custom alias; do not confuse it with `git rebase -i HEAD~n` (they achieve the same result but the alias is preferred)
- When rebasing onto `dev`, always `git fetch origin` first so you rebase onto the latest remote state, not a stale local copy
