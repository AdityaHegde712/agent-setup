# Mocking and cost management

The point of good test coverage is that it gets run often — ideally on every push, via CI. That only stays true if tests are fast and cheap enough that nobody starts skipping them. Mocking is the main lever for that.

## When to mock

Mock (via `override_resource`, `override_module`, or `mock_provider`) anything that is:

- **Slow to provision** — RDS instances (minutes), NAT gateways, EKS clusters — and isn't the direct subject of the current test.
- **Expensive** — anything billed per-hour-provisioned rather than per-request, especially if a test suite runs many times a day in CI.
- **A dependency, not the target** — if a test's job is to confirm a Lambda's environment variables are wired correctly, it doesn't need a real RDS instance behind those variables; it needs the *value* of the endpoint to be correct, which a mock provides just as well.

Don't mock the resource actually under test — that would make the test meaningless (you'd be asserting against a value you told the mock to have, not a value Terraform computed).

## `override_resource` pattern

```hcl
run "lambda_gets_correct_db_endpoint" {
  command = apply

  override_resource {
    target = aws_db_instance.backend
    values = {
      id       = "mock-db-id"
      endpoint = "mock-endpoint.example.com:5432"
    }
  }

  assert {
    condition     = aws_lambda_function.processor.environment[0].variables["DB_ENDPOINT"] == "mock-endpoint.example.com:5432"
    error_message = "Lambda must receive the mocked DB endpoint via its DB_ENDPOINT env var"
  }
}
```

The mocked resource still "exists" in the test's state for reference purposes — other resources can depend on it and read its (mocked) attributes — but Terraform never actually calls the provider API to create it.

## `mock_provider` for fully offline tests

```hcl
mock_provider "aws" {}
```

Use this when a whole test file only needs to check wiring/logic (references between resources, variable propagation, conditional expressions) and doesn't need any real attribute values computed by AWS. These tests run with no cloud credentials needed at all, which also makes them safe to run in contexts (like a public CI job on a fork) where real credentials shouldn't be exposed.

## A practical split for a growing test suite

As the pipeline grows (S3 → SQS → DynamoDB → compute), it's usually worth splitting test files roughly along these lines:

- **Fast, offline, `plan`-only, heavily mocked** — run on every commit. Checks schema/attribute correctness and basic wiring.
- **Slower, `apply`, selectively mocked** — run pre-merge or nightly. Checks that resources actually come up correctly together, with expensive dependencies (RDS, etc.) still mocked but the resources under test actually created.
- **Full integration (if ever needed)** — real deploy to a sandboxed/ephemeral environment, minimal mocking. Reserve for the few scenarios that genuinely need to observe real runtime behavior (see `references/terratest_escalation.md`) — this tier is expensive enough that it shouldn't run on every push.

This tiering keeps the fast feedback loop fast while still having somewhere for the handful of tests that genuinely need to be slow and real.
