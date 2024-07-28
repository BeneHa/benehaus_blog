terraform {
  backend "azurerm" {
    resource_group_name  = "state_storage"
    storage_account_name = "behatfstate"
    container_name       = "tfstate"
    key                  = "blog/terraform.tfstate"
    subscription_id = "2594c4b1-2529-430a-a44b-4a8e5281733b"
  }
}
