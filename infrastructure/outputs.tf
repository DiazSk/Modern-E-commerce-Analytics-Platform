output "resource_group_name" {
  description = "Resource group holding everything"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "ADLS Gen2 account (containers: raw, processed)"
  value       = azurerm_storage_account.lake.name
}

output "sql_server_fqdn" {
  description = "Azure SQL server host for dbt / sqlcmd"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  description = "Warehouse database name"
  value       = azapi_resource.warehouse.name
}

output "sql_database_id" {
  description = "Resource id, used to verify the free-offer settings"
  value       = azapi_resource.warehouse.id
}
