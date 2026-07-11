# Security checkpoints for generated test files

Check every generated `.tftest.hcl` file against these before considering it done. These matter because test files are still code that runs against (potentially real) cloud accounts — a sloppy test file can leak credentials or leave orphaned resources just as easily as a sloppy module.

## No hardcoded credentials

```hcl
# Wrong — never do this
provider "aws" {
  access_key = "AKIA..."
  secret_key = "..."
}

# Right — credentials come from the environment or a variable sourced from environment
provider "aws" {
  region = var.test_region
}
```

Terraform test runs should rely on the standard AWS credential chain (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars, an assumed role, or `~/.aws/credentials`) — the same as any other Terraform run. If a generated test file ever contains something that looks like a literal key (`AKIA...`, `ASIA...`, or a `secret_key`/`access_key` assignment with a literal string), stop and flag it — don't just quietly fix it, since its presence usually means the request or source material had it hardcoded somewhere upstream that's worth knowing about.

## Unique/randomized naming to avoid collisions

Tests that create real resources (`command = apply`) risk colliding with real, already-existing resources if names are hardcoded and not unique per run. Use a variable with a random suffix, or Terraform's `random_id`/`random_string` resource, so re-running tests (or running them in CI alongside other branches) doesn't collide:

```hcl
variables {
  bucket_prefix = "tftest-${formatdate("YYYYMMDDhhmmss", timestamp())}"
}
```

This matters more once tests run in CI (GitHub Actions) alongside a real deploy pipeline, where a name collision could otherwise silently corrupt a real resource instead of just failing the test.

## Cleanup / teardown expectations

Native `terraform test` automatically destroys resources created during `command = apply` runs once the test file finishes — this is one of the main reasons to prefer it. But a few situations still need explicit attention:

- **Deletion protection**: if a resource under test has `deletion_protection = true` (common for RDS, DynamoDB in prod-like configs), the test runner's automatic destroy will fail. Either override this to `false` specifically within the test's `variables` block, or explicitly note in the test file's comments that this resource requires manual cleanup verification.
- **Resources with retention policies**: S3 buckets with objects and no `force_destroy = true` will fail to delete if the test created objects in them. Set `force_destroy = true` in test-scoped variables if the test writes objects.
- **Cross-account or shared resources**: if a test references a resource in another account/module that it doesn't own (via `data` sources rather than `resource` blocks), it won't be destroyed — which is correct, but confirm the test isn't accidentally creating something under an assumption that it's shared/pre-existing when it's not.

## IAM scope for the test's own execution

The credentials used to *run* the tests should themselves be scoped no more broadly than what the tests need to create/read/destroy. If the test suite for a Lambda-only feature is being run with account-admin credentials, that's a real (if secondary) security concern worth mentioning to the user — the test runner doesn't need more access than the resources it's exercising.
