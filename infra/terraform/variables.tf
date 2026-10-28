variable "subscription_id" {
  description = "Azure subscription to deploy into (az account show --query id -o tsv)."
  type        = string
}

variable "name" {
  description = "Short project name used in resource names: 3-10 lowercase letters or digits."
  type        = string
  default     = "hack"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,9}$", var.name))
    error_message = "Use 3-10 lowercase letters or digits, starting with a letter."
  }
}

variable "location" {
  description = "Region for the app, database and registry. Student subscriptions only allow a few regions: see docs/deploy-azure.md."
  type        = string
  default     = "swedencentral"
}

variable "ai_location" {
  description = "Region for the AI Foundry account; defaults to location. Pick one where your models have quota."
  type        = string
  default     = null
}

variable "create_ai" {
  description = "Create an Azure AI Foundry account with the chat and embedding deployments. Set false to use ai_base_url and ai_api_key instead (organiser tokens, OpenAI...)."
  type        = bool
  default     = true
}

variable "foundry_project" {
  description = "Also create a Foundry project, needed for the Foundry portal playground and agents."
  type        = bool
  default     = true
}

variable "chat_model" {
  description = "Chat model deployment. The deployment is named after the model so AI_CHAT_MODEL works the same on OpenAI."
  type = object({
    name     = string
    version  = string
    capacity = number # thousands of tokens per minute
  })
  default = {
    name     = "gpt-5-mini"
    version  = "2025-08-07"
    capacity = 50
  }
}

variable "embedding_model" {
  description = "Embedding model deployment; dimensions must match the pgvector columns."
  type = object({
    name       = string
    version    = string
    capacity   = number
    dimensions = number
  })
  default = {
    name       = "text-embedding-3-small"
    version    = "1"
    capacity   = 50
    dimensions = 1536
  }
}

variable "ai_base_url" {
  description = "OpenAI-compatible base URL, used when create_ai = false."
  type        = string
  default     = null
}

variable "ai_api_key" {
  description = "API key for ai_base_url, used when create_ai = false."
  type        = string
  default     = null
  sensitive   = true
}

variable "ai_fallback_base_url" {
  description = "Second account (for example a teammate's Azure for Students resource with the same deployment names)."
  type        = string
  default     = null
}

variable "ai_fallback_api_key" {
  description = "API key for ai_fallback_base_url."
  type        = string
  default     = null
  sensitive   = true
}

variable "ai_daily_budget_usd" {
  description = "The API refuses AI calls once today's estimated spend reaches this."
  type        = number
  default     = 5
}

variable "extra_api_env" {
  description = "More API environment variables, for example AI_PRICE_INPUT_PER_MTOK for a different model."
  type        = map(string)
  default     = {}
}

variable "image_tag" {
  description = "Image tag to run; scripts/deploy.sh pushes each build as a commit tag and as latest."
  type        = string
  default     = "latest"
}

variable "keep_warm" {
  description = "Keep one replica of each app running (no cold starts). Turn on for the demo, off afterwards: it uses credit around the clock."
  type        = bool
  default     = false
}

variable "postgres_version" {
  description = "PostgreSQL major version; 17 matches the local Docker database."
  type        = string
  default     = "17"
}

variable "postgres_sku" {
  description = "Burstable B1ms is the cheapest tier and the one in Azure's free offers."
  type        = string
  default     = "B_Standard_B1ms"
}

variable "developer_ip_addresses" {
  description = "Public IPs allowed to reach PostgreSQL directly (psql from a laptop). Container Apps reach it through the Azure services rule."
  type        = list(string)
  default     = []
}

variable "budget_alert_email" {
  description = "Email for spend alerts at 50%, 80% and 100% of budget_amount_usd. Leave empty to skip (Azure for Students may not support budgets)."
  type        = string
  default     = ""
}

variable "budget_amount_usd" {
  description = "Monthly budget for this resource group."
  type        = number
  default     = 40
}
