#!/usr/bin/env bash
# Deploys the app to Azure: builds the api, web and keycloak images for linux/amd64, pushes them to
# the project's container registry and points the Container Apps at them. The first run also creates all the
# infrastructure (15-20 minutes). Terraform shows each plan and waits for "yes".
# Windows: run it from WSL or Git Bash.
set -euo pipefail
cd "$(dirname "$0")/.."
# scripts/setup.sh installs terraform and az here on Linux and WSL.
export PATH="$HOME/.local/bin:$PATH"

tf() { terraform -chdir=infra/terraform "$@"; }
tf_value() { echo "$1" | tf console | tr -d '"'; }

for tool in az docker terraform; do
  command -v "$tool" >/dev/null || { echo "Missing '$tool': run 'bash scripts/setup.sh' (make setup)." >&2; exit 1; }
done
if [ ! -f infra/terraform/terraform.tfvars ]; then
  echo "Copy infra/terraform/terraform.tfvars.example to terraform.tfvars and fill it in first." >&2
  exit 1
fi

# Unique per deploy, so uncommitted changes still roll out as a new revision.
tag="$(git rev-parse --short HEAD 2>/dev/null || echo build)-$(date +%Y%m%d%H%M%S)"

tf init -input=false
# The apps are created from images in the registry, so the registry has to exist first.
tf apply -target=azurerm_container_registry.main
registry="$(tf_value azurerm_container_registry.main.login_server)"
az acr login --name "${registry%%.*}" --subscription "$(tf_value var.subscription_id)"

for dir in api web infra/keycloak; do
  image="$registry/$(basename "$dir")"
  docker buildx build --platform linux/amd64 --target prod \
    --tag "$image:$tag" --tag "$image:latest" --push "$dir"
done

tf apply -var "image_tag=$tag"
echo "Deployed $tag: $(tf output -raw web_url)/status"
echo "Sign in as reviewer or admin; password: terraform -chdir=infra/terraform output -raw demo_password"
