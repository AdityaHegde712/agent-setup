---
name: code-debugger
description: >
  A professional-grade debugging skill for web and desktop application
  development. Trigger this skill whenever a bug, error, crash, unexpected
  behavior, regression, broken test, failed build, or environment issue
  is reported or encountered. Use it for runtime errors, network failures,
  state bugs, UI glitches, auth issues, database problems, API misbehavior,
  performance degradation, and broken CI/CD pipelines. This skill encodes
  the reasoning process and tooling habits of a senior software engineer
  and must be followed from diagnosis through to verification. Do not skip
  phases or jump to fixes without completing the investigation first.
license: MIT
metadata:
  author: user
  version: "1.0"
  scope: web, desktop
  excludes: ml-debugging, model-training, inference-pipelines
---

# Code Debugger

A structured, senior-engineer-grade debugging process for web and desktop
application development. Agent-agnostic — no assumptions about platform,
IDE, or AI provider.

---

## Core Principles

These are non-negotiable and apply throughout every debugging session:

1. **Understand before acting.** Do not modify code until the root cause is
   identified or a hypothesis is formed. Premature changes corrupt the signal.

2. **One variable at a time.** Change one thing per investigation step.
   Multiple simultaneous changes make it impossible to attribute cause.

3. **Reproduce before fixing.** If you cannot reproduce the bug reliably,
   you cannot confirm a fix. Flaky reproduction is a problem to solve first.

4. **Read the actual error, completely.** Do not skim stack traces. The
   relevant frame is often not the first or the last.

5. **Check your assumptions explicitly.** Most bugs live in the gap between
   what you believe is true and what is actually true. Surface that gap.

6. **Fix the cause, not the symptom.** A symptom-level fix leaves the
   underlying defect in place and creates future confusion.

7. **Leave an audit trail.** Comment non-obvious fixes, update tests, and
   document why the fix works — not just what it does.

---

## Debugging Phases

Work through these phases in order. Skip forward only when a phase is
genuinely not applicable. Document what you find at each step.

### Phase 1 — Establish Baseline Facts

Before touching anything, gather the raw facts:

- What is the **exact** error message, exception type, and stack trace?
- What is the **exact** user action or code path that triggers it?
- When did it **first** appear? (Specific commit, deploy, time, or change)
- Does it reproduce **consistently** or only under specific conditions?
- What **environment** is affected? (OS, browser, Node version, env vars, etc.)
- What **changed recently**? (Dependencies, config, schema, env, code)

Do not proceed past this phase if you cannot answer at least 80% of these.
If the error is intermittent, treat fixing reproducibility as the first task.

### Phase 2 — Classify the Bug

Categorize the bug before investigating. The category determines the correct
diagnostic tools and order of investigation. See the **Bug Taxonomy** section
below for classification guidance.

**Taxonomy quick-pick:**

| Symptom | Likely Category |
|---|---|
| Exception with stack trace | Runtime Error |
| Wrong value, silent failure | Logic / State |
| Works locally, fails in CI/prod | Environment / Config |
| Slow, memory grows, hangs | Performance / Resource |
| UI wrong but data correct | Rendering / CSS |
| Auth fails, tokens invalid | Auth / Session |
| API returns wrong or no data | Network / API |
| Build fails, tests fail | Build / Test |
| DB query errors, wrong records | Database |

### Phase 3 — Isolate the Blast Radius

Determine what is actually affected:

- Which **modules, services, or components** are involved?
- Does the bug affect **all users** or a subset (role, browser, region)?
- Is the bug **data-dependent**? Try with a known-clean dataset.
- Is the bug **path-dependent**? Try reaching the same state a different way.
- Does the bug occur on a **clean environment** (fresh install, new DB, clear cache)?

Narrowing the blast radius prevents fixing the wrong code and reveals whether
the bug is isolated or systemic.

### Phase 4 — Hypothesize

