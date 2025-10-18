"""Unit tests for PII detector module."""

import pytest
from unittest.mock import Mock, patch

from src.pii.pii_detector import PIIDetector


class TestPIIDetector:
    """Test PIIDetector class."""
    
    @pytest.fixture
    def pii_detector(self):
        """Create a PIIDetector instance for testing."""
        return PIIDetector()
    
    def test_pii_detector_initialization(self, pii_detector):
        """Test PII detector initialization."""
        assert pii_detector.pii_types == [
            'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 
            'ADDRESS', 'NAME', 'DATE_OF_BIRTH'
        ]
    
    def test_detect_email(self, pii_detector):
        """Test email detection."""
        text = "Contact me at john.doe@example.com for more info"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'EMAIL' in result['pii_types']
        assert len(result['pii_entities']) > 0
        
        # Check that email is found
        email_entities = [e for e in result['pii_entities'] if e['type'] == 'EMAIL']
        assert len(email_entities) > 0
        assert 'john.doe@example.com' in email_entities[0]['value']
    
    def test_detect_phone(self, pii_detector):
        """Test phone number detection."""
        text = "Call me at (555) 123-4567 or 555-123-4567"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'PHONE' in result['pii_types']
        assert len(result['pii_entities']) > 0
    
    def test_detect_ssn(self, pii_detector):
        """Test SSN detection."""
        text = "My SSN is 123-45-6789"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'SSN' in result['pii_types']
        assert len(result['pii_entities']) > 0
    
    def test_detect_credit_card(self, pii_detector):
        """Test credit card detection."""
        text = "My card number is 4111 1111 1111 1111"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'CREDIT_CARD' in result['pii_types']
        assert len(result['pii_entities']) > 0
    
    def test_detect_address(self, pii_detector):
        """Test address detection."""
        text = "I live at 123 Main St, Anytown, NY 12345"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'ADDRESS' in result['pii_types']
        assert len(result['pii_entities']) > 0
    
    def test_detect_name(self, pii_detector):
        """Test name detection."""
        text = "My name is John Doe"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert 'NAME' in result['pii_types']
        assert len(result['pii_entities']) > 0
    
    def test_detect_multiple_pii(self, pii_detector):
        """Test detection of multiple PII types."""
        text = "Hi, I'm John Doe and my email is john@example.com. Call me at (555) 123-4567"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert len(result['pii_types']) >= 3
        assert 'NAME' in result['pii_types']
        assert 'EMAIL' in result['pii_types']
        assert 'PHONE' in result['pii_types']
        assert len(result['pii_entities']) >= 3
    
    def test_no_pii_detected(self, pii_detector):
        """Test when no PII is detected."""
        text = "This text contains no personal information"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is False
        assert result['pii_types'] == []
        assert result['pii_entities'] == []
    
    def test_empty_text(self, pii_detector):
        """Test with empty text."""
        text = ""
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is False
        assert result['pii_types'] == []
        assert result['pii_entities'] == []
    
    def test_whitespace_only_text(self, pii_detector):
        """Test with whitespace-only text."""
        text = "   \n\t   "
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is False
        assert result['pii_types'] == []
        assert result['pii_entities'] == []
    
    def test_pii_entity_structure(self, pii_detector):
        """Test PII entity structure."""
        text = "Contact me at john.doe@example.com"
        result = pii_detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert len(result['pii_entities']) > 0
        
        entity = result['pii_entities'][0]
        assert 'type' in entity
        assert 'value' in entity
        assert 'start' in entity
        assert 'end' in entity
        assert 'confidence' in entity
        
        assert entity['type'] == 'EMAIL'
        assert entity['value'] == 'john.doe@example.com'
        assert isinstance(entity['start'], int)
        assert isinstance(entity['end'], int)
        assert isinstance(entity['confidence'], float)
        assert 0.0 <= entity['confidence'] <= 1.0
    
    def test_redact_pii(self, pii_detector):
        """Test PII redaction."""
        text = "Contact me at john.doe@example.com or call (555) 123-4567"
        result = pii_detector.detect_pii(text)
        
        redacted_text = pii_detector.redact_pii(text, result['pii_entities'])
        
        assert 'john.doe@example.com' not in redacted_text
        assert '(555) 123-4567' not in redacted_text
        assert '[REDACTED]' in redacted_text or '[EMAIL]' in redacted_text or '[PHONE]' in redacted_text
    
    def test_redact_pii_no_entities(self, pii_detector):
        """Test PII redaction with no entities."""
        text = "This text has no PII"
        entities = []
        
        redacted_text = pii_detector.redact_pii(text, entities)
        
        assert redacted_text == text
    
    def test_redact_pii_custom_replacement(self, pii_detector):
        """Test PII redaction with custom replacement."""
        text = "Contact me at john.doe@example.com"
        result = pii_detector.detect_pii(text)
        
        redacted_text = pii_detector.redact_pii(text, result['pii_entities'], replacement="[MASKED]")
        
        assert 'john.doe@example.com' not in redacted_text
        assert '[MASKED]' in redacted_text
    
    def test_validate_pii_types(self, pii_detector):
        """Test PII types validation."""
        # Test with valid PII types
        valid_types = ['EMAIL', 'PHONE']
        result = pii_detector._validate_pii_types(valid_types)
        assert result == valid_types
        
        # Test with invalid PII types (should be filtered out)
        mixed_types = ['EMAIL', 'INVALID_TYPE', 'PHONE']
        result = pii_detector._validate_pii_types(mixed_types)
        assert result == ['EMAIL', 'PHONE']
        
        # Test with empty list
        result = pii_detector._validate_pii_types([])
        assert result == pii_detector.pii_types  # Should return all types
    
    def test_custom_pii_types(self):
        """Test PII detector with custom PII types."""
        custom_types = ['EMAIL', 'PHONE']
        detector = PIIDetector(pii_types=custom_types)
        
        assert detector.pii_types == custom_types
        
        # Test detection with custom types
        text = "Contact me at john.doe@example.com or call (555) 123-4567"
        result = detector.detect_pii(text)
        
        assert result['pii_detected'] is True
        assert set(result['pii_types']).issubset(set(custom_types))
    
    @patch('src.pii.pii_detector.aws_clients')
    def test_detect_pii_aws_error(self, mock_aws_clients, pii_detector):
        """Test PII detection with AWS error."""
        # Mock AWS client error
        mock_comprehend = Mock()
        mock_aws_clients.comprehend = mock_comprehend
        mock_comprehend.detect_pii_entities.side_effect = Exception("AWS error")
        
        text = "Contact me at john.doe@example.com"
        result = pii_detector.detect_pii(text)
        
        # Should return safe default when AWS fails
        assert result['pii_detected'] is False
        assert result['pii_types'] == []
        assert result['pii_entities'] == []
        assert 'error' in result
