# AuraStream Testing Guide

This document provides comprehensive information about the AuraStream testing framework, including setup, execution, and best practices.

## 🧪 Test Structure

```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_utils.py       # Utility functions tests
│   ├── test_models.py      # Data model tests
│   ├── test_cache.py       # Cache functionality tests
│   ├── test_pii_detector.py # PII detection tests
│   ├── test_sync_handler.py # Sync handler tests
│   ├── test_async_handler.py # Async handler tests
│   └── test_status_handler.py # Status handler tests
├── integration/            # Integration tests
│   └── test_lambda_integration.py # End-to-end Lambda tests
├── performance/            # Performance and load tests
│   └── test_performance.py # Performance benchmarks
├── fixtures/               # Test fixtures and utilities
│   ├── aws_fixtures.py    # AWS service mocks
│   └── data_fixtures.py   # Sample data for testing
└── conftest.py            # Pytest configuration and shared fixtures
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-performance   # Performance tests only

# Run tests with coverage
make test-coverage

# Run tests in parallel (faster)
make test-parallel
```

## 📊 Coverage Requirements

- **Minimum Coverage**: 80%
- **Branch Coverage**: Enabled
- **Coverage Reports**: HTML, XML, and terminal output
- **CI Gate**: Tests fail if coverage drops below threshold

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
addopts = --cov=src --cov-fail-under=80 --cov-branch
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
    aws: Tests requiring AWS services
```

### Coverage Configuration (`.coveragerc`)

```ini
[run]
source = src
branch = True
omit = */tests/*, */__pycache__/*

[report]
fail_under = 80
show_missing = True
```

## 🧩 Test Categories

### Unit Tests

Test individual functions and classes in isolation:

```python
@pytest.mark.unit
def test_sentiment_analysis():
    """Test sentiment analysis functionality."""
    # Test implementation
```

**Coverage**: All modules in `src/`
**Execution Time**: < 1 second per test
**Dependencies**: Minimal mocking

### Integration Tests

Test complete workflows and service interactions:

```python
@pytest.mark.integration
def test_sync_handler_full_workflow():
    """Test complete sync handler workflow."""
    # Integration test implementation
```

**Coverage**: End-to-end Lambda handler workflows
**Execution Time**: 1-5 seconds per test
**Dependencies**: AWS service mocks (moto)

### Performance Tests

Test response times and resource usage:

```python
@pytest.mark.performance
@pytest.mark.slow
def test_sync_handler_response_time():
    """Test sync handler response time under load."""
    # Performance test implementation
```

**Coverage**: Critical performance paths
**Execution Time**: 5-30 seconds per test
**Dependencies**: Load testing tools

## 🛠️ Test Fixtures

### AWS Fixtures

```python
@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing."""
    with mock_aws(['dynamodb', 's3', 'stepfunctions']):
        yield

@pytest.fixture
def sample_comprehend_response():
    """Sample Comprehend API response."""
    return {
        'Sentiment': 'POSITIVE',
        'SentimentScore': {'Positive': 0.95, 'Negative': 0.02},
        'LanguageCode': 'en'
    }
```

### Data Fixtures

```python
@pytest.fixture
def sample_texts():
    """Sample texts for sentiment analysis testing."""
    return {
        'positive': "I love this product!",
        'negative': "This is terrible.",
        'neutral': "The product works as expected."
    }
```

## 🔒 Security Testing

### Security Scans

```bash
# Run security scans
make security

# Generate security reports
make security-json
```

### Security Test Categories

- **Input Validation**: SQL injection, XSS, command injection
- **Authentication**: API key validation, rate limiting
- **Data Protection**: PII detection and redaction
- **Dependency Vulnerabilities**: pip-audit and safety checks

## 📈 Performance Testing

### Performance Benchmarks

```bash
# Run performance tests
make test-performance

# Run with memory profiling
python -m memory_profiler tests/performance/test_performance.py
```

### Performance Metrics

- **Response Time**: < 1 second for sync operations
- **Throughput**: > 100 requests/second
- **Memory Usage**: < 100MB increase for large text
- **Concurrent Load**: 10+ simultaneous requests

## 🚦 CI/CD Integration

### GitHub Actions Workflow

The CI pipeline includes:

1. **Test Suite**: Unit, integration, and performance tests
2. **Coverage Gate**: Fails if coverage < 80%
3. **Security Scanning**: pip-audit and safety checks
4. **Code Quality**: Black, isort, flake8, mypy
5. **Build Verification**: Package building and validation

### Coverage Gate

```yaml
- name: Run tests with coverage
  run: pytest --cov=src --cov-fail-under=80 --cov-report=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    fail_ci_if_error: true
```

## 🎯 Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive names that explain the scenario
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Single Responsibility**: One assertion per test concept
4. **Edge Cases**: Test boundary conditions and error scenarios
5. **Mocking**: Mock external dependencies appropriately

### Test Data

1. **Realistic Data**: Use realistic test data that mirrors production
2. **Edge Cases**: Include empty strings, special characters, large inputs
3. **Security Scenarios**: Test with potentially malicious input
4. **Performance Data**: Use large datasets for performance tests

### Maintenance

1. **Regular Updates**: Keep test dependencies updated
2. **Coverage Monitoring**: Monitor coverage trends over time
3. **Performance Baselines**: Track performance regression
4. **Security Updates**: Regular security vulnerability scans

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Mock Issues**: Verify mock configurations match actual usage
3. **Timing Issues**: Use appropriate timeouts for async operations
4. **Environment Variables**: Set required environment variables

### Debug Commands

```bash
# Run specific test with verbose output
pytest tests/unit/test_sync_handler.py::TestSyncHandler::test_successful_analysis -v -s

# Run tests with debugging
pytest --pdb tests/unit/test_sync_handler.py

# Run tests with coverage and debugging
pytest --cov=src --cov-report=html --pdb tests/unit/
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Moto Documentation](https://docs.getmoto.org/)
- [AWS Testing Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/testing-lambda.html)

## 🤝 Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Ensure tests are fast, reliable, and isolated
3. Add appropriate test markers (`@pytest.mark.unit`, etc.)
4. Update this documentation if adding new test categories
5. Ensure new code has adequate test coverage

## 📞 Support

For testing-related questions or issues:

- Create an issue in the GitHub repository
- Check existing test examples in the codebase
- Review the CI/CD logs for test failures
- Consult the team for complex testing scenarios
