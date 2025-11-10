# ========================================
# Outputs
# ========================================

output "data_lake_bucket_names" {
  description = "Names of created S3 buckets"
  value       = { for k, v in aws_s3_bucket.data_lake_buckets : k => v.bucket }
}

output "data_lake_bucket_arns" {
  description = "ARNs of created S3 buckets (useful for IAM policies)"
  value       = { for k, v in aws_s3_bucket.data_lake_buckets : k => v.arn }
}

output "logs_bucket_name" {
  description = "Name of the access logs bucket"
  value       = aws_s3_bucket.logs.bucket
}
