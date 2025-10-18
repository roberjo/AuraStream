"""Unit tests for utility modules."""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.utils.json_encoder import AuraStreamJSONEncoder, json_dumps
from src.utils.constants import ERROR_CODES, SENTIMENT_TYPES, MAX_TEXT_LENGTH_SYNC, MAX_TEXT_LENGTH_ASYNC


class TestAuraStreamJSONEncoder:
    """Test the custom JSON encoder."""
    
    def test_datetime_serialization(self):
        """Test datetime serialization."""
        dt = datetime.now(timezone.utc)
        encoder = AuraStreamJSONEncoder()
        result = encoder.default(dt)
        assert result == dt.isoformat()
    
    def test_date_serialization(self):
        """Test date serialization."""
        from datetime import date
        d = date.today()
        encoder = AuraStreamJSONEncoder()
        result = encoder.default(d)
        assert result == d.isoformat()
    
    def test_decimal_serialization(self):
        """Test decimal serialization."""
        from decimal import Decimal
        dec = Decimal('123.45')
        encoder = AuraStreamJSONEncoder()
        result = encoder.default(dec)
        assert result == 123.45
    
    def test_pydantic_model_serialization(self):
        """Test Pydantic model serialization."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        encoder = AuraStreamJSONEncoder()
        result = encoder.default(model)
        assert result == {"name": "test", "value": 42}
    
    def test_legacy_pydantic_model_serialization(self):
        """Test legacy Pydantic model serialization."""
        class LegacyModel:
            def dict(self):
                return {"name": "test", "value": 42}
        
        model = LegacyModel()
        encoder = AuraStreamJSONEncoder()
        result = encoder.default(model)
        assert result == {"name": "test", "value": 42}
    
    def test_unknown_type_raises_error(self):
        """Test that unknown types raise TypeError."""
        encoder = AuraStreamJSONEncoder()
        with pytest.raises(TypeError):
            encoder.default(object())


class TestJsonDumps:
    """Test the json_dumps function."""
    
    def test_datetime_serialization(self):
        """Test datetime serialization in json_dumps."""
        dt = datetime.now(timezone.utc)
        data = {"timestamp": dt}
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed["timestamp"] == dt.isoformat()
    
    def test_nested_datetime_serialization(self):
        """Test nested datetime serialization."""
        dt = datetime.now(timezone.utc)
        data = {
            "nested": {
                "timestamp": dt,
                "value": 42
            }
        }
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed["nested"]["timestamp"] == dt.isoformat()
        assert parsed["nested"]["value"] == 42
    
    def test_pydantic_model_serialization(self):
        """Test Pydantic model serialization in json_dumps."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        data = {"model": model}
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed["model"] == {"name": "test", "value": 42}


class TestConstants:
    """Test constants module."""
    
    def test_error_codes_structure(self):
        """Test error codes structure."""
        assert isinstance(ERROR_CODES, dict)
        assert 'VALIDATION_ERROR' in ERROR_CODES
        assert 'INTERNAL_ERROR' in ERROR_CODES
        assert 'RATE_LIMIT_EXCEEDED' in ERROR_CODES
        assert 'SERVICE_UNAVAILABLE' in ERROR_CODES
    
    def test_error_codes_values(self):
        """Test error codes have valid HTTP status codes."""
        for error_type, status_code in ERROR_CODES.items():
            assert isinstance(status_code, int)
            assert 400 <= status_code <= 599
    
    def test_sentiment_types(self):
        """Test sentiment types."""
        assert isinstance(SENTIMENT_TYPES, list)
        assert 'POSITIVE' in SENTIMENT_TYPES
        assert 'NEGATIVE' in SENTIMENT_TYPES
        assert 'NEUTRAL' in SENTIMENT_TYPES
        assert 'MIXED' in SENTIMENT_TYPES
    
    def test_text_length_limits(self):
        """Test text length limits."""
        assert isinstance(MAX_TEXT_LENGTH_SYNC, int)
        assert isinstance(MAX_TEXT_LENGTH_ASYNC, int)
        assert MAX_TEXT_LENGTH_SYNC > 0
        assert MAX_TEXT_LENGTH_ASYNC > 0
        assert MAX_TEXT_LENGTH_ASYNC > MAX_TEXT_LENGTH_SYNC  # Async should allow longer text


class TestValidators:
    """Test input validators."""
    
    def test_validate_text_security_safe_text(self):
        """Test security validation with safe text."""
        from src.utils.validators import InputValidator
        
        safe_text = "This is a normal, safe text with no threats."
        result = InputValidator.validate_text_security(safe_text)
        
        assert result['is_safe'] is True
        assert result['threats'] == []
    
    def test_validate_text_security_sql_injection(self):
        """Test security validation with SQL injection."""
        from src.utils.validators import InputValidator
        
        malicious_text = "'; DROP TABLE users; --"
        result = InputValidator.validate_text_security(malicious_text)
        
        assert result['is_safe'] is False
        assert 'SQL_INJECTION' in result['threats']
    
    def test_validate_text_security_xss(self):
        """Test security validation with XSS."""
        from src.utils.validators import InputValidator
        
        malicious_text = "<script>alert('xss')</script>"
        result = InputValidator.validate_text_security(malicious_text)
        
        assert result['is_safe'] is False
        assert 'XSS' in result['threats']
    
    def test_validate_text_security_command_injection(self):
        """Test security validation with command injection."""
        from src.utils.validators import InputValidator
        
        malicious_text = "; rm -rf /"
        result = InputValidator.validate_text_security(malicious_text)
        
        assert result['is_safe'] is False
        assert 'COMMAND_INJECTION' in result['threats']
    
    def test_validate_text_security_path_traversal(self):
        """Test security validation with path traversal."""
        from src.utils.validators import InputValidator
        
        malicious_text = "../../../etc/passwd"
        result = InputValidator.validate_text_security(malicious_text)
        
        assert result['is_safe'] is False
        assert 'PATH_TRAVERSAL' in result['threats']
    
    def test_validate_text_security_multiple_threats(self):
        """Test security validation with multiple threats."""
        from src.utils.validators import InputValidator
        
        malicious_text = "'; DROP TABLE users; --<script>alert('xss')</script>"
        result = InputValidator.validate_text_security(malicious_text)
        
        assert result['is_safe'] is False
        assert len(result['threats']) >= 2
        assert 'SQL_INJECTION' in result['threats']
        assert 'XSS' in result['threats']


class TestAWSClients:
    """Test AWS clients utility."""
    
    @patch('boto3.client')
    def test_aws_clients_initialization(self, mock_boto_client):
        """Test AWS clients initialization."""
        from src.utils.aws_clients import aws_clients
        
        # Test that clients are initialized
        assert hasattr(aws_clients, 'dynamodb')
        assert hasattr(aws_clients, 's3')
        assert hasattr(aws_clients, 'stepfunctions')
        assert hasattr(aws_clients, 'comprehend')
        assert hasattr(aws_clients, 'cloudwatch')
    
    @patch('boto3.client')
    def test_aws_clients_region_configuration(self, mock_boto_client):
        """Test AWS clients region configuration."""
        from src.utils.aws_clients import aws_clients
        
        # Verify that boto3.client was called with correct region
        mock_boto_client.assert_called()
        calls = mock_boto_client.call_args_list
        
        # Check that at least one call includes region_name
        region_calls = [call for call in calls if 'region_name' in call[1]]
        assert len(region_calls) > 0
