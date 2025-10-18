# AuraStream Makefile
.PHONY: help setup test lint type-check format deploy-dev deploy-staging deploy-prod clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Setup development environment
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -r requirements-dev.txt
	. venv/bin/activate && pre-commit install

test: ## Run all tests
	. venv/bin/activate && pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	. venv/bin/activate && pytest tests/unit/ -v

test-integration: ## Run integration tests only
	. venv/bin/activate && pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	. venv/bin/activate && pytest tests/e2e/ -v

lint: ## Run linting
	. venv/bin/activate && flake8 src/ tests/
	. venv/bin/activate && black --check src/ tests/
	. venv/bin/activate && isort --check-only src/ tests/

type-check: ## Run type checking
	. venv/bin/activate && mypy src/

format: ## Format code
	. venv/bin/activate && black src/ tests/
	. venv/bin/activate && isort src/ tests/

security: ## Run security checks
	. venv/bin/activate && bandit -r src/
	. venv/bin/activate && safety check

build: ## Build the application
	sam build

deploy-dev: ## Deploy to development via Terraform Cloud
	cd terraform && terraform workspace select aurastream-dev
	cd terraform && terraform plan -var-file="workspaces/dev.tfvars"
	cd terraform && terraform apply -var-file="workspaces/dev.tfvars" -auto-approve

deploy-staging: ## Deploy to staging via Terraform Cloud
	cd terraform && terraform workspace select aurastream-staging
	cd terraform && terraform plan -var-file="workspaces/staging.tfvars"
	cd terraform && terraform apply -var-file="workspaces/staging.tfvars" -auto-approve

deploy-prod: ## Deploy to production via Terraform Cloud
	cd terraform && terraform workspace select aurastream-prod
	cd terraform && terraform plan -var-file="workspaces/prod.tfvars"
	cd terraform && terraform apply -var-file="workspaces/prod.tfvars" -auto-approve

local: ## Run locally
	sam local start-api --port 3000

invoke: ## Invoke function locally
	sam local invoke SyncHandler --event events/sync_event.json

logs: ## View logs
	sam logs -n SyncHandler --stack-name aurastream-dev --tail

clean: ## Clean build artifacts
	rm -rf .aws-sam/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

install-hooks: ## Install pre-commit hooks
	. venv/bin/activate && pre-commit install

update-deps: ## Update dependencies
	. venv/bin/activate && pip-compile requirements.in
	. venv/bin/activate && pip-compile requirements-dev.in

validate: ## Validate Terraform configuration
	cd terraform && terraform validate

terraform-init: ## Initialize Terraform
	cd terraform && terraform init

terraform-plan: ## Plan Terraform deployment
	cd terraform && terraform plan -var-file="workspaces/dev.tfvars"

terraform-fmt: ## Format Terraform files
	cd terraform && terraform fmt -recursive

terraform-workspace: ## List Terraform workspaces
	cd terraform && terraform workspace list
