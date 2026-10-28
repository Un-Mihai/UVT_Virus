# Offline checks with a mocked Azure provider: `terraform test` (no credentials, no cost).

mock_provider "azurerm" {
  # Resources whose IDs other resources validate need well-formed Azure IDs.
  mock_resource "azurerm_resource_group" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test" }
  }
  mock_resource "azurerm_log_analytics_workspace" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.OperationalInsights/workspaces/log-test" }
  }
  mock_resource "azurerm_container_registry" {
    defaults = {
      id           = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.ContainerRegistry/registries/acrtest"
      login_server = "acrtest.azurecr.io"
    }
  }
  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-test"
      principal_id = "11111111-1111-1111-1111-111111111111"
      client_id    = "22222222-2222-2222-2222-222222222222"
    }
  }
  mock_resource "azurerm_postgresql_flexible_server" {
    defaults = {
      id   = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.DBforPostgreSQL/flexibleServers/psql-test"
      fqdn = "psql-test.postgres.database.azure.com"
    }
  }
  mock_resource "azurerm_cognitive_account" {
    defaults = {
      id                 = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.CognitiveServices/accounts/ai-test"
      primary_access_key = "mock-key"
    }
  }
  mock_resource "azurerm_container_app_environment" {
    defaults = {
      id             = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.App/managedEnvironments/cae-test"
      default_domain = "test.swedencentral.azurecontainerapps.io"
    }
  }
}

variables {
  subscription_id = "00000000-0000-0000-0000-000000000000"
}

run "defaults_create_azure_ai_and_keep_the_api_internal" {
  command = apply

  assert {
    condition     = azurerm_container_app.api.ingress[0].external_enabled == false
    error_message = "The API must only be reachable from inside the Container Apps environment."
  }

  assert {
    condition     = azurerm_container_app.web.ingress[0].external_enabled
    error_message = "The web app must be public."
  }

  assert {
    condition     = length(azurerm_cognitive_deployment.chat) == 1 && azurerm_cognitive_deployment.chat[0].name == "gpt-5-mini"
    error_message = "The chat deployment must be named after the model, like on OpenAI."
  }

  assert {
    condition     = startswith(local.ai_base_url, "https://ai-hack") && endswith(local.ai_base_url, ".openai.azure.com/openai/v1/")
    error_message = "AI_BASE_URL must point at the account's OpenAI v1 endpoint."
  }

  assert {
    condition     = contains(keys(local.api_secrets), "ai-api-key") && !contains(keys(local.api_secrets), "ai-fallback-api-key")
    error_message = "Only the secrets that have values may be created."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_configuration.extensions.value == "VECTOR"
    error_message = "pgvector must be allow-listed."
  }

  assert {
    condition     = azurerm_container_app.api.template[0].min_replicas == 0
    error_message = "Apps scale to zero unless keep_warm is on."
  }

  assert {
    condition     = length(azurerm_consumption_budget_resource_group.main) == 0
    error_message = "No budget without an alert email."
  }

  assert {
    condition     = azurerm_container_app.keycloak.ingress[0].external_enabled && azurerm_container_app.keycloak.template[0].max_replicas == 1
    error_message = "Keycloak must be public (browsers sign in there) and run one replica (its caches are local)."
  }

  assert {
    condition = (
      local.web_env["APP_URL"] == "https://web.test.swedencentral.azurecontainerapps.io" &&
      local.keycloak_env["KC_APP_URL"] == local.web_env["APP_URL"] &&
      local.keycloak_env["KC_HOSTNAME"] == "https://keycloak.test.swedencentral.azurecontainerapps.io"
    )
    error_message = "Keycloak and the web app must point at each other's public URLs."
  }

  assert {
    condition     = local.api_env["AUTH_ISSUER"] == "https://keycloak.test.swedencentral.azurecontainerapps.io/realms/app" && local.web_env["AUTH_ISSUER"] == local.api_env["AUTH_ISSUER"]
    error_message = "The API and the web app must trust the same issuer, Keycloak's public realm URL."
  }

  assert {
    condition     = toset(compact(azurerm_container_app.web.template[0].container[0].env[*].secret_name)) == toset(["auth-client-secret", "auth-secret"])
    error_message = "The client secret and the cookie key must reach the web app as secrets."
  }
}

run "external_provider_with_fallback_and_demo_settings" {
  command = apply

  variables {
    create_ai            = false
    ai_base_url          = "https://api.openai.com/v1"
    ai_api_key           = "test-key"
    ai_fallback_base_url = "https://ai-other.openai.azure.com/openai/v1/"
    ai_fallback_api_key  = "other-key"
    keep_warm            = true
    budget_alert_email   = "team@example.com"
  }

  assert {
    condition     = length(azurerm_cognitive_account.ai) == 0
    error_message = "No Azure AI account when create_ai is false."
  }

  assert {
    condition     = local.api_env["AI_BASE_URL"] == "https://api.openai.com/v1" && local.api_env["AI_FALLBACK_BASE_URL"] == "https://ai-other.openai.azure.com/openai/v1/"
    error_message = "The API must get both provider URLs."
  }

  assert {
    condition     = contains(keys(local.api_secrets), "ai-fallback-api-key")
    error_message = "The fallback key must become a secret."
  }

  assert {
    condition     = azurerm_container_app.web.template[0].min_replicas == 1
    error_message = "keep_warm must keep one replica running."
  }

  assert {
    condition     = length(azurerm_consumption_budget_resource_group.main) == 1
    error_message = "An alert email must create the budget."
  }

  assert {
    condition     = azurerm_container_app.keycloak.template[0].min_replicas == 1
    error_message = "keep_warm must keep Keycloak running too, or the first sign-in waits for it to start."
  }
}
