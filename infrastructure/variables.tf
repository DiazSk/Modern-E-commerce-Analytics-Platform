# ================================
# Variables
# ================================

# Define the AWS provider and the region as a variable for reusability
variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "modern-ecommerce-analytics-platform"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Use a map to define the buckets we want to create
variable "s3_buckets" {
  description = "A map of S3 buckets to create for the project."
  type        = map(string)
  default = {
    "raw"       = "ecommerce-raw-data"
    "processed" = "ecommerce-processed-data"
  }
}

# Email address for billing alerts
variable "billing_alert_email" {
  description = "Email address to receive billing alerts"
  type        = string
  default     = "zaid07sk@gmail.com" # Change this to your actual email

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.billing_alert_email))
    error_message = "Must be a valid email address."
  }
}
