---
name: terraform-test-writer
description: Writes native Terraform test files (.tftest.hcl, Terraform v1.6+) that verify infrastructure-as-code meets a set of stated requirements, before or instead of running terraform apply against real cloud resources. Use this whenever the user has a PLAN.md, architecture doc, or set of feature/system requirements for infrastructure and needs test coverage written against it — even if they don't say the word "test" explicitly, e.g. "make sure this Terraform config actually does what the plan says", "write assertions for my S3-to-Lambda pipeline", "how do I verify this SQS/DynamoDB setup works before deploying", "TDD this Terraform module", or "check that IAM roles are scoped correctly". Also use for reviewing/extending existing .tftest.hcl files, debugging failing terraform test output, or deciding between native terraform test and Terratest for a given scenario. Agent-agnostic: works whether the user is driving directly or orchestrating this as one step in a larger multi-agent pipeline (e.g. an Architect agent producing a PLAN.md that this skill consumes).
---

# Terraform Test Writer

## The idea in one sentence

Given a description of what infrastructure is *supposed* to do (a PLAN.md, a requirements doc, or just a conversation), write `.tftest.hcl` files that fail until the Terraform config actually does that — this is TDD applied to infrastructure.

## Why native `terraform test`, not Terratest

Terraform v1.6+ ships a built-in test runner that reads `.tftest.hcl` files, spins up real (or mocked) resources in an ephemeral state, checks `assert` blocks against that state, and tears everything down automatically. For someone building this alongside a Terraform config, this is the right default because:

- It's HCL — no separate Go toolchain or test framework to learn on top of Terraform itself.
- Cleanup is automatic. You don't have to remember to destroy test resources; the test runner does it, which matters a lot when you're still building intuition for what "leaves resources running" even looks like.
- It's designed for exactly this shape of problem: assert facts about planned or applied state.

Reach for **Terratest** (a Go library) only when a test needs to do something native `terraform test` genuinely can't: making real HTTP requests against a deployed endpoint to check runtime behavior, orchestrating multi-cloud scenarios, or asserting on side effects outside Terraform's own state (e.g., "did the Lambda actually process the SQS message and write the right row to DynamoDB"). If a test case needs this, say so explicitly and write it as a documented gap rather than silently switching frameworks — see `references/terratest_escalation.md`.

## Input: what you're working from

Usually this is one of:

1. **A PLAN.md or architecture doc** — a set of feature/system requirements written by a human or an Architect agent, describing what the infrastructure should provide (e.g., "S3 bucket triggers SQS on upload, Lambda drains the queue with a DLQ after 3 failures, results land in DynamoDB with the source key as partition key").
2. **An existing Terraform config** (`.tf` files) with no tests yet.
3. **A vague ask** ("write tests for my pipeline") — in this case, read the actual `.tf` files first; the resources, variables, and outputs already declared are the ground truth for what's testable. Don't invent requirements that aren't grounded in either the plan doc or the code.

If both a plan doc and existing `.tf` files are available, treat the plan doc as the source of *intent* (what "correct" means) and the `.tf` files as the source of *shape* (what resources/attributes actually exist to assert against). Mismatches between the two are worth surfacing to the user before writing tests — testing against a plan the code doesn't yet implement is fine (that's the point of TDD), but testing against attributes that don't exist in the code will just produce broken HCL.

## Coverage checklist — what "as much coverage as possible" means concretely

Rather than writing tests until it feels thorough, work through these categories explicitly for each resource or wiring point in scope. Not every category applies to every resource — a standalone S3 bucket has no cross-resource wiring to test — but scan the list rather than stopping at the first passing assertion.

