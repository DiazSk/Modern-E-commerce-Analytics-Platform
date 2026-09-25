# ADLS Gen2 lake (hierarchical namespace). Containers:
#   raw/rees46/archive/...          Kaggle downloads as delivered
#   processed/rees46/events/event_date=YYYY-MM-DD/*.parquet

resource "azurerm_storage_account" "lake" {
  name                            = "st${local.name}"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_kind                    = "StorageV2"
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_id    = azurerm_storage_account.lake.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "processed" {
  name                  = "processed"
  storage_account_id    = azurerm_storage_account.lake.id
  container_access_type = "private"
}

# Kaggle archives can be re-downloaded; the Parquet is the durable copy.
resource "azurerm_storage_management_policy" "lake" {
  storage_account_id = azurerm_storage_account.lake.id

  rule {
    name    = "expire-kaggle-archives"
    enabled = true

    filters {
      prefix_match = ["raw/rees46/archive/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 30
      }
    }
  }
}
