"""PII detection service using Amazon Comprehend."""

import logging
from typing import Any, Dict, List

from src.utils.aws_clients import aws_clients

logger = logging.getLogger(__name__)


class PIIDetector:
    """Detects personally identifiable information in text."""

    def __init__(self) -> None:
        """Initialize PII detector."""
        self.comprehend = aws_clients.get_comprehend_client()

    def detect_pii(self, text: str, language_code: str = "en") -> Dict[str, Any]:
        """
        Detect PII in text using Amazon Comprehend.

        Args:
            text: Text to analyze
            language_code: Language code for analysis

        Returns:
            PII detection results
        """
        try:
            response = self.comprehend.detect_pii_entities(
                Text=text, LanguageCode=language_code
            )

            entities = response.get("Entities", [])
            pii_detected = len(entities) > 0

            # Categorize PII entities
            pii_categories = self._categorize_pii_entities(entities)

            result = {
                "pii_detected": pii_detected,
                "entities": entities,
                "categories": pii_categories,
                "confidence": response.get("Confidence", 0.0),
                "entity_count": len(entities),
            }

            logger.info(f"PII detection completed: {len(entities)} entities found")
            return result

        except Exception as e:
            logger.error(f"Error detecting PII: {str(e)}")
            return {
                "pii_detected": False,
                "entities": [],
                "categories": {},
                "confidence": 0.0,
                "entity_count": 0,
                "error": str(e),
            }

    def redact_pii(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Redact PII entities from text.

        Args:
            text: Original text
            entities: PII entities to redact

        Returns:
            Text with PII redacted
        """
        if not entities:
            return text

        # Sort entities by start position (descending) to avoid offset issues
        sorted_entities = sorted(entities, key=lambda x: x["BeginOffset"], reverse=True)

        redacted_text = text

        for entity in sorted_entities:
            start = entity["BeginOffset"]
            end = entity["EndOffset"]
            entity_type = entity["Type"]

            # Generate redaction text
            redaction = self._get_redaction_text(entity_type)

            # Replace the entity with redaction
            redacted_text = redacted_text[:start] + redaction + redacted_text[end:]

        logger.info(f"PII redaction completed: {len(entities)} entities redacted")
        return redacted_text

    def _categorize_pii_entities(
        self, entities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Categorize PII entities by type.

        Args:
            entities: List of PII entities

        Returns:
            Dictionary of entity types and counts
        """
        categories: Dict[str, int] = {}

        for entity in entities:
            entity_type = entity.get("Type", "UNKNOWN")
            categories[entity_type] = categories.get(entity_type, 0) + 1

        return categories

    def _get_redaction_text(self, entity_type: str) -> str:
        """
        Get redaction text for entity type.

        Args:
            entity_type: Type of PII entity

        Returns:
            Redaction text
        """
        redaction_map = {
            "NAME": "[NAME]",
            "EMAIL": "[EMAIL]",
            "PHONE": "[PHONE]",
            "SSN": "[SSN]",
            "CREDIT_DEBIT_NUMBER": "[CARD_NUMBER]",
            "ADDRESS": "[ADDRESS]",
            "DATE_TIME": "[DATE]",
            "PASSPORT_NUMBER": "[PASSPORT]",
            "DRIVER_ID": "[DRIVER_ID]",
            "BANK_ACCOUNT_NUMBER": "[ACCOUNT_NUMBER]",
            "BANK_ROUTING": "[ROUTING_NUMBER]",
            "IP_ADDRESS": "[IP_ADDRESS]",
            "MAC_ADDRESS": "[MAC_ADDRESS]",
            "URL": "[URL]",
        }

        return redaction_map.get(entity_type, "[REDACTED]")

    def is_sensitive_entity(self, entity_type: str) -> bool:
        """
        Check if entity type is considered sensitive.

        Args:
            entity_type: Type of PII entity

        Returns:
            True if sensitive
        """
        sensitive_types = [
            "SSN",
            "CREDIT_DEBIT_NUMBER",
            "BANK_ACCOUNT_NUMBER",
            "PASSPORT_NUMBER",
            "DRIVER_ID",
        ]

        return entity_type in sensitive_types

    def get_entity_risk_level(self, entity_type: str) -> str:
        """
        Get risk level for entity type.

        Args:
            entity_type: Type of PII entity

        Returns:
            Risk level (low, medium, high, critical)
        """
        risk_levels = {
            "SSN": "critical",
            "CREDIT_DEBIT_NUMBER": "critical",
            "BANK_ACCOUNT_NUMBER": "critical",
            "PASSPORT_NUMBER": "high",
            "DRIVER_ID": "high",
            "EMAIL": "medium",
            "PHONE": "medium",
            "ADDRESS": "medium",
            "NAME": "low",
            "DATE_TIME": "low",
        }

        return risk_levels.get(entity_type, "medium")
