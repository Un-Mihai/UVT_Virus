resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.id}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  logs_destination           = "log-analytics"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.tags
}

# PERSONAL_DATA_HASH_KEY: HMAC key the API compares CNPs with; never rotate it casually, stored
# hashes stop matching new uploads.
resource "random_password" "personal_data_hash_key" {
  length  = 48
  special = false
}

locals {
  registry = azurerm_container_registry.main.login_server

  api_env = merge(
    {
      AI_CHAT_MODEL           = var.chat_model.name
      AI_EMBEDDING_MODEL      = var.embedding_model.name
      AI_EMBEDDING_DIMENSIONS = tostring(var.embedding_model.dimensions)
      AI_DAILY_BUDGET_USD     = tostring(var.ai_daily_budget_usd)
      AUTH_ISSUER             = local.auth_issuer
      # Tesseract takes a CPU core per page and the API has half of one.
      OCR_CONCURRENCY = "1"
    },
    local.ai_base_url == null ? {} : { AI_BASE_URL = local.ai_base_url },
    var.ai_fallback_base_url == null ? {} : { AI_FALLBACK_BASE_URL = var.ai_fallback_base_url },
    var.extra_api_env,
  )

  # Secret name => environment variable; values below. The conditions only test whether a key
  # exists, so they are safe to mark non-sensitive (for_each refuses sensitive keys).
  api_secrets = merge(
    { database-url = "DATABASE_URL", personal-data-hash-key = "PERSONAL_DATA_HASH_KEY" },
    var.create_ai || nonsensitive(var.ai_api_key != null) ? { ai-api-key = "AI_API_KEY" } : {},
    nonsensitive(var.ai_fallback_api_key != null) ? { ai-fallback-api-key = "AI_FALLBACK_API_KEY" } : {},
  )
  api_secret_values = {
    database-url           = local.database_url
    ai-api-key             = local.ai_api_key
    ai-fallback-api-key    = var.ai_fallback_api_key
    personal-data-hash-key = random_password.personal_data_hash_key.result
  }

  web_env = {
    API_URL        = "http://${azurerm_container_app.api.name}"
    APP_URL        = local.web_url
    AUTH_ISSUER    = local.auth_issuer
    AUTH_CLIENT_ID = "web"
  }
  web_secrets = {
    auth-client-secret = "AUTH_CLIENT_SECRET"
    auth-secret        = "AUTH_SECRET"
  }
  web_secret_values = {
    auth-client-secret = random_password.web_client_secret.result
    auth-secret        = random_password.auth_secret.result
  }
}

resource "azurerm_container_app" "api" {
  name                         = "api"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = local.registry
    identity = azurerm_user_assigned_identity.apps.id
  }

  dynamic "secret" {
    for_each = local.api_secrets
    content {
      name  = secret.key
      value = local.api_secret_values[secret.key]
    }
  }

  # Internal only: the browser reaches the API through the web app's /api proxy.
  ingress {
    external_enabled           = false
    allow_insecure_connections = true
    target_port                = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.keep_warm ? 1 : 0
    max_replicas = 2

    container {
      name   = "api"
      image  = "${local.registry}/api:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      dynamic "env" {
        for_each = local.api_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.api_secrets
        content {
          name        = env.value
          secret_name = env.key
        }
      }

      liveness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/health/live"
      }

      readiness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/health"
      }
    }
  }

  depends_on = [
    azurerm_role_assignment.acr_pull,
    azurerm_postgresql_flexible_server_configuration.extensions,
    azurerm_postgresql_flexible_server_firewall_rule.azure_services,
  ]
}

resource "azurerm_container_app" "web" {
  name                         = "web"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = local.registry
    identity = azurerm_user_assigned_identity.apps.id
  }

  dynamic "secret" {
    for_each = local.web_secrets
    content {
      name  = secret.key
      value = local.web_secret_values[secret.key]
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.keep_warm ? 1 : 0
    max_replicas = 2

    container {
      name   = "web"
      image  = "${local.registry}/web:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      dynamic "env" {
        for_each = local.web_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.web_secrets
        content {
          name        = env.value
          secret_name = env.key
        }
      }

      readiness_probe {
        transport = "TCP"
        port      = 3000
      }
    }
  }

  depends_on = [azurerm_role_assignment.acr_pull]
}
