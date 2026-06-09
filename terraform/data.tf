data "azurerm_function_app_host_keys" "this" {
  name                = azurerm_function_app_flex_consumption.this.name
  resource_group_name = azurerm_resource_group.this.name
}