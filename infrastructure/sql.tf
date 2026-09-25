resource "azurerm_mssql_server" "main" {
  name                          = "sql-${local.name}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  version                       = "12.0"
  administrator_login           = var.sql_admin_login
  administrator_login_password  = var.sql_admin_password
  minimum_tls_version           = "1.2"
  public_network_access_enabled = true
  tags                          = local.tags
}

# Only the operator's machine. Never 0.0.0.0 and never Databricks egress
# (spec §11.2.3). If your IP changes: terraform apply -var operator_ip=<new>.
resource "azurerm_mssql_firewall_rule" "operator" {
  name             = "operator"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = var.operator_ip
  end_ip_address   = var.operator_ip
}

# Serverless database on the Azure SQL free offer. azurerm does not expose
# useFreeLimit / freeLimitExhaustionBehavior, so this one resource uses azapi.
# AutoPause = when the monthly free vCore-seconds are used, pause until next
# month instead of billing (spec §1.6).
resource "azapi_resource" "warehouse" {
  type      = "Microsoft.Sql/servers/databases@2023-08-01-preview"
  name      = "rees46"
  parent_id = azurerm_mssql_server.main.id
  location  = azurerm_resource_group.main.location
  tags      = local.tags

  body = {
    sku = {
      name     = "GP_S_Gen5"
      tier     = "GeneralPurpose"
      family   = "Gen5"
      capacity = 2
    }
    properties = {
      useFreeLimit                     = true
      freeLimitExhaustionBehavior      = "AutoPause"
      autoPauseDelay                   = 60
      minCapacity                      = 0.5
      maxSizeBytes                     = 34359738368
      zoneRedundant                    = false
      requestedBackupStorageRedundancy = "Local"
    }
  }
}
