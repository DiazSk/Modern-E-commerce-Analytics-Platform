// Terraform S3 backend configuration
// This file configures Terraform to store state in an S3 bucket.
// It uses the existing logging bucket created by your Terraform run.
// Run `terraform init` in this folder to migrate local state to S3.

terraform {
  backend "s3" {
    # Use one of the S3 buckets you created. This stores the Terraform state.
    bucket = "modern-ecommerce-analytics-platform-logs-dev-bnf5etbn"

    # Path within the bucket where the state file will be stored
    key = "infrastructure/terraform.tfstate"

    # Region for the S3 bucket
    region = "us-east-1"

    # Encrypt state at rest
    encrypt = true

    # Optional: enable DynamoDB locking by creating a table and uncommenting
    # the line below. If you don't have a lock table yet, leave commented
    # and create the table separately before enabling locks.
    # dynamodb_table = "terraform-locks-modern-ecommerce"
  }
}
