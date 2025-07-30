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
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  application_type    = "web"
  sampling_percentage = 0
  workspace_id = azurerm_log_analytics_workspace.this.id
}

resource "azurerm_service_plan" "this" {
  name                = "ASP-benehausblogrg-af9b"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
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

resource "azurerm_key_vault_secret" "strava_userid" {
    name = "strava-userid"
    value = "change_manually"
    key_vault_id = azurerm_key_vault.this.id
    depends_on = [ azurerm_role_assignment.personal ]
    lifecycle {
      ignore_changes = [ value ]
    }
}

resource "azurerm_key_vault_secret" "strava_client_secret" {
    name = "strava-client-secret"
    value = "change_manually"
    key_vault_id = azurerm_key_vault.this.id
    depends_on = [ azurerm_role_assignment.personal ]
    lifecycle {
      ignore_changes = [ value ]
    }
}

resource "azurerm_key_vault_secret" "strava_refresh_token" {
    name = "strava-refresh-token"
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
  location            = azurerm_resource_group.this.location
  daily_memory_time_quota = 1

  identity {
    type = "SystemAssigned"
  }

  storage_account_name       = azurerm_storage_account.this.name
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
    blobtriggerconnection__queueServiceUri = trimsuffix(azurerm_storage_account.this.primary_queue_endpoint, "/")
    blobtriggerconnection2__blobServiceUri = trimsuffix(azurerm_storage_account.this.primary_blob_endpoint, "/")
    blobtriggerconnection2__queueServiceUri = trimsuffix(azurerm_storage_account.this.primary_queue_endpoint, "/")
    komoot_password = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.komoot_password.name})"
    komoot_username = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.komoot_username.name})"
    storage_account_name = azurerm_storage_account.this.primary_blob_endpoint
    strava_userid = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.strava_userid.name})"
    strava_client_secret = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.strava_client_secret.name})"
    strava_refresh_token = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${azurerm_key_vault_secret.strava_refresh_token.name})"
    key_vault_url = azurerm_key_vault.this.vault_uri
  }


  lifecycle {
    #ignore_changes = [ app_settings, tags, daily_memory_time_quota ]
  }
}

resource "azurerm_monitor_diagnostic_setting" "this" {
  name = "diagsettingfunc"
  target_resource_id = azurerm_linux_function_app.this.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  enabled_log {
    category = "FunctionAppLogs"
  }
  lifecycle {
    ignore_changes = [ metric ]
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
    role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_role_assignment" "storage_sp" {
    scope = azurerm_storage_account.this.id
    principal_id = local.sp_id
    role_definition_name = "Storage Blob Data Contributor"
}

resource "azurerm_cdn_frontdoor_profile" "this" {
  name                = "benehaus-blog-cdn"
  resource_group_name = azurerm_resource_group.this.name
  sku_name            = "Standard_AzureFrontDoor"
  response_timeout_seconds = 120
  lifecycle {
    ignore_changes = [ sku_name ]
  }
}

# resource "azurerm_cdn_frontdoor_endpoint" "this" {
#   name                     = "benehausblogendpoint"
#   cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
# }

# resource "azurerm_cdn_frontdoor_custom_domain" "this" {
#   name                     = "benehausblogendpoint"
#   cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
#   host_name                = "www.bene.haus"

#   tls {
#     certificate_type    = "ManagedCertificate"
#     minimum_tls_version = "TLS12"
#   }
# }