1. **Schema/attribute assertions** — does the resource have the configuration the plan requires (encryption enabled, versioning on, correct runtime version, correct instance type)? This is the most basic layer and usually the first thing to write.
2. **Cross-resource wiring** — do the connections between services actually hold together? IAM role attached to the right resource with the right permissions, event source mappings pointing at the right queue/topic, security groups allowing the specific traffic that's needed (and not more).
3. **Security posture** — least-privilege IAM (no wildcard actions/resources unless explicitly required), encryption at rest and in transit where applicable, no public access on things that shouldn't be public. This overlaps with #1/#2 but is worth a deliberate pass since it's the category most likely to be silently wrong.
4. **Negative/failure-mode tests** — does the config correctly reject or handle bad input? E.g., a `run` block with `expect_failures` confirming a variable validation rule actually blocks an invalid value. These are the tests people skip, and they're often what catches a misconfigured validation block.
5. **Cost-conscious mocking** — for resources that are expensive or slow to actually provision (RDS, NAT gateways, large EC2 fleets) and aren't the direct subject of the test, use `override_resource` / `mock_provider` so the test suite stays fast and cheap. See `references/mocking_and_cost.md`.

Walk the plan doc's requirements one at a time and map each to at least one assertion; that mapping is worth showing the user (see Output below) so they can see nothing was silently dropped.

## Workflow

### 1. Establish what's being tested

Read the plan doc and/or `.tf` files. Build a short list: "resources in scope" and "requirements to verify," pairing each requirement with the resource(s) it touches. For anything genuinely ambiguous (the plan says "logging enabled" but doesn't say CloudWatch vs S3 access logs), ask rather than guessing — a wrong assumption here produces a test that passes without checking what the user actually cares about.

### 2. Structure the test file(s)

One `.tftest.hcl` per module or logical unit is usually right — don't cram an entire multi-service pipeline into one file if it maps cleanly to separate modules. Within a file, order `run` blocks so cheaper/foundational checks run first (e.g., "bucket exists with correct name" before "bucket triggers land in the right queue") — an early failure then tells you the base resource is wrong before you waste time on wiring that depends on it.

Read `references/tftest_syntax.md` for the concrete HCL structure (`run`, `assert`, `variables`, `provider`, `override_resource`, `expect_failures`) — don't guess at syntax from memory, the block structure has specific rules (e.g., `command = plan` vs `command = apply` changes what's available to assert against).

### 3. Write assertions with error messages that teach

Every `assert` needs an `error_message` that states what was expected and, ideally, interpolates the actual value, so a test failure is immediately diagnostic rather than requiring a re-read of the HCL to understand what went wrong. Since the person driving this may not have deep Terraform fluency yet, favor error messages that explain the *requirement* in plain terms, not just the technical condition.

### 4. Apply security and isolation checkpoints

Before finalizing, check the generated HCL against `references/security_checkpoints.md`: no hardcoded credentials (only `var.*` or environment-sourced values), randomized/unique naming to avoid collisions with real resources, and explicit teardown expectations where the test runner's automatic cleanup might not be enough (e.g., resources with deletion protection).

### 5. Map coverage back to requirements

Before handing back the test file(s), produce a compact table: requirement → `run` block name. Two columns, one line per requirement — this is a scan-and-confirm artifact, not documentation, so resist the urge to add a category column or explanatory prose per row. Only break this pattern to flag something *not* covered (e.g., a requirement needing Terratest instead) — that's worth a short separate note, not a table row.

## Output

Produce:
- The `.tftest.hcl` file(s), ready to run with `terraform test`.
- The requirement-to-assertion coverage table from step 5.
- A short note on anything explicitly out of scope for native `terraform test` (i.e., needs Terratest or manual verification post-deploy), per `references/terratest_escalation.md` — don't leave this implicit.

## Reference files

- `references/tftest_syntax.md` — concrete `.tftest.hcl` block syntax and semantics (`run`, `assert`, `variables`, `command = plan|apply`, `expect_failures`, `override_resource`, `override_module`, `provider` blocks). Read this before writing any HCL.
- `references/aws_assertion_patterns.md` — ready-to-adapt assertion patterns for S3, SQS, DynamoDB, Lambda, EC2/ECS/Fargate, and IAM — the services in a typical event-driven AWS pipeline. Read this when writing assertions for any of these services rather than deriving attribute paths from scratch.
- `references/security_checkpoints.md` — credential handling, naming/isolation, and cleanup rules to check every generated test file against.
- `references/mocking_and_cost.md` — when and how to use `override_resource`/`mock_provider` to keep test runs fast and cheap.
- `references/terratest_escalation.md` — the specific, narrow set of cases where native `terraform test` isn't enough and Terratest (or manual post-deploy verification) is the honest answer.
