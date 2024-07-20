resource "azurerm_resource_group" "this" {
    name = "benehaus-blog-rg"
    location = "germanywestcentral"
}

resource "azurerm_role_assignment" "rg" {
    scope = azurerm_resource_group.this.id
    principal_id = local.user_id
    role_definition_name = "Owner"
}

resource "azurerm_storage_account" "this" {
    name = "benehausblogstorage"
    resource_group_name = azurerm_resource_group.this.name

    account_tier = "Standard"
    location = "germanywestcentral"
    account_replication_type = "LRS"

    static_website {
      error_404_document = "404.html"
      index_document = "index.html"
    }
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "lawsbehafunction"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "this" {
  name                = "behablogfunction"
  location            = "westeurope"
  resource_group_name = azurerm_resource_group.this.name
  application_type    = "web"
  sampling_percentage = 0
  workspace_id = azurerm_log_analytics_workspace.this.id
}

resource "azurerm_service_plan" "this" {
  name                = "ASP-benehausblogrg-af9b"
  resource_group_name = azurerm_resource_group.this.name
  location            = "westeurope"
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_key_vault" "this" {
    name = "behablogkv"
    resource_group_name = azurerm_resource_group.this.name
    location = azurerm_resource_group.this.location
    tenant_id = local.tenant_id
    sku_name = "standard"
    enable_rbac_authorization = true
}

resource "azurerm_role_assignment" "personal" {
    scope = azurerm_key_vault.this.id
    principal_id = local.user_id
    role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_key_vault_secret" "komoot_username" {
    name = "komoot-username"
    value = "change_manually"
    key_vault_id = azurerm_key_vault.this.id
    depends_on = [ azurerm_role_assignment.personal ]
    lifecycle {
      ignore_changes = [ value ]
    }
}

resource "azurerm_key_vault_secret" "komoot_password" {
    name = "komoot-password"
    value = "change_manually"
    key_vault_id = azurerm_key_vault.this.id
    depends_on = [ azurerm_role_assignment.personal ]
    lifecycle {
      ignore_changes = [ value ]
    }
}

resource "azurerm_linux_function_app" "this" {
  name                = "behablogfunction"
  resource_group_name = azurerm_resource_group.this.name
  location            = "westeurope"
  daily_memory_time_quota = 1

  identity {
    type = "SystemAssigned"
  }

  storage_account_name       = azurerm_storage_account.this.name
  #storage_account_access_key = azurerm_storage_account.this.primary_access_key
  storage_uses_managed_identity = true
  service_plan_id            = azurerm_service_plan.this.id

  site_config {
    application_insights_connection_string = azurerm_application_insights.this.connection_string
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    blobtriggerconnection__blobServiceUri = trimsuffix(azurerm_storage_account.this.primary_blob_endpoint, "/")
    #blobtriggerconnection__credential = "managedidentity"
    blobtriggerconnection__queueServiceUri = trimsuffix(azurerm_storage_account.this.primary_queue_endpoint, "/")
    komoot_password = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.komoot_username.name})"
    komoot_username = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.komoot_password.name})"
    storage_account_name = azurerm_storage_account.this.primary_blob_endpoint
  }


  lifecycle {
    ignore_changes = [ app_settings.WEBSITE_RUN_FROM_PACKAGE, app_settings.WEBSITE_ENABLE_SYNC_UPDATE_SITE, tags ]
  }
}

resource "azurerm_monitor_diagnostic_setting" "this" {
  name = "diagsettingfunc"
  target_resource_id = azurerm_linux_function_app.this.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  enabled_log {
    category = "FunctionAppLogs"
  }
  metric {
    category = "AllMetrics"
  }
}

# Circle dependency, apply with target on re-create
resource "azurerm_role_assignment" "storage" {
    scope = azurerm_storage_account.this.id
    principal_id = azurerm_linux_function_app.this.identity[0].principal_id
    role_definition_name = "Storage Blob Data Owner"
}

resource "azurerm_role_assignment" "queue" {
    scope = azurerm_storage_account.this.id
    principal_id = azurerm_linux_function_app.this.identity[0].principal_id
    role_definition_name = "Storage Queue Data Contributor"
}

resource "azurerm_role_assignment" "owner" {
    scope = azurerm_storage_account.this.id
    principal_id = azurerm_linux_function_app.this.identity[0].principal_id
    role_definition_name = "Storage Account Contributor"
}

# Circle dependency, apply with target on re-create
resource "azurerm_role_assignment" "key_vault" {
    scope = azurerm_key_vault.this.id
    principal_id = azurerm_linux_function_app.this.identity[0].principal_id
    role_definition_name = "Key Vault Secrets User"
}

resource "azurerm_role_assignment" "storage_sp" {
    scope = azurerm_storage_account.this.id
    principal_id = local.sp_id
    role_definition_name = "Storage Blob Data Contributor"
}