Form at most 3 specific, falsifiable hypotheses before writing any code.

A good hypothesis follows this format:
> "The bug occurs because [specific mechanism] when [specific condition],
> which causes [observed effect]. I expect to confirm this by [test]."

Rank hypotheses by likelihood, starting with the simplest. Write them down
explicitly — this keeps investigation disciplined and creates a record.

### Phase 5 — Investigate (Structured)

Test hypotheses using the appropriate tools for the category. Do not rely
on intuition alone. Use the **Diagnostic Toolkit** section for specific
commands and techniques per bug category.

Investigation checklist:
- [ ] Read the full stack trace, not just the top frame
- [ ] Add targeted logging at the boundary where behavior diverges from expectation
- [ ] Verify inputs at the point of failure (do not assume upstream correctness)
- [ ] Check whether the bug exists on the `main`/`dev` branch (regression check)
- [ ] Search the codebase for other usages of the failing function/module
- [ ] Read the relevant dependency documentation if the failure is at an API boundary

### Phase 6 — Confirm Root Cause

Before writing the fix, confirm your hypothesis is the root cause:

- Can you **reproduce the bug** by artificially triggering the cause in isolation?
- Can you **prevent the bug** by removing or guarding the cause?
- Does the fix **make sense semantically** — does it address the actual problem?

If you cannot answer yes to all three, continue investigating.

### Phase 7 — Fix

Write the minimal fix that resolves the root cause. Follow these rules:

- **Smallest possible diff.** Do not refactor unrelated code in the same change.
- **Defensive where appropriate.** Add guards, null checks, or fallbacks if the
  system should have been resilient to this class of failure.
- **Preserve intent.** The fix should make the code do what it was designed to
  do, not work around it.
- **Do not add workarounds** that mask the root cause (catching and silencing
  exceptions, hardcoding fallback values, etc.) unless explicitly time-boxed and
  documented.

### Phase 8 — Verify

Verification is not optional:

1. **Reproduce the original bug** with the fix in place — confirm it no longer
   occurs.
2. **Run the full test suite** for the affected module or service.
3. **Check adjacent behavior** — does the fix break any related functionality?
4. **Test edge cases** specific to the bug (empty input, null, boundary values,
   concurrent access, etc.).
5. If the bug was intermittent, **run the scenario multiple times** to gain
   confidence.

### Phase 9 — Prevent Recurrence

After confirming the fix:

- **Write a regression test** that would have caught this bug. This is mandatory
  unless the test infrastructure literally cannot support it.
- **Add a comment** on the fix explaining *why* it is necessary, not just what
  it does.
- If the root cause reveals a systemic issue (missing validation, absent error
  handling pattern, incorrect assumption across many modules), **file a follow-up
  issue** rather than expanding the current fix.

---

## Bug Taxonomy

Detailed investigation guidance per category.

### Runtime Errors

**Signals:** Exception thrown, process crash, unhandled promise rejection,
unexpected `null` / `undefined` reference.

**Investigation order:**
1. Read the full stack trace. Identify the first frame in **your** code, not a
   library. Library frames show where it blew up; your code shows why.
2. Check the inputs to the failing function at that frame. Add a log or
   breakpoint immediately before the failure.
3. Trace backwards — where does that input come from? Is it nullable?
   Is it the right type? Is it initialized before use?
4. Check whether the error is caught somewhere upstream and silently swallowed.
   Grep for `catch` blocks around the call site.

**Common sources:**
- Unguarded nullable access (`obj.field` where `obj` is `null`)
- Async code missing `await` (function returns a Promise, not a value)
- Off-by-one on array access
- Type coercion surprises (`==` vs `===`, implicit string→number)
- Circular reference in JSON serialization
- Missing `return` in a function expected to return a value

---

### Logic / State Bugs

**Signals:** Wrong output, no error thrown, data gets corrupted silently,
UI shows stale or incorrect state.

