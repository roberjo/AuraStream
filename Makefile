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

deploy-dev: ## Deploy to development
	sam build
	sam deploy --config-env dev --no-confirm-changeset

deploy-staging: ## Deploy to staging
	sam build
	sam deploy --config-env staging --no-confirm-changeset

deploy-prod: ## Deploy to production
	sam build
	sam deploy --config-env prod --confirm-changeset

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

validate: ## Validate CloudFormation template
	sam validate

package: ## Package the application
	sam package --template-file template.yaml --s3-bucket aurastream-deployments --output-template-file packaged-template.yaml
