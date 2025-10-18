# AuraStream Development Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Code Standards](#code-standards)
5. [Development Workflow](#development-workflow)
6. [Testing Guidelines](#testing-guidelines)
7. [Deployment Process](#deployment-process)
8. [Contributing Guidelines](#contributing-guidelines)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before you begin development, ensure you have the following installed:

- **Python 3.9+** - Runtime environment
- **AWS CLI v2** - AWS service interaction
- **AWS SAM CLI** - Serverless application deployment
- **Docker** - Local development and testing
- **Git** - Version control
- **Node.js 16+** - For testing tools and utilities

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/aurastream.git
cd aurastream

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure AWS credentials
aws configure

# Run initial setup
make setup
```

---

## Development Environment Setup

### Local Development Stack

#### 1. AWS SAM Local

```bash
# Install AWS SAM CLI
# macOS
brew install aws-sam-cli

# Windows
# Download from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Linux
pip install aws-sam-cli
```

#### 2. Docker Setup

```bash
# Start Docker daemon
# macOS/Windows: Start Docker Desktop
# Linux: sudo systemctl start docker

# Verify installation
docker --version
sam --version
```

#### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# .env
AWS_REGION=us-east-1
AWS_PROFILE=default
STAGE=dev
LOG_LEVEL=DEBUG
ENABLE_XRAY=true
```

#### 4. Local Development Commands

```bash
# Start local API Gateway
sam local start-api --port 3000

# Invoke function locally
sam local invoke SyncHandler --event events/sync_event.json

# Build and test
sam build
sam local start-api --port 3000

# Run tests
make test

# Run linting
make lint

# Run type checking
make type-check
```

### IDE Configuration

#### VS Code Setup

Install recommended extensions:

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-azuretools.vscode-docker",
    "amazonwebservices.aws-toolkit-vscode"
  ]
}
```

#### VS Code Settings

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## Project Structure

```
AuraStream/
├── src/                          # Source code
│   ├── handlers/                 # Lambda function handlers
│   │   ├── __init__.py
│   │   ├── sync_handler.py       # Synchronous analysis
│   │   ├── async_handler.py      # Asynchronous analysis
│   │   ├── status_handler.py     # Job status checking
│   │   └── health_handler.py     # Health check endpoint
│   ├── cache/                    # Caching logic
│   │   ├── __init__.py
│   │   ├── sentiment_cache.py    # Sentiment result caching
│   │   └── cache_manager.py      # Cache management utilities
│   ├── error_handling/           # Error handling utilities
│   │   ├── __init__.py
│   │   ├── retry_handler.py      # Retry logic with backoff
│   │   ├── circuit_breaker.py    # Circuit breaker pattern
│   │   └── error_classifier.py   # Error type classification
│   ├── pii/                      # PII detection and redaction
│   │   ├── __init__.py
│   │   ├── pii_detector.py       # PII detection using Comprehend
│   │   ├── pii_redactor.py       # PII redaction logic
│   │   └── pii_patterns.py       # Custom PII patterns
│   ├── monitoring/               # Monitoring and metrics
│   │   ├── __init__.py
│   │   ├── metrics.py            # CloudWatch custom metrics
│   │   ├── alerts.py             # Alert configuration
│   │   └── logging.py            # Structured logging
│   ├── billing/                  # Usage tracking and billing
│   │   ├── __init__.py
│   │   ├── usage_tracker.py      # Usage tracking logic
│   │   ├── cost_calculator.py    # Cost calculation
│   │   └── billing_reporter.py   # Billing report generation
│   ├── utils/                    # Common utilities
│   │   ├── __init__.py
│   │   ├── text_normalizer.py    # Text normalization
│   │   ├── validators.py         # Input validation
│   │   ├── aws_clients.py        # AWS service clients
│   │   └── constants.py          # Application constants
│   └── models/                   # Data models
│       ├── __init__.py
│       ├── request_models.py     # Request data models
│       ├── response_models.py    # Response data models
│       └── job_models.py         # Job-related models
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   │   ├── test_handlers/
│   │   ├── test_cache/
│   │   ├── test_error_handling/
│   │   ├── test_pii/
│   │   └── test_utils/
│   ├── integration/              # Integration tests
│   │   ├── test_api_integration.py
│   │   ├── test_dynamodb_integration.py
│   │   └── test_comprehend_integration.py
│   ├── load/                     # Load tests
│   │   ├── load_test_sync.py
│   │   └── load_test_async.py
│   └── fixtures/                 # Test fixtures
│       ├── sample_texts.json
│       └── mock_responses.json
├── cloudformation/               # Infrastructure templates
│   ├── template.yaml             # Main SAM template
│   ├── monitoring.yaml           # Monitoring resources
│   ├── billing.yaml              # Billing infrastructure
│   └── security.yaml             # Security configurations
├── scripts/                      # Utility scripts
│   ├── deploy.sh                 # Deployment script
│   ├── setup_monitoring.py       # Monitoring setup
│   ├── generate_billing_report.py # Billing reports
│   └── run_tests.py              # Test runner
├── events/                       # Test events for local development
│   ├── sync_event.json
│   ├── async_event.json
│   └── status_event.json
├── docs/                         # Documentation
├── .github/                      # GitHub Actions workflows
│   └── workflows/
│       ├── deploy.yml
│       ├── test.yml
│       └── security-scan.yml
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pytest.ini                   # Pytest configuration
├── .flake8                       # Flake8 configuration
├── .pre-commit-config.yaml       # Pre-commit hooks
├── Makefile                      # Development commands
└── README.md                     # Project overview
```

---

## Code Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Line length: 88 characters (Black formatter default)
# Import order: Standard library, third-party, local imports
# Docstrings: Google style

def analyze_sentiment(text: str, options: Optional[Dict] = None) -> SentimentResult:
    """
    Analyze sentiment of the given text.
    
    Args:
        text: The text to analyze (max 5000 characters)
        options: Optional analysis parameters
        
    Returns:
        SentimentResult object containing sentiment analysis
        
    Raises:
        ValidationError: If text is invalid
        ServiceError: If analysis fails
    """
    # Implementation here
    pass
```

### Code Formatting

We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check formatting
black --check src/ tests/
isort --check-only src/ tests/
```

### Type Hints

All functions must include type hints:

```python
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class SentimentResult:
    sentiment: str
    score: float
    confidence: float
    language_code: str

def process_text(
    text: str, 
    options: Optional[Dict[str, Union[str, bool]]] = None
) -> SentimentResult:
    """Process text with type hints."""
    pass
```

### Error Handling

Use custom exception classes and proper error handling:

```python
class AuraStreamError(Exception):
    """Base exception for AuraStream errors."""
    pass

class ValidationError(AuraStreamError):
    """Raised when input validation fails."""
    pass

class ServiceError(AuraStreamError):
    """Raised when external service fails."""
    pass

def validate_text(text: str) -> None:
    """Validate input text."""
    if not text or not text.strip():
        raise ValidationError("Text cannot be empty")
    
    if len(text) > 5000:
        raise ValidationError("Text exceeds maximum length of 5000 characters")
```

### Logging

Use structured logging with appropriate levels:

```python
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

def log_analysis_request(text: str, options: Dict[str, Any]) -> None:
    """Log analysis request with structured data."""
    logger.info(
        "Analysis request received",
        extra={
            "text_length": len(text),
            "has_options": bool(options),
            "language_code": options.get("language_code"),
            "include_confidence": options.get("include_confidence", True)
        }
    )

def log_analysis_result(result: SentimentResult, processing_time_ms: int) -> None:
    """Log analysis result."""
    logger.info(
        "Analysis completed",
        extra={
            "sentiment": result.sentiment,
            "score": result.score,
            "confidence": result.confidence,
            "processing_time_ms": processing_time_ms
        }
    )
```

---

## Development Workflow

### Git Workflow

We use **Git Flow** with the following branch structure:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Feature development branches
- **hotfix/***: Critical bug fixes
- **release/***: Release preparation branches

#### Branch Naming Convention

```bash
# Feature branches
feature/add-caching-layer
feature/implement-pii-detection
feature/enhance-error-handling

# Bug fix branches
bugfix/fix-cache-ttl-issue
bugfix/resolve-rate-limiting-bug

# Hotfix branches
hotfix/critical-security-patch
hotfix/fix-production-outage
```

#### Commit Message Format

We use **Conventional Commits**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

**Examples**:
```bash
feat(cache): implement sentiment result caching
fix(api): resolve rate limiting validation error
docs(api): update API reference documentation
test(handlers): add unit tests for sync handler
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Develop and Test**
   ```bash
   # Make your changes
   # Run tests
   make test
   # Run linting
   make lint
   # Commit changes
   git add .
   git commit -m "feat: implement your feature"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

4. **Code Review**
   - At least 2 reviewers required
   - All CI checks must pass
   - Address review feedback

5. **Merge**
   - Squash and merge to develop
   - Delete feature branch

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-boto3]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.2.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

---

## Testing Guidelines

### Test Structure

#### Unit Tests

Test individual functions and classes in isolation:

```python
# tests/unit/test_cache/test_sentiment_cache.py
import pytest
from unittest.mock import Mock, patch
from src.cache.sentiment_cache import SentimentCache

class TestSentimentCache:
    def test_cache_hit_returns_cached_result(self):
        """Test that cache hit returns cached result."""
        cache = SentimentCache()
        text = "I love this product!"
        expected_result = {"sentiment": "POSITIVE", "score": 0.9}
        
        # Mock DynamoDB response
        with patch('src.cache.sentiment_cache.dynamodb') as mock_db:
            mock_db.get_item.return_value = {
                'Item': {
                    'text_hash': 'abc123',
                    'sentiment_result': expected_result,
                    'ttl': 1234567890
                }
            }
            
            result = cache.get_cached_result(text)
            assert result == expected_result

    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        cache = SentimentCache()
        text = "I love this product!"
        
        with patch('src.cache.sentiment_cache.dynamodb') as mock_db:
            mock_db.get_item.return_value = {}
            
            result = cache.get_cached_result(text)
            assert result is None
```

#### Integration Tests

Test interactions between components:

```python
# tests/integration/test_api_integration.py
import pytest
import json
from src.handlers.sync_handler import lambda_handler

class TestSyncHandlerIntegration:
    def test_sync_analysis_success(self, mock_comprehend):
        """Test successful synchronous analysis."""
        event = {
            "httpMethod": "POST",
            "path": "/analyze/sync",
            "body": json.dumps({
                "text": "I love this product!"
            }),
            "headers": {
                "X-API-Key": "test-api-key"
            }
        }
        
        # Mock Comprehend response
        mock_comprehend.detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.9,
                'Negative': 0.05,
                'Neutral': 0.03,
                'Mixed': 0.02
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['sentiment'] == 'POSITIVE'
        assert body['score'] == 0.9
```

#### Load Tests

Test system performance under load:

```python
# tests/load/load_test_sync.py
import asyncio
import aiohttp
import time
from typing import List

async def test_sync_endpoint_load():
    """Test sync endpoint under load."""
    url = "http://localhost:3000/analyze/sync"
    headers = {"X-API-Key": "test-key", "Content-Type": "application/json"}
    payload = {"text": "This is a test message for load testing"}
    
    async def make_request(session):
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        # Send 100 concurrent requests
        tasks = [make_request(session) for _ in range(100)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        successful_requests = sum(1 for r in results if 'sentiment' in r)
        avg_response_time = (end_time - start_time) / len(results)
        
        assert successful_requests >= 95  # 95% success rate
        assert avg_response_time < 1.0  # Under 1 second average
```

### Test Configuration

#### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    load: Load tests
    slow: Slow running tests
```

#### Test Fixtures

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock
from moto import mock_dynamodb, mock_s3
import boto3

@pytest.fixture
def mock_comprehend():
    """Mock AWS Comprehend service."""
    with patch('src.utils.aws_clients.comprehend') as mock:
        mock.detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {'Positive': 0.9, 'Negative': 0.05, 'Neutral': 0.03, 'Mixed': 0.02}
        }
        yield mock

@pytest.fixture
def dynamodb_table():
    """Create DynamoDB table for testing."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-sentiment-cache',
            KeySchema=[{'AttributeName': 'text_hash', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'text_hash', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table

@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        'positive': "I absolutely love this product! It's amazing!",
        'negative': "This is the worst product I've ever used.",
        'neutral': "The product arrived on time and as described.",
        'mixed': "The product is good but the customer service is terrible."
    }
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration
pytest tests/load/ -m load

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_handlers/test_sync_handler.py

# Run specific test function
pytest tests/unit/test_handlers/test_sync_handler.py::TestSyncHandler::test_successful_analysis
```

---

## Deployment Process

### Environment Configuration

#### Development Environment

```bash
# Deploy to development
make deploy-dev

# Or manually
sam build
sam deploy --config-env dev --no-confirm-changeset
```

#### Staging Environment

```bash
# Deploy to staging
make deploy-staging

# Or manually
sam build
sam deploy --config-env staging --no-confirm-changeset
```

#### Production Environment

```bash
# Deploy to production (requires approval)
make deploy-prod

# Or manually
sam build
sam deploy --config-env prod --confirm-changeset
```

### Deployment Scripts

#### Makefile

```makefile
# Makefile
.PHONY: help setup test lint type-check deploy-dev deploy-staging deploy-prod

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Setup development environment
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test: ## Run all tests
	pytest tests/ -v

lint: ## Run linting
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

type-check: ## Run type checking
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

deploy-dev: ## Deploy to development
	sam build
	sam deploy --config-env dev --no-confirm-changeset

deploy-staging: ## Deploy to staging
	sam build
	sam deploy --config-env staging --no-confirm-changeset

deploy-prod: ## Deploy to production
	sam build
	sam deploy --config-env prod --confirm-changeset

clean: ## Clean build artifacts
	rm -rf .aws-sam/
	rm -rf dist/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
```

#### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-dev}
STACK_NAME="aurastream-${ENVIRONMENT}"

echo "Deploying to ${ENVIRONMENT} environment..."

# Build the application
echo "Building application..."
sam build

# Deploy based on environment
case $ENVIRONMENT in
  dev|staging)
    echo "Deploying to ${ENVIRONMENT}..."
    sam deploy --config-env ${ENVIRONMENT} --no-confirm-changeset
    ;;
  prod)
    echo "Deploying to production..."
    sam deploy --config-env ${ENVIRONMENT} --confirm-changeset
    ;;
  *)
    echo "Invalid environment: ${ENVIRONMENT}"
    echo "Usage: $0 [dev|staging|prod]"
    exit 1
    ;;
esac

echo "Deployment completed successfully!"
```

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy AuraStream

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run linting
        run: |
          flake8 src/ tests/
          black --check src/ tests/
          isort --check-only src/ tests/
          
      - name: Run type checking
        run: mypy src/
        
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  deploy-dev:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Deploy to development
        run: make deploy-dev

  deploy-prod:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
          aws-region: us-east-1
          
      - name: Deploy to production
        run: make deploy-prod
```

---

## Contributing Guidelines

### Code Review Process

1. **Self Review**: Review your own code before submitting
2. **Automated Checks**: Ensure all CI checks pass
3. **Peer Review**: At least 2 reviewers required
4. **Testing**: All new code must have tests
5. **Documentation**: Update documentation as needed

### Review Checklist

#### For Authors

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No sensitive data in code
- [ ] Error handling is implemented
- [ ] Logging is appropriate

#### For Reviewers

- [ ] Code is readable and maintainable
- [ ] Logic is correct and efficient
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Tests are comprehensive
- [ ] Documentation is accurate

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive data exposed
```

---

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Found

```bash
# Error: Unable to locate credentials
# Solution: Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

#### 2. SAM Build Fails

```bash
# Error: Build failed
# Solution: Check Docker is running
docker --version
# Restart Docker if needed
# Clear SAM cache
rm -rf .aws-sam/
sam build
```

#### 3. Local API Gateway Not Starting

```bash
# Error: Port already in use
# Solution: Use different port
sam local start-api --port 3001
# Or kill process using port
lsof -ti:3000 | xargs kill -9
```

#### 4. Tests Failing

```bash
# Error: Import errors
# Solution: Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements-dev.txt

# Error: AWS service errors
# Solution: Use moto for mocking
pip install moto
```

### Debugging Tips

#### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. Use AWS X-Ray

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('my_function')
def my_function():
    pass
```

#### 3. Local Testing with Real AWS Services

```bash
# Use AWS CLI to test services
aws comprehend detect-sentiment --text "I love this product!" --language-code en
aws dynamodb get-item --table-name test-table --key '{"id":{"S":"test"}}'
```

#### 4. Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    # Your code here
    pass

# Profile the function
cProfile.run('profile_function()', 'profile_output.prof')

# Analyze results
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(10)
```

### Getting Help

1. **Check Documentation**: Review this guide and API documentation
2. **Search Issues**: Look for similar issues in GitHub
3. **Ask Questions**: Create a GitHub issue with detailed information
4. **Contact Team**: Reach out to the development team

### Useful Commands

```bash
# Development
make setup          # Setup development environment
make test           # Run all tests
make lint           # Run linting
make format         # Format code
make clean          # Clean build artifacts

# Deployment
make deploy-dev     # Deploy to development
make deploy-staging # Deploy to staging
make deploy-prod    # Deploy to production

# AWS
aws sts get-caller-identity  # Check AWS credentials
aws cloudformation list-stacks  # List CloudFormation stacks
aws logs describe-log-groups  # List CloudWatch log groups
```

---

This development guide provides comprehensive instructions for setting up, developing, testing, and deploying the AuraStream project. Follow these guidelines to ensure consistent, high-quality code and smooth development workflows.
