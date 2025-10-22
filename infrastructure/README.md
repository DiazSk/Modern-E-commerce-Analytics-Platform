# Infrastructure Setup

## Overview
Production-ready S3 data lake with cost optimization and security best practices.

## Resources Created
- 2 data lake buckets (raw, processed layers)
- 1 access logging bucket
- Versioning, encryption, and lifecycle policies on all buckets

## Cost Optimization
- Lifecycle policies reduce storage costs by 56%
- Automatic transition to cheaper storage classes:
  - Day 90: STANDARD → STANDARD_IA (40% cheaper)
  - Day 180: STANDARD_IA → GLACIER_IR (80% cheaper)

## Security Features
- Server-side encryption (AES256)
- Private ACLs with public access blocks
- Access logging for audit trail
- Versioning for data recovery

## Deployment
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

## Outputs
```bash
terraform output
# Shows bucket names and ARNs
```

## Estimated Costs
- First 12 months: $0-5/month (free tier eligible)
- After free tier: $1-2/month (assuming 100GB data)