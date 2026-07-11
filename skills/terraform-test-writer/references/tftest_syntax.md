# `.tftest.hcl` syntax reference

Native Terraform testing (v1.6+) lives in files ending `.tftest.hcl`, conventionally placed in a `tests/` directory at the root of the module, or alongside the module they test.

## Top-level structure

```hcl
# tests/main.tftest.hcl

variables {
  bucket_prefix = "test-bucket"
}

provider "aws" {
  region = "us-west-2"
}

run "bucket_exists_with_encryption" {
  command = plan

  assert {
    condition     = aws_s3_bucket_server_side_encryption_configuration.example.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm == "AES256"
    error_message = "S3 bucket must use AES256 encryption by default"
  }
}

run "bucket_versioning_enabled" {
  command = apply

  assert {
    condition     = aws_s3_bucket_versioning.example.versioning_configuration[0].status == "Enabled"
    error_message = "S3 bucket must have versioning enabled"
  }
}
```

A file can contain many `run` blocks. They execute in order, top to bottom, and by default each accumulates state from previous `run` blocks in the same file (useful for multi-step scenarios — e.g., a resource created in `run "setup"` can be referenced in a later `run` block). Use `variables` at the top level for defaults shared across all `run` blocks; each `run` block can override with its own `variables {}` block.

## `command`: plan vs apply

- `command = plan` — runs `terraform plan`, checks assertions against the plan output. Fast, no real resources created. Use this whenever the assertion only needs to check *configuration* (attribute values, references, whether a resource would be created) rather than a value only known after creation (e.g., a generated ARN, an auto-assigned ID).
- `command = apply` — actually creates resources (real or mocked, see below), then checks assertions against applied state. Necessary when the assertion depends on a computed value, or you're testing that resources interact correctly at runtime. Slower and, if using real providers, costs real money/time.

Default to `plan` wherever it's sufficient — most schema/attribute assertions don't need real resources. Reach for `apply` when testing cross-resource wiring that only resolves after creation, or when using `override_resource` to mock expensive dependencies while still applying the resource actually under test.

## `assert` blocks

```hcl
assert {
  condition     = <boolean expression referencing resources/outputs>
  error_message = "<human-readable explanation, ideally interpolating the actual value>"
}
```

A `run` block can have multiple `assert` blocks — each checks one condition. Prefer several focused asserts with clear individual error messages over one large `&&`-chained condition, since a failure in the latter tells you *that* something's wrong but not *which* part.

Reference resources the same way you would in the module under test: `aws_s3_bucket.example.bucket`, `aws_lambda_function.processor.runtime`, etc. Reference module outputs the same way you'd reference them from a caller: `output.some_output_name`.

## `variables` blocks

Override any input variable the module accepts, either at file scope (applies to all `run` blocks) or inside a specific `run` block (applies to that block only, overriding file-scope values of the same name). Use this to parameterize test scenarios — e.g., testing the same module with `environment = "prod"` in one `run` block and `environment = "dev"` in another, to check environment-conditional logic actually branches correctly.

## `expect_failures` — negative testing

```hcl
run "rejects_invalid_bucket_name" {
  command = plan

  variables {
    bucket_name = "InvalidName-With-Caps"
  }

  expect_failures = [
    var.bucket_name,
  ]
}
```

This checks that a `validation` block on the referenced variable (or a resource precondition/postcondition) actually triggers and blocks the plan. This is the mechanism for testing "does this correctly reject bad input" — don't just write assertions for the happy path. If the module has any `validation` blocks in its variable declarations, there should be a corresponding `expect_failures` test confirming the validation actually fires for the case it's meant to catch, not just that it exists.

## `override_resource` and `override_module` — mocking

```hcl
run "test_with_mocked_rds" {
  command = apply

  override_resource {
    target = aws_db_instance.backend
    values = {
      id       = "mock-db-id"
      endpoint = "mock-endpoint:5432"
    }
  }

  assert {
    condition     = aws_lambda_function.processor.environment[0].variables["DB_ENDPOINT"] == "mock-endpoint:5432"
    error_message = "Lambda must receive the DB endpoint via environment variable"
  }
}
```

`override_resource` replaces a specific resource with computed mock values instead of actually provisioning it — use this for anything slow or expensive that isn't the direct subject of the current test but that other resources depend on. `override_module` does the same at the module level, useful when a child module is a dependency but not what's under test. See `references/mocking_and_cost.md` for when this matters most.

## `mock_provider` — full provider mocking

For running tests with no real cloud calls at all (fastest, but least representative of real behavior), an entire provider can be mocked:

```hcl
mock_provider "aws" {}
```

This is useful for pure logic/wiring tests where you don't need the provider to actually validate anything against a real account — good for CI runs that shouldn't require live cloud credentials at all.

## Running tests

```bash
terraform test                    # human-readable output
terraform test -json              # structured output, useful for parsing programmatically
terraform test -filter=tests/main.tftest.hcl   # run a specific file
```

`terraform init` must be run first, same as any other Terraform workflow.
