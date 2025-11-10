# ========================================
# E-Commerce Data Lake Infrastructure
# ========================================
# This Terraform configuration creates a production-ready
# S3-based data lake with proper security, versioning,
# lifecycle management, and cost optimization.
# ========================================


# Configure the Terraform AWS provider and create S3 buckets for a data lake
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  required_version = ">= 1.2.0"
}

# ========================================
# Provider Configuration
# ========================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform"
    }
  }
}

# ========================================
# Provider Alias for us-east-1 (Billing/CloudWatch)
# ========================================
# Billing metrics and alarms MUST be created in us-east-1
# This is an AWS requirement - billing data is only available there

provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform"
    }
  }
}


# ========================================
# Random Suffix for Global Bucket Uniqueness
# ========================================
# S3 bucket names must be globally unique across all AWS accounts.
# This random suffix ensures no naming conflicts.

# Single random string resource to ensure both buckets have a unique suffix
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}


# ========================================
# S3 Buckets for Data Lake
# ========================================

# Use for_each to create multiple S3 buckets from our map variable
resource "aws_s3_bucket" "data_lake_buckets" {
  for_each = var.s3_buckets
  bucket   = "${each.value}-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${each.value} Bucket"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = each.key # Adds a tag for 'raw' or 'processed'
  }
}

# Allow ACL usage for logging requirements
resource "aws_s3_bucket_ownership_controls" "data_lake_ownership" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}


# ========================================
# S3 Bucket ACL (Private by default)
# ========================================

# Set ACL to private for all created buckets
resource "aws_s3_bucket_acl" "data_lake_acl" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id
  acl      = "private"

  depends_on = [aws_s3_bucket_ownership_controls.data_lake_ownership]
}

# ========================================
# S3 Bucket Versioning
# ========================================
# Versioning provides:
# 1. Protection against accidental deletion
# 2. Audit trail for data changes
# 3. Recovery from application errors

# Enable versioning on all created buckets - CRITICAL for a data lake
resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}


# ========================================
# S3 Public Access Block
# ========================================
# Defense in depth: Block all public access even if ACLs
# or bucket policies are misconfigured

# Apply public access block to all created buckets for security
resource "aws_s3_bucket_public_access_block" "data_lake_public_access" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ========================================
# S3 Server-Side Encryption
# ========================================
# Encrypt all objects at rest using AES-256

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_encryption" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true # Reduces costs for KMS if using aws:kms
  }
}

# ========================================
# S3 Lifecycle Policy for Cost Optimization
# ========================================
# Automatically transition data to cheaper storage classes
# Strategy:
# - Day 0-90: STANDARD (frequent access for recent data)
# - Day 90-180: STANDARD_IA (infrequent access, 40% cheaper)
# - Day 180+: GLACIER (archival, 80% cheaper)

resource "aws_s3_bucket_lifecycle_configuration" "data_lake_lifecycle" {
  for_each = aws_s3_bucket.data_lake_buckets
  bucket   = each.value.id

  rule {
    id     = "transition-to-cheaper-storage"
    status = "Enabled"

    filter {
      prefix = "" # Apply lifecycle rule to the entire bucket
    }

    # Transition current version
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR" # Glacier Instant Retrieval
    }

    # Manage old versions
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER_IR"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365 # Delete versions older than 1 year
    }

    # Clean up incomplete multipart uploads (cost saver)
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ========================================
# Logging Bucket
# ========================================

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}-${random_string.bucket_suffix.result}"

  tags = {
    Name = "Access Logs Bucket"
  }
}

resource "aws_s3_bucket_ownership_controls" "logs_ownership" {
  bucket = aws_s3_bucket.logs.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "logs_acl" {
  bucket = aws_s3_bucket.logs.id
  acl    = "log-delivery-write"

  depends_on = [aws_s3_bucket_ownership_controls.logs_ownership]
}

# ========================================
# Enable Access Logging
# ========================================

resource "aws_s3_bucket_logging" "data_lake_logging" {
  for_each      = aws_s3_bucket.data_lake_buckets
  bucket        = each.value.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/${each.key}/"
}

# ========================================
# Cost Estimation
# ========================================
# Estimated monthly cost (assuming 100GB data, us-east-1):
# - STANDARD storage: $2.30/month
# - Data transfer: ~$0-9/month (depending on usage)
# - With lifecycle policies: ~$1.00/month (56% savings)
# Total: ~$1-11/month (well within free tier initially)