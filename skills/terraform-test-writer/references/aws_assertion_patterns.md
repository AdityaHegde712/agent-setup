# AWS assertion patterns by service

Ready-to-adapt patterns for the services that show up most in an event-driven, S3 → SQS → DynamoDB → compute (EC2/ECS/Fargate/Lambda) pipeline. These are starting points — adapt resource names to match the actual `.tf` config, and always check the attribute path against the current AWS provider's schema if there's any doubt (provider versions do change attribute shapes).

## S3

```hcl
# Encryption
assert {
  condition     = aws_s3_bucket_server_side_encryption_configuration.example.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm == "AES256"
  error_message = "Bucket must use AES256 (or aws:kms) server-side encryption by default"
}

# Versioning
assert {
  condition     = aws_s3_bucket_versioning.example.versioning_configuration[0].status == "Enabled"
  error_message = "Bucket must have versioning enabled to protect against accidental overwrite/delete"
}

# Public access block (security posture)
assert {
  condition     = aws_s3_bucket_public_access_block.example.block_public_acls == true
  error_message = "Bucket must block public ACLs — this bucket should never be publicly readable"
}

# Event notification wiring to SQS
assert {
  condition     = aws_s3_bucket_notification.example.queue[0].queue_arn == aws_sqs_queue.ingest.arn
  error_message = "S3 bucket notification must target the ingest SQS queue, not some other queue"
}
```

## SQS

```hcl
# Dead-letter queue configured
assert {
  condition     = jsondecode(aws_sqs_queue.ingest.redrive_policy)["maxReceiveCount"] == 3
  error_message = "Queue must route to DLQ after 3 failed receives"
}

assert {
  condition     = jsondecode(aws_sqs_queue.ingest.redrive_policy)["deadLetterTargetArn"] == aws_sqs_queue.ingest_dlq.arn
  error_message = "Queue's redrive policy must point at the dedicated DLQ, not itself or another queue"
}

# Visibility timeout sane relative to Lambda timeout (common misconfiguration)
assert {
  condition     = aws_sqs_queue.ingest.visibility_timeout_seconds >= aws_lambda_function.processor.timeout
  error_message = "Queue visibility timeout must be >= Lambda function timeout, or messages can be redelivered mid-processing"
}
```

## DynamoDB

```hcl
# Partition key matches the plan's stated design
assert {
  condition     = aws_dynamodb_table.results.hash_key == "source_key"
  error_message = "Table partition key must be source_key per the design doc"
}

# Point-in-time recovery / backups
assert {
  condition     = aws_dynamodb_table.results.point_in_time_recovery[0].enabled == true
  error_message = "Table must have point-in-time recovery enabled"
}

# Billing mode matches expected cost model
assert {
  condition     = aws_dynamodb_table.results.billing_mode == "PAY_PER_REQUEST"
  error_message = "Table should use on-demand billing unless a specific capacity plan was agreed"
}
```

## Lambda

```hcl
# Runtime matches what the plan specifies
assert {
  condition     = aws_lambda_function.processor.runtime == "python3.12"
  error_message = "Lambda runtime must be python3.12 per the design doc"
}

# Event source mapping wired to the correct queue
assert {
  condition     = aws_lambda_event_source_mapping.from_sqs.event_source_arn == aws_sqs_queue.ingest.arn
  error_message = "Lambda's event source mapping must point at the ingest queue"
}

# IAM: Lambda execution role actually has the permission it needs (see IAM section below for the general pattern)
```

## EC2 / ECS / Fargate

```hcl
# ECS task uses Fargate launch type where the plan calls for serverless compute
assert {
  condition     = aws_ecs_service.processor.launch_type == "FARGATE"
  error_message = "Service must run on Fargate, not EC2-backed ECS, per the design doc"
}

# Task definition CPU/memory within expected bounds (cost/perf sanity check)
assert {
  condition     = tonumber(aws_ecs_task_definition.processor.cpu) <= 1024
  error_message = "Task CPU allocation exceeds the 1 vCPU budget specified in the plan"
}

# Networking: task can actually reach dependencies (security group egress)
assert {
  condition     = contains(aws_security_group.ecs_tasks.egress[*].to_port, 443)
  error_message = "ECS task security group must allow outbound 443 to reach AWS APIs (SQS, DynamoDB)"
}
```

## IAM — the pattern that matters most across every service above

The recurring failure mode across all of these services isn't the resource itself — it's the IAM policy that's supposed to connect them being wrong (wildcard actions, wrong resource ARN, or just missing the one action that's needed). Test IAM policies by decoding the policy document and checking for the specific action/resource pair, not just that a policy exists:

```hcl
run "lambda_can_receive_from_sqs" {
  command = plan

  assert {
    condition = anytrue([
      for stmt in jsondecode(aws_iam_role_policy.lambda_exec.policy).Statement :
      contains(stmt.Action, "sqs:ReceiveMessage") && contains(stmt.Resource, aws_sqs_queue.ingest.arn)
    ])
    error_message = "Lambda execution role must have sqs:ReceiveMessage scoped to the ingest queue ARN"
  }
}

# Negative check: make sure the policy ISN'T overly broad
assert {
  condition = !anytrue([
    for stmt in jsondecode(aws_iam_role_policy.lambda_exec.policy).Statement :
    contains(stmt.Action, "*") || contains(stmt.Resource, "*")
  ])
  error_message = "Lambda execution role must not use wildcard actions or resources — scope permissions explicitly"
}
```

This pair (positive: has exactly the permission needed; negative: doesn't have more than that) is worth writing for every IAM role in the pipeline, not just Lambda's.
