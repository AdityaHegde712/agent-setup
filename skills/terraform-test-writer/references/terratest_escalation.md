# When native `terraform test` isn't enough

Native `terraform test` covers the large majority of infrastructure test needs — anything that can be phrased as "given this config, does the planned or applied Terraform state have this property." It falls short in a specific, narrow set of cases. Recognize these rather than trying to force a native test to do something it structurally can't, and say so explicitly in the output rather than silently omitting coverage.

## Genuine gaps

1. **Runtime/behavioral verification after deploy.** Native tests check *Terraform's* state — resource attributes, references, computed values. They can't make an HTTP request to a deployed API Gateway endpoint and check the response body, or actually invoke a Lambda and check its return value against sample input. If "does the pipeline actually process a message correctly end-to-end" is the question, that's a runtime test, not an infrastructure-state test.

2. **Multi-step orchestration across apply cycles with real external interaction.** E.g., "deploy the infra, upload a real file to S3, wait for the Lambda to process it, then check DynamoDB has the right row" is a real integration test against live AWS behavior, not just Terraform state — Terratest (or a plain script using the AWS SDK) is the honest tool here.

3. **Testing across multiple independent Terraform configurations/workspaces that don't share a test file's state.** Native tests operate within one module's test context; cross-stack integration (e.g., "the VPC stack and the app stack actually connect correctly when both are deployed") is more naturally a Terratest scenario or a manual verification step.

## What to do when a requirement falls into one of these gaps

Don't quietly drop the requirement or force a native `assert` to approximate it (e.g., don't try to fake a runtime check by asserting on a static Lambda attribute that only weakly implies the runtime behavior is correct — that produces a false sense of coverage). Instead:

- Note the requirement explicitly in the coverage table as "not covered by native tests."
- Suggest the specific Terratest pattern or manual verification step that would cover it, so the user (or a downstream agent) can decide whether it's worth the added tooling.
- If the user wants, sketch the Terratest Go test structure — it follows a familiar shape (`terraform.InitAndApply`, make an assertion via the AWS SDK or an HTTP call, `defer terraform.Destroy`) — but this is a bigger lift (needs a Go toolchain and test file) and shouldn't be reached for by default.

## Minimal Terratest shape, for reference

```go
func TestLambdaProcessesMessageEndToEnd(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../infra",
    }
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Real interaction: upload to S3, wait, check DynamoDB
    bucketName := terraform.Output(t, terraformOptions, "bucket_name")
    // ... upload test file via AWS SDK, poll DynamoDB for the expected row ...
}
```

This is intentionally minimal — the point is recognizing the shape, not memorizing Terratest's full API surface. Most pipelines will never need this tier of testing for most requirements.