**Investigation order:**
1. Find the exact point where the value diverges from expected. Use binary
   search with logs — narrow it to a specific function, then a specific line.
2. Log the **input** and **output** of each transformation in the chain until
   you find the step that produces wrong output.
3. Check for **mutation** — is the original data being changed instead of
   a copy? Especially in objects/arrays passed by reference.
4. Check for **shared mutable state** — is something else modifying the value
   concurrently or before your code reads it?
5. Verify **ordering** — are async operations completing in the order you assume?

**Common sources:**
- Mutating instead of cloning objects/arrays
- Stale closure over a mutable variable
- Race condition between concurrent async operations
- Incorrect comparison (`>` should be `>=`, `===` should be `!==`)
- Boolean logic error (De Morgan's law is frequently violated)
- Missing `break` in a `switch` statement
- Incorrect initial state or state not reset between operations
- Frontend state library (Redux, Zustand, Pinia, etc.) selector returning
  wrong slice due to stale reference

---

### Environment / Configuration Bugs

**Signals:** Works locally but fails in CI, staging, or production. Differs
between developer machines. Fails after a deployment with no code change.

**Investigation order:**
1. Identify **exactly** which environments are affected vs. unaffected.
2. Diff the **environment variables** between working and failing environments.
3. Diff the **dependency versions** (`package-lock.json`, `poetry.lock`, etc.).
4. Check **file system paths** — hardcoded absolute paths, missing files,
   permission issues.
5. Check **service connectivity** — can the affected environment reach all
   external services (DB, cache, API, auth provider)?
6. Check **build-time vs. runtime** configuration injection. Env vars embedded
   at build time are frozen; vars loaded at runtime are not.

**Checklist:**
- [ ] Compare `.env` / env var dumps between environments
- [ ] Check for missing required env vars (app should fail loudly on startup if required vars are absent)
- [ ] Verify third-party service credentials are valid in the target environment
- [ ] Confirm the deployed artifact matches the expected commit
- [ ] Check if the issue is caused by caching (CDN, build cache, Docker layer)

---

### Performance / Resource Bugs

**Signals:** Slow page load, slow API response, high memory usage, memory
leak over time, CPU spike, request timeout.

**Investigation order:**
1. **Measure first.** Identify the actual bottleneck before guessing. Use profiling
   tools appropriate to the stack.
2. For API slowness: check DB query count and duration. N+1 queries are the most
   common cause.
3. For memory leaks: check for retained event listeners, cached objects with no
   eviction, growing arrays never cleared, closures capturing large objects.
4. For frontend slowness: check render count, re-renders triggered by reference
   equality failures, large bundle size, unoptimized images.
5. For CPU spikes: profile with CPU sampling. Identify hot functions.

**Profiling tools by stack:**

| Stack | Tool |
|---|---|
| Node.js | `--inspect` + Chrome DevTools, `clinic.js`, `0x` |
| Browser JS | Chrome DevTools Performance tab |
| React | React DevTools Profiler |
| Python backend | `cProfile`, `py-spy`, `memory_profiler` |
| PostgreSQL | `EXPLAIN ANALYZE`, `pg_stat_statements` |
| MySQL | `EXPLAIN`, slow query log |

**Common sources:**
- N+1 database queries (loop issuing one query per row)
- Missing database index on a filtered or sorted column
- Returning too much data (no pagination, no field projection)
- Unthrottled event listeners (scroll, resize, keydown firing on every event)
- Synchronous heavy computation blocking the event loop
- Memory leak via retained event listeners or global cache with no TTL
- Rendering entire lists without virtualization

---

### Rendering / UI Bugs

**Signals:** UI displays wrong data, layout is broken, styles not applied,
component renders at wrong time, visual glitch.

**Investigation order:**
1. Open browser DevTools. Inspect the actual DOM — is the element present,
   and is it what you expect?
2. Check the **computed styles** on the element. Is the style you expect present?
   Is it being overridden? Check the cascade.
3. Check the **data** driving the render. Log or inspect the prop/state values
   passed to the component.
4. Check **conditional rendering logic** — is the component conditionally shown
   based on a value that is unexpectedly falsy?
5. For React/Vue/Svelte: check whether the component re-renders when expected
   and whether the correct values are passed down through props/context.

**Common sources:**
- CSS specificity conflict (a more specific rule overrides your intent)
- Wrong `z-index` stacking context
- Flexbox / Grid axis confusion (`flex-direction`, `align-items` vs. `justify-content`)
- Component not re-rendering because prop reference is the same (shallow equality)
- `v-if` / conditional prop evaluating the wrong falsy value (0, "", null, undefined)
- Missing `key` prop on a list causing identity confusion during reconciliation
- Global CSS reset or third-party stylesheet overriding base styles

---

### Auth / Session Bugs

**Signals:** Unexpected 401/403, user logged out unexpectedly, wrong permissions
applied, token expiry issues, CSRF failures.

**Investigation order:**
1. Inspect the actual request in the browser Network tab. What auth header or
   cookie is being sent? Is the token present?
2. Decode the JWT (use jwt.io offline) — check `exp`, `iat`, `sub`, `aud`, and
   any custom claims. Is it valid? Is it expired?
3. Verify the token is being stored and retrieved correctly (correct cookie name,
   correct localStorage key, correct header format: `Bearer <token>`).
4. Check the **server-side validation logic** — is the token being verified against
   the correct secret/public key? Is the audience check correct?
5. Check CORS headers if auth fails cross-origin. `Authorization` headers require
   explicit `Access-Control-Allow-Headers` permission.
6. Check session store (Redis, DB) — is the session present? Is it expired?

**Common sources:**
- Token sent in wrong format (missing `Bearer ` prefix)
- Token not refreshed before expiry
- Cookie not sent on cross-origin requests (missing `SameSite=None; Secure`)
- JWT secret mismatch between issuer and validator
- Role/permission check inverted (`if (!hasRole)` where `if (hasRole)` intended)
- Middleware order: auth middleware not applied before the protected route

---

### Network / API Bugs

**Signals:** HTTP errors (400, 401, 403, 404, 422, 429, 500, 502, 503),
network timeouts, CORS errors, unexpected response shape, missing data.

**Investigation order:**
1. Open the browser Network tab. Find the failing request. Read:
   - Request URL (is it correct?)
   - Request method (GET/POST/etc. — correct?)
   - Request headers (Authorization, Content-Type, etc.)
   - Request body (is it being serialized correctly?)
   - Response status
   - Response body (read the full error message from the server)
2. Replicate the failing request with `curl` or a tool like HTTPie to isolate
   frontend vs. backend.
3. Check server logs for the exact request received and the error generated.
4. Verify the **Content-Type** header matches the body format.
5. For 429 (rate limit): check retry logic and backoff.
6. For CORS: the error is always on the preflight OPTIONS request or the
   actual request response headers — not in the client code.

**Common sources:**
- Base URL misconfigured (wrong env, trailing slash mismatch)
- JSON body not serialized (`fetch` requires `JSON.stringify` + `Content-Type: application/json`)
- CORS: missing `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, or `Access-Control-Allow-Headers`
- API expects query params but client sends body (or vice versa)
- Endpoint not registered / wrong HTTP method
- Paginated API — caller assumes all data in first response

---

### Build / Test Failures

**Signals:** Compilation error, type error, failing unit/integration/e2e test,
CI pipeline failure, import resolution error.

**Investigation order:**
1. Read the full error output. Compiler and bundler errors are usually precise.
   Do not paraphrase — read the exact message.
2. For TypeScript errors: identify the inferred type vs. the expected type.
   Do not add `as any` — understand why they differ.
3. For import errors: check that the module exists, the path is correct
   (case-sensitive on Linux), and the export name matches the import name.
4. For failing tests: read the assertion failure — expected vs. received.
   Reproduce the test in isolation (`--testNamePattern`, `it.only`, `pytest -k`).
5. For CI-only failures: diff the CI environment from local (Node version, env vars,
   OS, installed system packages). Check if the CI cache is stale.

**Common sources:**
- Type mismatch introduced by a dependency update
- Circular import (module A imports B, B imports A)
- Test relies on global state mutated by a previous test (test order dependency)
- Mock not reset between tests
- Snapshot test not updated after intentional UI change
- Incorrect `tsconfig.json` path aliases or `moduleResolution`
- ESM/CJS interop issues (mixing `import` and `require`)

---

### Database Bugs

**Signals:** Query error, missing records, duplicate records, constraint violation,
migration failure, deadlock, slow query.

**Investigation order:**
1. Run the failing query directly against the database. Read the exact error.
2. Check the **migration state** — are all migrations applied? Is the schema
   what the application expects?
3. For missing data: check whether the record was ever inserted. Verify
   filters (especially soft deletes — `WHERE deleted_at IS NULL` may be excluding it).
4. For constraint violations: identify which constraint and on which column.
   The error message names it.
5. For slow queries: run `EXPLAIN ANALYZE` (PostgreSQL) or `EXPLAIN` (MySQL)
   to see the query plan. Check for sequential scans on large tables.
6. For deadlocks: check the DB error log for the deadlock graph. Identify
   which transactions are competing for the same rows and in what order.

**Common sources:**
- Soft-deleted records not excluded from queries
- N+1 query pattern (missing `JOIN` or eager load)
- Missing index on a filtered column
- Incorrect transaction scope (autocommit assumed, but not set)
- Schema drift between migration state and ORM model
- Timestamp timezone mismatch (storing in UTC, displaying without conversion,
  or vice versa)
- ORM caching stale data (use `reload`, `refresh_from_db`, or equivalent)

---

## Diagnostic Toolkit

Quick-reference commands for common investigation tasks.

### Logging

Always prefer **structured logs** (JSON) over interpolated strings in server-side code.
Add temporary debug logs at **boundaries** — inputs and outputs of functions,
not inside tight loops.

Remove temporary debug logs before committing. Use a task comment:
```
// TODO: remove debug log
console.log('[DEBUG] user payload:', payload);
```

### Network Inspection

```bash
# Replicate a request with curl (preserves headers)
curl -X POST https://api.example.com/endpoint \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' \
  -v   # verbose: shows request/response headers

# Test connectivity
curl -I https://api.example.com/health

# Decode JWT without external tools
echo "<token>" | cut -d '.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

### Database Diagnostics

```sql
-- PostgreSQL: explain a slow query
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

-- PostgreSQL: find missing indexes (sequential scans on large tables)
SELECT relname, seq_scan, idx_scan
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;

-- PostgreSQL: check active locks
SELECT pid, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE wait_event IS NOT NULL;

-- Check migration state (Prisma)
npx prisma migrate status

-- Check migration state (Django)
python manage.py showmigrations

-- Drizzle: check schema diff
npx drizzle-kit check
```

### Process & System

```bash
# Node.js: check process memory
node --max-old-space-size=4096 app.js  # set heap limit
process.memoryUsage()                  # in REPL or debug log

# Find what is listening on a port
lsof -i :3000
ss -tlnp | grep 3000

# Check environment variables actually set
printenv | grep APP_
env | grep DATABASE_

# Tail logs from a running service
journalctl -u myservice -f
docker logs -f <container_id>
```

### Git Bisect (regression locating)

When a bug was introduced by an unknown commit:

```bash
git bisect start
git bisect bad                    # current commit is bad
git bisect good <last-known-good-sha>
# Git checks out a midpoint commit. Test it, then:
git bisect good   # or git bisect bad
# Repeat until git identifies the introducing commit
git bisect reset  # cleanup
```

### Dependency Debugging

```bash
# Node.js: check for duplicate/conflicting versions
npm ls <package-name>
npx npm-why <package-name>

# Python: check what is installed
pip show <package>
pip check   # check for dependency conflicts

# Check for known vulnerabilities
npm audit
pip-audit
```

---

## Decision Trees

### "It works locally but not in production"

```
Is the error a missing env var or wrong value?
  → Yes: Diff env vars. Add startup validation for required vars.
  → No: Is it a dependency version mismatch?
      → Yes: Lock versions. Align package-lock.json / poetry.lock between envs.
      → No: Is it a file path or permission issue?
          → Yes: Check absolute paths, file permissions, working directory.
          → No: Is it a build artifact mismatch?
              → Yes: Clear build cache. Rebuild from clean state.
              → No: Add environment-specific logging. Compare DB/service state.
```

### "The test was passing, now it fails"

```
Did I change the code under test?
  → Yes: Read the assertion. Is my change intentionally different?
      → Yes: Update the test to reflect the new contract.
      → No: My change broke something unintentionally. Revert or fix.
  → No: Did a dependency change?
      → Yes: Check changelog. Adapt to new API.
      → No: Does the test depend on order or global state?
          → Yes: Isolate the test. Add setup/teardown to reset state.
          → No: Is it a flaky timing issue?
              → Yes: Add proper async handling or increase timeout carefully.
```

### "The API returns 500 with no useful message"

```
Check server logs immediately — the real error is there.
If no logs: add error logging middleware that catches and logs all unhandled errors.
If logs show DB error: run the query manually. Check migration state.
If logs show undefined/null error: add input validation at the route handler.
If logs show external service error: check connectivity and credentials.
```

---

## Anti-Patterns

Do not do any of the following:

**Do not add `try/catch` that swallows errors silently.**
```js
// WRONG — hides failures, makes debugging impossible later
try { doThing(); } catch (e) { /* ignore */ }

// CORRECT — log and re-throw, or handle with intent
try { doThing(); } catch (e) { logger.error('doThing failed', e); throw e; }
```

**Do not use `as any` in TypeScript to silence a type error.**
A type error is the compiler telling you the types don't match. Understand why.
Casting it away leaves the actual mismatch unresolved.

**Do not comment out failing tests.** A commented-out test is a deleted test.
If the test reveals a real bug, fix the bug. If the test is wrong, fix the test.

**Do not add `time.sleep()` or `setTimeout()` to fix race conditions.**
This is a symptom-level patch. Find the actual race: missing `await`, incorrect
event order, missing synchronization primitive.

**Do not run `DROP TABLE` or `DELETE` without a backup in any non-local environment.**
Ever.

**Do not guess at a fix without understanding the cause.**
A guess that works is a fix with an unknown contract — it may break again under
different conditions, and you will not know why.

---

## Output Standards

When reporting a bug investigation, structure the output as:

```
## Bug Report

**Symptom:** [What the user or system observed]
**Root Cause:** [The specific code/config/state causing it]
**Affected:** [Component, service, or code path]
**Reproduces On:** [Environments, conditions]

## Fix Applied

[Description of the change and why it resolves the root cause]

## Verification

[How the fix was confirmed — test run output, manual steps, etc.]

## Regression Test

[Test added, or reason one was not added]

## Follow-Up

[Any systemic issues identified that warrant a separate ticket]
```

---

## Escalation Signals

Stop and flag for human review when:

- The bug involves **data loss or corruption** in a non-local environment.
- The fix requires a **destructive database operation** (schema drop, bulk delete,
  data migration in production).
- The root cause is **inside a dependency** and requires a patch, fork, or workaround
  that diverges from upstream.
- The bug is a **security vulnerability** (auth bypass, injection, data exposure).
- After three distinct hypotheses have been tested and none explains the behavior.

In these cases, report what has been found so far and what remains unexplained.
Do not continue modifying code.
