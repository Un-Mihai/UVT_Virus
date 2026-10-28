resource "azurerm_cognitive_account" "ai" {
  count                      = var.create_ai ? 1 : 0
  name                       = "ai-${local.id}"
  location                   = local.ai_location
  resource_group_name        = azurerm_resource_group.main.name
  kind                       = "AIServices"
  sku_name                   = "S0"
  custom_subdomain_name      = "ai-${local.id}"
  local_auth_enabled         = true # the app authenticates with the key, like any other provider
  project_management_enabled = var.foundry_project
  tags                       = local.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_account_project" "main" {
  count                = var.create_ai && var.foundry_project ? 1 : 0
  name                 = "proj-${local.id}"
  cognitive_account_id = azurerm_cognitive_account.ai[0].id
  location             = local.ai_location

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_deployment" "chat" {
  count                = var.create_ai ? 1 : 0
  name                 = var.chat_model.name
  cognitive_account_id = azurerm_cognitive_account.ai[0].id

  model {
    format  = "OpenAI"
    name    = var.chat_model.name
    version = var.chat_model.version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.chat_model.capacity
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  count                = var.create_ai ? 1 : 0
  name                 = var.embedding_model.name
  cognitive_account_id = azurerm_cognitive_account.ai[0].id

  model {
    format  = "OpenAI"
    name    = var.embedding_model.name
    version = var.embedding_model.version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.embedding_model.capacity
  }

  # Azure rejects two deployment operations on one account at the same time.
  depends_on = [azurerm_cognitive_deployment.chat]
}

locals {
  ai_base_url = var.create_ai ? "https://${azurerm_cognitive_account.ai[0].custom_subdomain_name}.openai.azure.com/openai/v1/" : var.ai_base_url
  ai_api_key  = var.create_ai ? azurerm_cognitive_account.ai[0].primary_access_key : var.ai_api_key
}
