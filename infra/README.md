# Infrastructure

Terraform/OpenTofu skeleton deploying the ingestion Lambda on a schedule (EventBridge).

```bash
make lambda-zip
cd infra/terraform
tofu init
tofu plan -var "database_url=..." -var "pandascore_token=..."
```

Status: skeleton, not applied yet. Planned next: remote state (S3 + DynamoDB lock),
secrets in SSM Parameter Store, one tfvars per environment (dev / staging / prod),
RDS or Neon for Postgres, API on Lambda (Mangum) or ECS.
