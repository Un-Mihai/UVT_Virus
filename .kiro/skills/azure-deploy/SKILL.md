---
name: azure-deploy
description: Deploy this repo to Azure with Terraform (Container Apps, PostgreSQL with pgvector, Container Registry, Azure AI Foundry, Keycloak sign-in) on Azure for Students subscriptions, add a fallback AI account, prepare the demo, tear down, and diagnose deployment errors such as region policy, offer restrictions, model quota, image pulls and cold starts.
---

# Deploy to Azure

The full human guide, with every command, is `docs/deploy-azure.md`. Read it before acting; this
skill adds the rules an agent must follow.

## Rules

- Deploying creates billable resources and uses the team's credit. Run `make deploy`,
  `terraform apply`, `terraform destroy` or any resource-changing `az` command only when a human
  asked for it in this session, and let Terraform's confirmation prompt reach them.
- Never read or print `infra/terraform/terraform.tfvars`, `*.tfstate` or `terraform output` of
  sensitive values into the conversation. Ask the human to check them.
- Change infrastructure only in `infra/terraform/*.tf`. After editing, run
  `terraform -chdir=infra/terraform fmt` and `terraform -chdir=infra/terraform test` (offline,
  mocked provider) and extend `tests/plan.tftest.hcl` when you add behaviour.
- A new API setting is wired in three places: `api/app/config.py`, `.env.example`, and `api_env`
  (or `api_secrets` for secrets) in `infra/terraform/apps.tf`.

## Order of work for a first deploy

1. `az account show` matches the subscription the team wants (ask if unsure).
2. Allowed regions and model quota checked (guide, step 2). Most first-deploy failures are a
   region the student policy forbids or a model with zero quota.
3. `terraform.tfvars` created by the human from the example.
4. `make deploy`, then open `<web_url>/status`, sign in as `reviewer` (the human reads the
   password with `terraform -chdir=infra/terraform output -raw demo_password`) and run the AI
   check.

## Diagnosing

Match the error text against the troubleshooting table at the end of `docs/deploy-azure.md`.
When it is not listed:

- API errors at runtime: `az containerapp logs show --name api --resource-group <rg> --follow`
  (or `--name keycloak` for sign-in errors).
- A revision that never becomes healthy:
  `az containerapp revision list --name api --resource-group <rg> -o table`, then its logs.
- Terraform state out of sync after a manual portal change: `terraform -chdir=infra/terraform
  plan` and let the human decide whether to import, revert or re-apply.

## Before the demo

- The jury has the URL, the user `reviewer` and the demo password; sign in with them once on the
  deployed URL.
- `keep_warm = true` and redeploy so there are no cold starts; set it back afterwards.
- Run the AI check on the deployed URL and process the demo documents once, so the first live run
  is not the first run ever.
