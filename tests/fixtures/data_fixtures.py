"""Data fixtures for testing."""


import pytest


@pytest.fixture
def sample_texts():
    """Sample texts for sentiment analysis testing."""
    return {
        "positive": "I absolutely love this product! It's amazing and works perfectly.",
        "negative": "This is terrible. I hate it and it doesn't work at all.",
        "neutral": "The product arrived on time and was packaged well.",
        "mixed": "The product is good but the customer service was terrible.",
        "long_text": "This is a very long text. " * 1000,  # ~25KB
        "very_long_text": "This is an extremely long text. " * 10000,  # ~250KB
        "empty": "",
        "whitespace": "   \n\t   ",
        "special_chars": "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?",
        "unicode": "Hello 世界! 🌟 This is a test with unicode characters.",
        "newlines": "Line 1\nLine 2\nLine 3",
        "tabs": "Column1\tColumn2\tColumn3",
    }


@pytest.fixture
def sample_sentiment_scores():
    """Sample sentiment scores for testing."""
    return {
        "positive": {
            "Positive": 0.95,
            "Negative": 0.02,
            "Neutral": 0.02,
            "Mixed": 0.01,
        },
        "negative": {
            "Positive": 0.02,
            "Negative": 0.95,
            "Neutral": 0.02,
            "Mixed": 0.01,
        },
        "neutral": {"Positive": 0.25, "Negative": 0.25, "Neutral": 0.45, "Mixed": 0.05},
        "mixed": {"Positive": 0.40, "Negative": 0.40, "Neutral": 0.15, "Mixed": 0.05},
    }


@pytest.fixture
def sample_pii_data():
    """Sample PII data for testing."""
    return {
        "email": "Contact me at john.doe@example.com for more info",
        "phone": "Call me at (555) 123-4567 or 555-123-4567",
        "ssn": "My SSN is 123-45-6789",
        "credit_card": "My card number is 4111 1111 1111 1111",
        "address": "I live at 123 Main St, Anytown, NY 12345",
        "name": "My name is John Doe",
        "no_pii": "This text contains no personal information",
        "mixed_pii": "Hi, I'm John Doe and my email is john@example.com",
    }


@pytest.fixture
def sample_validation_errors():
    """Sample validation errors for testing."""
    return {
        "empty_text": {
            "text": "",
            "expected_error": "String should have at least 1 character",
        },
        "too_long_text": {
            "text": "x" * 1048577,  # Exceeds 1MB limit
            "expected_error": "String should have at most 1048576 characters",
        },
        "invalid_json": {
            "body": "invalid json",
            "expected_error": "Invalid JSON in request body",
        },
        "missing_text": {
            "body": '{"source_id": "test"}',
            "expected_error": "Field required",
        },
        "invalid_source_id": {
            "body": '{"text": "test", "source_id": ""}',
            "expected_error": "String should have at least 1 character",
        },
    }


@pytest.fixture
def sample_security_threats():
    """Sample security threats for testing."""
    return {
        "sql_injection": "'; DROP TABLE users; --",
        "xss": "<script>alert('xss')</script>",
        "command_injection": "; rm -rf /",
        "path_traversal": "../../../etc/passwd",
        "no_threat": "This is a normal text with no security threats",
    }


@pytest.fixture
def sample_cache_data():
    """Sample cache data for testing."""
    return {
        "hit": {
            "sentiment": "POSITIVE",
            "score": 0.95,
            "language_code": "en",
            "confidence": True,
            "pii_detected": False,
            "processing_time_ms": 150,
        },
        "miss": None,
        "expired": {
            "sentiment": "POSITIVE",
            "score": 0.95,
            "language_code": "en",
            "confidence": True,
            "pii_detected": False,
            "processing_time_ms": 150,
            "cached_at": "2023-01-01T00:00:00Z",  # Old timestamp
        },
    }


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for testing."""
    return {
        "api_usage": {
            "endpoint": "/analyze/sync",
            "customer_id": "test-customer",
            "response_time": 150,
            "status_code": 200,
        },
        "sentiment_analysis": {
            "sentiment": "POSITIVE",
            "text_length": 50,
            "processing_time": 150,
        },
        "cache_metrics": {"hit": True, "miss": False},
        "pii_detection": {"detected": True, "types": ["EMAIL", "PHONE"]},
        "error_metrics": {"error_type": "VALIDATION_ERROR", "handler": "sync_handler"},
    }


@pytest.fixture
def sample_step_function_data():
    """Sample Step Function execution data."""
    return {
        "execution_arn": (
            "arn:aws:states:us-east-1:123456789012:execution:"
            "aurastream-processor:test-execution-123"
        ),
        "state_machine_arn": (
            "arn:aws:states:us-east-1:123456789012:stateMachine:"
            "aurastream-processor"
        ),
        "input": {
            "job_id": "test-job-123",
            "text": "I love this product!",
            "source_id": "test-source",
            "options": {"include_confidence": True, "include_pii_detection": True},
        },
        "status": "RUNNING",
    }
