"""Tests for PII detection."""

from unittest.mock import Mock, patch

from src.pii.pii_detector import PIIDetector


class TestPIIDetector:
    """Test PII detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("src.pii.pii_detector.aws_clients") as mock_aws:
            mock_comprehend = Mock()
            mock_aws.get_comprehend_client.return_value = mock_comprehend
            self.detector = PIIDetector()

    def test_detect_pii_success(self):
        """Test successful PII detection."""
        mock_response = {
            "Entities": [
                {
                    "Type": "EMAIL",
                    "BeginOffset": 0,
                    "EndOffset": 10,
                    "Score": 0.99,
                },
                {
                    "Type": "PHONE",
                    "BeginOffset": 15,
                    "EndOffset": 25,
                    "Score": 0.95,
                },
            ],
            "Confidence": 0.97,
        }

        with patch.object(
            self.detector.comprehend, "detect_pii_entities"
        ) as mock_detect:
            mock_detect.return_value = mock_response

            result = self.detector.detect_pii("test@email.com and 555-1234")

            assert result["pii_detected"] is True
            assert len(result["entities"]) == 2
            assert result["entity_count"] == 2
            assert result["confidence"] == 0.97
            assert "EMAIL" in result["categories"]
            assert "PHONE" in result["categories"]
            assert result["categories"]["EMAIL"] == 1
            assert result["categories"]["PHONE"] == 1

    def test_detect_pii_no_entities(self):
        """Test PII detection with no entities found."""
        mock_response = {"Entities": [], "Confidence": 0.0}

        with patch.object(
            self.detector.comprehend, "detect_pii_entities"
        ) as mock_detect:
            mock_detect.return_value = mock_response

            result = self.detector.detect_pii("This is just normal text")

            assert result["pii_detected"] is False
            assert len(result["entities"]) == 0
            assert result["entity_count"] == 0
            assert result["confidence"] == 0.0
            assert result["categories"] == {}

    def test_detect_pii_error(self):
        """Test PII detection with error."""
        with patch.object(
            self.detector.comprehend, "detect_pii_entities"
        ) as mock_detect:
            mock_detect.side_effect = Exception("Comprehend error")

            result = self.detector.detect_pii("test text")

            assert result["pii_detected"] is False
            assert len(result["entities"]) == 0
            assert result["entity_count"] == 0
            assert result["confidence"] == 0.0
            assert result["categories"] == {}
            assert "error" in result

    def test_redact_pii_success(self):
        """Test successful PII redaction."""
        entities = [
            {
                "Type": "EMAIL",
                "BeginOffset": 0,
                "EndOffset": 10,
            },
            {
                "Type": "PHONE",
                "BeginOffset": 15,
                "EndOffset": 25,
            },
        ]

        result = self.detector.redact_pii("test@email.com and 555-1234", entities)

        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "test@email.com" not in result
        assert "555-1234" not in result

    def test_redact_pii_no_entities(self):
        """Test PII redaction with no entities."""
        result = self.detector.redact_pii("normal text", [])

        assert result == "normal text"

    def test_redact_pii_none_entities(self):
        """Test PII redaction with None entities."""
        result = self.detector.redact_pii("normal text", None)

        assert result == "normal text"

    def test_categorize_pii_entities(self):
        """Test PII entity categorization."""
        entities = [
            {"Type": "EMAIL"},
            {"Type": "EMAIL"},
            {"Type": "PHONE"},
            {"Type": "SSN"},
        ]

        categories = self.detector._categorize_pii_entities(entities)

        assert categories["EMAIL"] == 2
        assert categories["PHONE"] == 1
        assert categories["SSN"] == 1

    def test_categorize_pii_entities_unknown_type(self):
        """Test PII entity categorization with unknown type."""
        entities = [{"Type": "UNKNOWN_TYPE"}]

        categories = self.detector._categorize_pii_entities(entities)

        assert categories["UNKNOWN_TYPE"] == 1

    def test_get_redaction_text(self):
        """Test redaction text generation."""
        assert self.detector._get_redaction_text("EMAIL") == "[EMAIL]"
        assert self.detector._get_redaction_text("PHONE") == "[PHONE]"
        assert self.detector._get_redaction_text("SSN") == "[SSN]"
        assert self.detector._get_redaction_text("NAME") == "[NAME]"
        assert self.detector._get_redaction_text("UNKNOWN") == "[REDACTED]"

    def test_is_sensitive_entity(self):
        """Test sensitive entity detection."""
        assert self.detector.is_sensitive_entity("SSN") is True
        assert self.detector.is_sensitive_entity("CREDIT_DEBIT_NUMBER") is True
        assert self.detector.is_sensitive_entity("BANK_ACCOUNT_NUMBER") is True
        assert self.detector.is_sensitive_entity("PASSPORT_NUMBER") is True
        assert self.detector.is_sensitive_entity("DRIVER_ID") is True
        assert self.detector.is_sensitive_entity("EMAIL") is False
        assert self.detector.is_sensitive_entity("PHONE") is False

    def test_get_entity_risk_level(self):
        """Test entity risk level assessment."""
        assert self.detector.get_entity_risk_level("SSN") == "critical"
        assert self.detector.get_entity_risk_level("CREDIT_DEBIT_NUMBER") == "critical"
        assert self.detector.get_entity_risk_level("BANK_ACCOUNT_NUMBER") == "critical"
        assert self.detector.get_entity_risk_level("PASSPORT_NUMBER") == "high"
        assert self.detector.get_entity_risk_level("DRIVER_ID") == "high"
        assert self.detector.get_entity_risk_level("EMAIL") == "medium"
        assert self.detector.get_entity_risk_level("PHONE") == "medium"
        assert self.detector.get_entity_risk_level("ADDRESS") == "medium"
        assert self.detector.get_entity_risk_level("NAME") == "low"
        assert self.detector.get_entity_risk_level("DATE_TIME") == "low"
        assert self.detector.get_entity_risk_level("UNKNOWN") == "medium"

    def test_redact_pii_overlapping_entities(self):
        """Test PII redaction with overlapping entities."""
        entities = [
            {
                "Type": "EMAIL",
                "BeginOffset": 0,
                "EndOffset": 10,
            },
            {
                "Type": "PHONE",
                "BeginOffset": 5,
                "EndOffset": 15,
            },
        ]

        result = self.detector.redact_pii("test@email.com", entities)

        # Should handle overlapping entities correctly
        assert "[EMAIL]" in result or "[PHONE]" in result
