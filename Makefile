# AuraStream Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-performance test-coverage lint format security clean build deploy-dev deploy-staging deploy-prod

# Default target
help: ## Show this help message
	@echo "AuraStream Development Commands"
	@echo "================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation commands
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

install-pre-commit: ## Install pre-commit hooks
	pre-commit install

# Testing commands
test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-performance: ## Run performance tests only
	pytest tests/performance/ -v -m performance

test-coverage: ## Run tests with coverage report
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-fast: ## Run fast tests (exclude slow/performance tests)
	pytest tests/ -v -m "not slow and not performance"

test-parallel: ## Run tests in parallel
	pytest tests/ -v -n auto

# Code quality commands
lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

format-check: ## Check code formatting
	black --check src/ tests/
	isort --check-only src/ tests/

# Security commands
security: ## Run security scans
	pip-audit --desc
	safety check

security-json: ## Run security scans with JSON output
	pip-audit --desc --format=json --output=security-audit.json
	safety check --json --output=safety-report.json

# Dependency management
update-deps: ## Update dependency lock files
	pip-compile requirements.in
	pip-compile requirements-dev.in

sync-deps: ## Sync dependencies with lock files
	pip-sync requirements-dev.txt

# Build and deployment
build: ## Build the package
	python -m build

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Terraform commands
terraform-init: ## Initialize Terraform
	cd terraform && terraform init

terraform-plan: ## Plan Terraform changes
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	cd terraform && terraform apply

terraform-destroy: ## Destroy Terraform resources
	cd terraform && terraform destroy

terraform-fmt: ## Format Terraform files
	cd terraform && terraform fmt -recursive

terraform-validate: ## Validate Terraform configuration
	cd terraform && terraform validate

# Environment-specific deployments
deploy-dev: ## Deploy to development environment
	cd terraform && terraform workspace select dev
	cd terraform && terraform apply -var-file="workspaces/dev.tfvars"

deploy-staging: ## Deploy to staging environment
	cd terraform && terraform workspace select staging
	cd terraform && terraform apply -var-file="workspaces/staging.tfvars"

deploy-prod: ## Deploy to production environment
	cd terraform && terraform workspace select prod
	cd terraform && terraform apply -var-file="workspaces/prod.tfvars"

# Development workflow
dev-setup: install-dev install-pre-commit ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything is working."

ci-test: ## Run CI test suite (used in GitHub Actions)
	pytest tests/unit/ tests/integration/ -v --cov=src --cov-report=xml --cov-fail-under=80
	pytest tests/performance/ -v -m performance --timeout=300

ci-quality: ## Run CI quality checks (used in GitHub Actions)
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

ci-security: ## Run CI security checks (used in GitHub Actions)
	pip-audit --desc --format=json --output=security-audit.json
	safety check --json --output=safety-report.json

# Documentation
docs: ## Generate documentation
	cd docs && sphinx-build -b html . _build/html

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8000

# Monitoring and debugging
logs: ## Show recent logs (requires AWS CLI configured)
	aws logs tail /aws/lambda/aurastream-sync-handler --follow

debug-local: ## Run local debugging session
	python -m pdb -c continue src/handlers/sync_handler.py

# Performance profiling
profile: ## Run performance profiling
	python -m cProfile -o profile.stats src/handlers/sync_handler.py
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Database operations (for local development)
db-setup: ## Set up local DynamoDB tables
	python scripts/setup_local_db.py

db-seed: ## Seed local database with test data
	python scripts/seed_local_db.py

# Utility commands
check-env: ## Check environment configuration
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "AWS CLI version: $$(aws --version 2>/dev/null || echo 'AWS CLI not installed')"
	@echo "Terraform version: $$(terraform --version 2>/dev/null || echo 'Terraform not installed')"

version: ## Show version information
	@echo "AuraStream Version: $$(grep version pyproject.toml 2>/dev/null || echo 'Not specified')"
	@echo "Git commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'Not a git repository')"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"