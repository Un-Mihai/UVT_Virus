output "web_url" {
  description = "Public URL of the app."
  value       = "https://${azurerm_container_app.web.ingress[0].fqdn}"
}

output "demo_password" {
  description = "Password of the client, reviewer and admin demo accounts, for the team and the jury: terraform output -raw demo_password"
  value       = random_password.demo_users.result
  sensitive   = true
}

output "keycloak_url" {
  description = "Keycloak. Its admin console is <url>/admin/, user keycloak, password from keycloak_admin_password."
  value       = "https://${azurerm_container_app.keycloak.ingress[0].fqdn}"
}

output "keycloak_admin_password" {
  value     = random_password.keycloak_admin.result
  sensitive = true
}

output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "registry_login_server" {
  description = "scripts/deploy.sh pushes images here."
  value       = azurerm_container_registry.main.login_server
}

output "ai_base_url" {
  description = "AI_BASE_URL for a local .env that uses the Azure deployments."
  value       = local.ai_base_url
}

output "ai_api_key" {
  description = "AI_API_KEY for a local .env: terraform output -raw ai_api_key"
  value       = local.ai_api_key
  sensitive   = true
}

output "ai_foundry_project" {
  description = "Open the Foundry portal (https://ai.azure.com) and pick this project."
  value       = var.create_ai && var.foundry_project ? azurerm_cognitive_account_project.main[0].name : null
}

output "postgres_host" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "database_url" {
  description = "DATABASE_URL the API uses; reachable from a laptop only if its IP is in developer_ip_addresses."
  value       = local.database_url
  sensitive   = true
}
