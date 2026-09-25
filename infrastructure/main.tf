# Azure infrastructure for the REES46 pipeline (spec §4).
# Auth: `az login`. azurerm 4.x also needs the subscription id:
#   export ARM_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
# State is local (terraform.tfstate, gitignored); it contains the SQL admin
# password, so never commit it.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azapi" {}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  name = "${var.project}${random_string.suffix.result}"
  tags = {
    project    = var.project
    managed_by = "terraform"
    repository = "https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project}"
  location = var.location
  tags     = local.tags
}
