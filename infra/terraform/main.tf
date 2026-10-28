resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

locals {
  # Globally unique names (registry, database, AI subdomain) need the random suffix.
  id          = "${var.name}${random_string.suffix.result}"
  ai_location = coalesce(var.ai_location, var.location)
  tags        = { project = var.name, managed-by = "terraform" }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.name}-${random_string.suffix.result}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.id}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 1
  tags                = local.tags
}

resource "azurerm_container_registry" "main" {
  name                = "acr${local.id}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Basic"
  tags                = local.tags
}

# The apps pull images with this identity instead of registry passwords.
resource "azurerm_user_assigned_identity" "apps" {
  name                = "id-${local.id}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_consumption_budget_resource_group" "main" {
  count             = var.budget_alert_email == "" ? 0 : 1
  name              = "budget-${local.id}"
  resource_group_id = azurerm_resource_group.main.id
  amount            = var.budget_amount_usd
  time_grain        = "Monthly"

  time_period {
    start_date = formatdate("YYYY-MM-01'T'00:00:00Z", timestamp())
  }

  dynamic "notification" {
    for_each = [50, 80, 100]
    content {
      operator       = "GreaterThanOrEqualTo"
      threshold      = notification.value
      contact_emails = [var.budget_alert_email]
    }
  }

  lifecycle {
    ignore_changes = [time_period]
  }
}
