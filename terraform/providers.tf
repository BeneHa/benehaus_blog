terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "< 5"
    }
  }
}

provider "azurerm" {
  features {
  }
  subscription_id = "2594c4b1-2529-430a-a44b-4a8e5281733b"
}
