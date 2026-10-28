# Deploy to Azure (Azure for Students)

One person on the team owns the deployment: Terraform keeps its state in
`infra/terraform/terraform.tfstate` on that person's laptop.

## What you get

| Resource | Purpose | Rough cost |
|---|---|---|
| Container Apps `web` (public) and `api` (internal) | The app; scale to zero when idle | Free monthly grant covers a hackathon |
| Container App `keycloak` (public), 1 vCPU and 2 GiB | Sign-in, with its own database on the PostgreSQL server | Scales to zero; with `keep_warm` about $1–3 per day |
| PostgreSQL Flexible Server, Burstable B1ms, 32 GB | Database with pgvector | About $0.50 per day, unless your subscription has the 12-month free tier |
| Container Registry, Basic | Your images | About $0.17 per day |
| Azure AI Foundry account + `gpt-5-mini` and `text-embedding-3-small` deployments | AI | Per token (the app's daily budget caps it) |
| Log Analytics | Container logs, capped at 1 GB per day | Cents |

Prices are approximate (October 2026). Credit-only student subscriptions stop when the credit
runs out instead of charging a card.

## 1. Prerequisites

- An activated [Azure for Students](https://azure.microsoft.com/free/students) subscription
  ($100, no card; each teammate can get one).
- Docker with Buildx (Docker Desktop has it), plus the Azure CLI and Terraform 1.9 or newer:
  `make setup` installs those two. Windows: use WSL.

```bash
az login
az account list -o table
az account set --subscription "Azure for Students"
az account show --query id -o tsv
```

The last command prints the `subscription_id` for step 3.

## 2. Find a region you are allowed to use

Student subscriptions may only deploy to about five regions, and the list differs per person:

```bash
az policy assignment list --disable-scope-strict-match --query "[?displayName=='Allowed resource deployment regions'].parameters" -o jsonc
```

Or in the portal: Policy → Assignments → "Allowed resource deployment regions" → Allowed
locations. Prefer an EU region (documents stay in the EU).

Check that the AI models have quota in the region you choose for `ai_location`:

```bash
az cognitiveservices usage list --location swedencentral -o table | grep -Ei "gpt-5-mini|text-embedding-3-small"
```

A limit of 0 means no quota there: try another allowed region, lower the capacity in
`terraform.tfvars`, request quota at https://aka.ms/oai/stuquotarequest, or use another provider
(`create_ai = false`, step 3).

## 3. Configure

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Fill in `subscription_id`, `location` and `ai_location`. Never commit `terraform.tfvars`.

## 4. Deploy

```bash
make deploy
```

`scripts/deploy.sh` creates the container registry, builds the `api`, `web` and `keycloak` images
for `linux/amd64`, pushes them, then creates or updates everything else. Terraform shows each
plan and waits for `yes`. The first run takes 15–20 minutes (the database and the Container Apps
environment are slow to create); later deploys take a few minutes, mostly the image builds.

Open the printed URL (it ends in `/status`) and sign in as `reviewer` with the password from
`terraform -chdir=infra/terraform output -raw demo_password`, then press **Run AI check**.
Keycloak's first start creates its tables and imports the realm, so the first sign-in after
the first deploy may need a minute or two.

To use the Azure AI deployment from your laptop too, copy the two lines from `make azure-env`
into `.env`.

## 5. A second account as fallback

When one subscription's credit runs out, its AI calls fail and the app switches to the fallback
account automatically. A teammate creates an AI account in their own subscription with the same
deployment names:

```bash
az group create --name rg-ai-backup --location swedencentral
az cognitiveservices account create --name ai-backup-<yourname> --resource-group rg-ai-backup \
  --location swedencentral --kind AIServices --sku S0 --custom-domain ai-backup-<yourname> --yes
az cognitiveservices account deployment create --name ai-backup-<yourname> --resource-group rg-ai-backup \
  --deployment-name gpt-5-mini --model-name gpt-5-mini --model-version 2025-08-07 \
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50
az cognitiveservices account deployment create --name ai-backup-<yourname> --resource-group rg-ai-backup \
  --deployment-name text-embedding-3-small --model-name text-embedding-3-small --model-version 1 \
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50
az cognitiveservices account keys list --name ai-backup-<yourname> --resource-group rg-ai-backup --query key1 -o tsv
```

Put `https://ai-backup-<yourname>.openai.azure.com/openai/v1/` and the key into
`ai_fallback_base_url` and `ai_fallback_api_key` in `terraform.tfvars` (and into
`AI_FALLBACK_BASE_URL` / `AI_FALLBACK_API_KEY` in `.env` for local work), then `make deploy`.

## 6. Demo day and afterwards

- Every page and API call needs a sign-in, so strangers cannot read the data or spend the AI
  budget. Give the jury the URL, the user `reviewer` and the demo password. Add people or change
  passwords in the Keycloak admin console ([docs/auth.md](auth.md)).
- Before the demo set `keep_warm = true` and run `make deploy`, so neither the first visitor nor
  the first sign-in waits for a cold start. It keeps one replica of each app running around the
  clock: turn it off after.
- Logs: `az containerapp logs show --name api --resource-group <resource_group> --follow`
  (`terraform -chdir=infra/terraform output resource_group` prints the group).
- Pause the database when nobody uses it:
  `az postgres flexible-server stop --resource-group <resource_group> --name <server>` (Azure
  starts it again after 7 days).
- When you are done: `terraform -chdir=infra/terraform destroy`. This deletes the database too.

## Troubleshooting

| Error | Cause and fix |
|---|---|
| `RequestDisallowedByAzure` ... "best available regions" | The region is not in your allowed list (step 2). Change `location` or `ai_location`. |
| `LocationIsOfferRestricted`, `RegionIsOfferRestricted`, "Subscriptions are restricted from provisioning in this region" | PostgreSQL is not offered to your subscription in that region. Try another allowed `location`. |
| `InsufficientQuota` on `azurerm_cognitive_deployment` | No model quota there. Lower `capacity`, change `ai_location`, request quota, or `create_ai = false`. |
| `MissingSubscriptionRegistration` | Run `az provider register --namespace Microsoft.App --wait` (or the namespace named in the error), then deploy again. |
| Container App stuck pulling the image, `UNAUTHORIZED` | The AcrPull permission takes a few minutes to apply. Run `make deploy` again. |
| `exec format error` in the logs | The image was built for ARM. Deploy with `make deploy`, which builds `linux/amd64`. |
| `ACR Tasks requests for the registry are not permitted` | `az acr build` is disabled for free-credit subscriptions; `make deploy` builds locally. |
| The sign-in page takes about 30 seconds, or fails once | Keycloak had scaled to zero. Try again, or set `keep_warm = true`. |
| Keycloak keeps restarting | `az containerapp logs show --name keycloak --resource-group <rg>`: a database error means PostgreSQL is stopped or unreachable. |
| `/status` says the AI provider is not set up, or the check fails | Check the AI variables in `terraform.tfvars`, then the API logs (section 6). |
| Everything stopped working at once | The subscription ran out of credit and was disabled. The fallback account keeps AI working; for the app itself, deploy from a teammate's subscription. |
