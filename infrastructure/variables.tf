variable "project" {
  description = "Short lowercase name used in resource names"
  type        = string
  default     = "ecomv2"

  validation {
    condition     = can(regex("^[a-z0-9]{3,10}$", var.project))
    error_message = "project must be 3-10 lowercase letters/digits (storage account naming rules)."
  }
}

variable "location" {
  description = "Azure region; must be allowed by the Azure for Students policy"
  type        = string
  default     = "eastus"
}

variable "sql_admin_login" {
  description = "SQL server administrator login"
  type        = string
  default     = "ecomadmin"
}

variable "sql_admin_password" {
  description = "SQL server administrator password; set in the gitignored secret.auto.tfvars"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.sql_admin_password) >= 16
    error_message = "sql_admin_password must be at least 16 characters."
  }
}

variable "operator_ip" {
  description = "Public IPv4 of the machine allowed through the SQL firewall"
  type        = string

  validation {
    condition     = can(cidrhost("${var.operator_ip}/32", 0))
    error_message = "operator_ip must be a single IPv4 address, e.g. 203.0.113.7."
  }
}

variable "alert_email" {
  description = "Where budget alerts are sent"
  type        = string
  default     = "zaid07sk@gmail.com"
}
