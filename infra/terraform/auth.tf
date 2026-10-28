# Sign-in: Keycloak on Container Apps, with its own database on the app's PostgreSQL server. The
# image (infra/keycloak/Dockerfile) carries the realm, which is imported on the first start only;
# after that, change the realm in the admin console (docs/auth.md).

locals {
  # Public apps are reachable at <app name>.<environment domain>, so Keycloak and the web app can
  # point at each other before either exists.
  web_url      = "https://web.${azurerm_container_app_environment.main.default_domain}"
  keycloak_url = "https://keycloak.${azurerm_container_app_environment.main.default_domain}"
  auth_issuer  = "${local.keycloak_url}/realms/app"

  keycloak_env = {
    KC_HOSTNAME                 = local.keycloak_url
    KC_HTTP_ENABLED             = "true" # the ingress terminates TLS
    KC_PROXY_HEADERS            = "xforwarded"
    KC_CACHE                    = "local" # one replica; user sessions are kept in PostgreSQL
    KC_DB_URL                   = "jdbc:postgresql://${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.keycloak.name}?sslmode=require"
    KC_DB_USERNAME              = azurerm_postgresql_flexible_server.main.administrator_login
    KC_DB_POOL_MAX_SIZE         = "10" # B1ms allows 50 connections; the API takes up to 15 per replica
    KC_BOOTSTRAP_ADMIN_USERNAME = "keycloak"
    KC_APP_URL                  = local.web_url # realm-app.json builds the redirect URLs from it
  }

  # Secret name => environment variable, as for the API.
  keycloak_secrets = {
    db-password       = "KC_DB_PASSWORD"
    admin-password    = "KC_BOOTSTRAP_ADMIN_PASSWORD"
    web-client-secret = "KC_WEB_CLIENT_SECRET"
    demo-password     = "KC_DEMO_PASSWORD"
  }
  keycloak_secret_values = {
    db-password       = random_password.postgres.result
    admin-password    = random_password.keycloak_admin.result
    web-client-secret = random_password.web_client_secret.result
    demo-password     = random_password.demo_users.result
  }
}

resource "azurerm_postgresql_flexible_server_database" "keycloak" {
  name      = "keycloak"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "random_password" "keycloak_admin" {
  length  = 24
  special = false
}

# The reviewer and admin demo accounts sign in with it: the team and the jury.
resource "random_password" "demo_users" {
  length  = 16
  special = false
}

# The web app's OIDC client secret, given to both Keycloak and the web app.
resource "random_password" "web_client_secret" {
  length  = 32
  special = false
}

# AUTH_SECRET: encrypts the web app's session cookies.
resource "random_password" "auth_secret" {
  length  = 48
  special = false
}

resource "azurerm_container_app" "keycloak" {
  name                         = "keycloak"
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
    for_each = local.keycloak_secrets
    content {
      name  = secret.key
      value = local.keycloak_secret_values[secret.key]
    }
  }

  # Public: browsers come here to sign in.
  ingress {
    external_enabled = true
    target_port      = 8080

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.keep_warm ? 1 : 0
    max_replicas = 1 # local caches do not cluster

    container {
      name   = "keycloak"
      image  = "${local.registry}/keycloak:${var.image_tag}"
      cpu    = 1
      memory = "2Gi"

      dynamic "env" {
        for_each = local.keycloak_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.keycloak_secrets
        content {
          name        = env.value
          secret_name = env.key
        }
      }

      # Health is on the management port. The first start creates the schema and imports the
      # realm, which takes a few minutes on a B1ms database.
      startup_probe {
        transport               = "HTTP"
        port                    = 9000
        path                    = "/health/started"
        initial_delay           = 20
        interval_seconds        = 20
        failure_count_threshold = 10
        timeout                 = 5
      }

      readiness_probe {
        transport = "HTTP"
        port      = 9000
        path      = "/health/ready"
        timeout   = 5
      }

      liveness_probe {
        transport = "HTTP"
        port      = 9000
        path      = "/health/live"
      }
    }
  }

  depends_on = [
    azurerm_role_assignment.acr_pull,
    azurerm_postgresql_flexible_server_firewall_rule.azure_services,
  ]
}
