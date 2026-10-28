# Shortcuts for the commands in AGENTS.md. Everything runs inside the Docker containers.
.DEFAULT_GOAL := help
compose := docker compose
# Reads WEB_PORT and friends from .env when it exists, so targets use the same ports as Compose.
-include .env
WEB_PORT ?= 3000
app := http://localhost:$(WEB_PORT)
# Pages the UI scan renders, signed in as the demo reviewer; add your product's routes:
# make check-ui UI_URLS="http://localhost:3000/status http://localhost:3000/files"
UI_URLS ?= $(app)/status
# Tools that scripts/setup.sh installs on Linux and WSL live here.
export PATH := $(HOME)/.local/bin:$(PATH)
# Commands that write files run as you, so Linux and WSL hosts do not get root-owned files.
as_me := --user $(shell id -u):$(shell id -g) --env HOME=/tmp

help: ## List the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

setup: ## Install missing tools, create .env, install dependencies, start the stack
	bash scripts/setup.sh

doctor: ## Report which tools are installed and what is missing; changes nothing
	bash scripts/setup.sh --check

# The web container keeps node_modules and its build cache in anonymous volumes, which Compose
# would reuse after a rebuild (old packages) and leave behind on down (about 800 MB). Removing
# the container with its volumes avoids both; the database is not touched.
up: ## Build and start the stack (web, api, keycloak, db) in the background; also after a pull
	$(compose) rm --stop --force --volumes web
	$(compose) up --build -d

down: ## Stop the stack (data is kept)
	$(compose) rm --stop --force --volumes web
	$(compose) down

reset-db: ## Stop the stack and delete the local database (run make up after)
	$(compose) down --volumes

reset-auth: ## Re-import infra/keycloak/realm-app.json (deletes local Keycloak users and sessions)
	$(compose) stop keycloak
	$(compose) exec db psql -U app -d app -c 'DROP DATABASE IF EXISTS keycloak' -c 'CREATE DATABASE keycloak'
	$(compose) up -d keycloak

logs: ## Follow api and web logs
	$(compose) logs -f api web

check: check-api check-web ## Every check: run before calling a task done

check-api: ## Format, lint, types and tests for the API
	$(compose) exec api poe check

check-web: ## Format, lint, types, tests and unused code for the web app
	$(compose) exec web npm run check

check-ui: ## Anti-slop scan (stack must be up): impeccable on source + signed-in pages at desktop and phone width, taste's linter
	node scripts/signed_in.mjs $(app) sh .agents/skills/impeccable/scripts/impeccable detect web/src $(UI_URLS)
	node scripts/signed_in.mjs $(app) sh .agents/skills/impeccable/scripts/impeccable detect --viewport 390x844 $(UI_URLS)
	node .agents/skills/design-taste-frontend/scripts/lint.mjs web/src --app

fix: ## Apply formatting and autofixable lint
	$(compose) exec $(as_me) api poe fix
	$(compose) exec $(as_me) web npm run format

migration: ## New Alembic migration from models.py: make migration m="add documents"
	$(compose) exec $(as_me) api alembic revision --autogenerate -m "$(m)"

gen-api: ## Regenerate the web app's API types from the running API
	$(compose) exec $(as_me) web npm run gen:api

criteria: ## Re-read the hackathon's official rules, criteria and schedule; report changes
	python3 scripts/judging_criteria.py

sync-agents: ## Copy .agents/skills to the Claude Code and Kiro folders and validate them
	python3 scripts/sync_agents.py

deploy: ## Build, push and deploy to Azure (asks before changing anything)
	bash scripts/deploy.sh

azure-env: ## Print AI_BASE_URL and AI_API_KEY of the deployed Azure AI account for .env
	@echo "AI_BASE_URL=$$(terraform -chdir=infra/terraform output -raw ai_base_url)"
	@echo "AI_API_KEY=$$(terraform -chdir=infra/terraform output -raw ai_api_key)"

.PHONY: help setup doctor up down reset-db reset-auth logs check check-api check-web check-ui fix migration gen-api criteria sync-agents deploy azure-env
