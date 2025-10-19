"""Unit tests for utility modules."""

import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import BaseModel

from src.utils.constants import (
    ERROR_CODES,
    MAX_TEXT_LENGTH_ASYNC,
    MAX_TEXT_LENGTH_SYNC,
    SENTIMENT_TYPES,
)
from src.utils.json_encoder import json_dumps
from src.utils.validators import InputValidator


class TestAuraStreamJSONEncoder:
    """Test the custom JSON encoder."""

    def test_datetime_serialization(self):
        """Test datetime serialization."""
        dt = datetime(2023, 12, 25, 10, 30, 45, tzinfo=timezone.utc)
        result = json_dumps({"timestamp": dt})
        data = json.loads(result)
        assert data["timestamp"] == "2023-12-25T10:30:45+00:00"

    def test_date_serialization(self):
        """Test date serialization."""
        d = date(2023, 12, 25)
        result = json_dumps({"date": d})
        data = json.loads(result)
        assert data["date"] == "2023-12-25"

    def test_decimal_serialization(self):
        """Test decimal serialization."""
        dec = Decimal("123.45")
        result = json_dumps({"amount": dec})
        data = json.loads(result)
        assert data["amount"] == 123.45

    def test_pydantic_model_serialization(self):
        """Test Pydantic model serialization."""

        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        result = json_dumps({"model": model})
        data = json.loads(result)
        assert data["model"] == {"name": "test", "value": 42}

    def test_legacy_pydantic_model_serialization(self):
        """Test legacy Pydantic model serialization."""

        class LegacyModel(BaseModel):
            name: str
            value: int

            def dict(self):
                return {"name": self.name, "value": self.value}

        model = LegacyModel(name="test", value=42)
        result = json_dumps({"model": model})
        data = json.loads(result)
        assert data["model"] == {"name": "test", "value": 42}

    def test_unknown_type_raises_error(self):
        """Test that unknown types raise TypeError."""

        class UnknownType:
            pass

        with pytest.raises(TypeError):
            json_dumps({"unknown": UnknownType()})


class TestJsonDumps:
    """Test the json_dumps utility function."""

    def test_datetime_serialization(self):
        """Test datetime serialization with json_dumps."""
        dt = datetime(2023, 12, 25, 10, 30, 45, tzinfo=timezone.utc)
        result = json_dumps({"timestamp": dt})
        data = json.loads(result)
        assert data["timestamp"] == "2023-12-25T10:30:45+00:00"

    def test_nested_datetime_serialization(self):
        """Test nested datetime serialization."""
        dt = datetime(2023, 12, 25, 10, 30, 45, tzinfo=timezone.utc)
        data = {"user": {"created_at": dt, "profile": {"last_login": dt}}}
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed["user"]["created_at"] == "2023-12-25T10:30:45+00:00"
        assert parsed["user"]["profile"]["last_login"] == "2023-12-25T10:30:45+00:00"

    def test_pydantic_model_serialization(self):
        """Test Pydantic model serialization with json_dumps."""

        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        result = json_dumps({"model": model})
        data = json.loads(result)
        assert data["model"] == {"name": "test", "value": 42}


class TestConstants:
    """Test constants module."""

    def test_error_codes_structure(self):
        """Test error codes structure."""
        assert isinstance(ERROR_CODES, dict)
        assert "VALIDATION_ERROR" in ERROR_CODES
        assert "INTERNAL_ERROR" in ERROR_CODES
        assert "SERVICE_UNAVAILABLE" in ERROR_CODES

    def test_error_codes_values(self):
        """Test error codes values."""
        assert ERROR_CODES["VALIDATION_ERROR"] == 400
        assert ERROR_CODES["INTERNAL_ERROR"] == 500
        assert ERROR_CODES["SERVICE_UNAVAILABLE"] == 503

    def test_sentiment_types(self):
        """Test sentiment types."""
        assert isinstance(SENTIMENT_TYPES, list)
        assert "POSITIVE" in SENTIMENT_TYPES
        assert "NEGATIVE" in SENTIMENT_TYPES
        assert "NEUTRAL" in SENTIMENT_TYPES
        assert "MIXED" in SENTIMENT_TYPES

    def test_text_length_limits(self):
        """Test text length limits."""
        assert MAX_TEXT_LENGTH_SYNC == 5000
        assert MAX_TEXT_LENGTH_ASYNC == 1048576


class TestValidators:
    """Test validation utilities."""

    def test_validate_text_security_safe_text(self):
        """Test security validation with safe text."""
        safe_text = "This is a normal, safe text for sentiment analysis."
        result = InputValidator.validate_text_security(safe_text)
        assert result["is_safe"] is True
        assert result["threats"] == []

    def test_validate_text_security_sql_injection(self):
        """Test security validation with SQL injection attempt."""
        malicious_text = "'; DROP TABLE users; --"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False
        assert len(result["threats"]) > 0
        assert any("sql" in threat["type"].lower() for threat in result["threats"])

    def test_validate_text_security_xss(self):
        """Test security validation with XSS attempt."""
        malicious_text = "<script>alert('xss')</script>"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False
        assert len(result["threats"]) > 0
        assert any("xss" in threat["type"].lower() for threat in result["threats"])

    def test_validate_text_security_command_injection(self):
        """Test security validation with command injection attempt."""
        malicious_text = "test; rm -rf /"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False
        assert len(result["threats"]) > 0
        assert any("command" in threat["type"].lower() for threat in result["threats"])

    def test_validate_text_security_path_traversal(self):
        """Test security validation with path traversal attempt."""
        malicious_text = "../../../etc/passwd"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False
        assert len(result["threats"]) > 0
        assert any("path" in threat["type"].lower() for threat in result["threats"])

    def test_validate_text_security_multiple_threats(self):
        """Test security validation with multiple threats."""
        malicious_text = "'; DROP TABLE users; -- <script>alert('xss')</script>"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False
        assert len(result["threats"]) > 1
        threat_types = [threat["type"].lower() for threat in result["threats"]]
        assert any("sql" in t for t in threat_types)
        assert any("xss" in t for t in threat_types)

    def test_validate_text_security_empty_text(self):
        """Test security validation with empty text."""
        result = InputValidator.validate_text_security("")
        assert result["is_safe"] is True
        assert result["threats"] == []

    def test_validate_text_security_whitespace_only(self):
        """Test security validation with whitespace-only text."""
        result = InputValidator.validate_text_security("   \n\t   ")
        assert result["is_safe"] is True
        assert result["threats"] == []

    def test_validate_text_security_unicode_text(self):
        """Test security validation with unicode text."""
        unicode_text = "Hello 世界! This is a test with unicode characters: 🚀"
        result = InputValidator.validate_text_security(unicode_text)
        assert result["is_safe"] is True
        assert result["threats"] == []

    def test_validate_text_security_large_text(self):
        """Test security validation with large text."""
        large_text = "This is a test sentence. " * 1000  # ~25KB
        result = InputValidator.validate_text_security(large_text)
        assert result["is_safe"] is True
        assert result["threats"] == []

    def test_validate_text_security_threat_severity(self):
        """Test that threats have appropriate severity levels."""
        malicious_text = "'; DROP TABLE users; --"
        result = InputValidator.validate_text_security(malicious_text)
        assert result["is_safe"] is False

        for threat in result["threats"]:
            assert "severity" in threat
            assert threat["severity"] in ["low", "medium", "high", "critical"]
            assert "type" in threat
            assert "pattern" in threat
