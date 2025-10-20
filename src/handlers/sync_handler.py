"""Synchronous sentiment analysis handler."""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError

from src.cache.sentiment_cache import SentimentCache
from src.models.request_models import SentimentAnalysisRequest
from src.models.response_models import ErrorResponse, SentimentAnalysisResponse
from src.monitoring.metrics import MetricsCollector
from src.pii.pii_detector import PIIDetector
from src.utils.aws_clients import aws_clients
from src.utils.constants import ERROR_CODES
from src.utils.json_encoder import json_dumps
from src.utils.validators import InputValidator

logger = logging.getLogger(__name__)
metrics = MetricsCollector()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for synchronous sentiment analysis.

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        API Gateway response
    """
    start_time = time.time()
    request_id = context.aws_request_id if context else "unknown"

    try:
        # Parse request
        request_data = json.loads(event.get("body", "{}"))
        request = SentimentAnalysisRequest(**request_data)
    except ValidationError as e:
        logger.warning(f"Validation error for request {request_id}: {str(e)}")
        return _create_error_response(
            ERROR_CODES["VALIDATION_ERROR"],
            "VALIDATION_ERROR",
            f"Invalid request data: {str(e)}",
            request_id,
        )
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error for request {request_id}: {str(e)}")
        return _create_error_response(
            ERROR_CODES["VALIDATION_ERROR"],
            "VALIDATION_ERROR",
            "Invalid JSON in request body",
            request_id,
        )

    try:
        # Validate input security
        security_check = InputValidator.validate_text_security(request.text)
        if not security_check["is_safe"]:
            logger.warning(f"Security threat detected: {security_check['threats']}")
            return _create_error_response(
                ERROR_CODES["VALIDATION_ERROR"],
                "VALIDATION_ERROR",
                "Text contains potentially malicious content",
                request_id,
            )

        # Initialize services
        cache = SentimentCache()
        pii_detector = PIIDetector()

        # Check cache first
        cached_result = cache.get_cached_result(request.text)
        if cached_result:
            logger.info(f"Cache hit for request {request_id}")
            metrics.record_cache_hit()
            return _create_success_response(cached_result, request_id, True)

        # Detect PII if requested
        pii_detected = False
        if request.options and request.options.get("include_pii_detection", True):
            pii_result = pii_detector.detect_pii(request.text)
            pii_detected = pii_result["pii_detected"]

            if pii_detected:
                logger.info(f"PII detected in request {request_id}")
                metrics.record_pii_detection()

        # Analyze sentiment
        sentiment_result = _analyze_sentiment(request.text, request.options)

        # Create response
        response = SentimentAnalysisResponse(
            sentiment=sentiment_result["Sentiment"],
            score=_get_sentiment_score(sentiment_result),
            language_code=sentiment_result.get("LanguageCode", "en"),
            confidence=(
                request.options.get("include_confidence", True)
                if request.options
                else True
            ),
            pii_detected=pii_detected,
            processing_time_ms=int((time.time() - start_time) * 1000),
            cache_hit=False,
            request_id=request_id,
        )

        # Cache the result
        cache.store_result(
            request.text,
            response.model_dump()
            if hasattr(response, "model_dump")
            else response.dict(),
        )

        # Record metrics
        metrics.record_sentiment_analysis(
            sentiment=response.sentiment,
            confidence=response.confidence or 0.0,
            processing_time=response.processing_time_ms or 0,
        )

        logger.info(f"Successfully processed request {request_id}")
        return _create_success_response(
            response.model_dump()
            if hasattr(response, "model_dump")
            else response.dict(),
            request_id,
            False,
        )

    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        metrics.record_error()
        return _create_error_response(
            ERROR_CODES["INTERNAL_ERROR"],
            "INTERNAL_ERROR",
            "An internal error occurred",
            request_id,
        )


def _analyze_sentiment(text: str, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze sentiment using Amazon Comprehend.

    Args:
        text: Text to analyze
        options: Analysis options

    Returns:
        Sentiment analysis result
    """
    comprehend = aws_clients.get_comprehend_client()

    params = {
        "Text": text,
        "LanguageCode": options.get("language_code", "en") if options else "en",
    }

    response = comprehend.detect_sentiment(**params)
    return dict(response) if response else {}


def _get_sentiment_score(sentiment_result: Dict[str, Any]) -> float:
    """
    Extract sentiment score from Comprehend result.

    Args:
        sentiment_result: Comprehend API result

    Returns:
        Sentiment score
    """
    sentiment = sentiment_result["Sentiment"]
    scores = sentiment_result["SentimentScore"]

    # Return the score for the detected sentiment
    # Map sentiment to the correct key in SentimentScore
    sentiment_key_map = {
        "POSITIVE": "Positive",
        "NEGATIVE": "Negative",
        "NEUTRAL": "Neutral",
        "MIXED": "Mixed",
    }
    sentiment_key = sentiment_key_map.get(sentiment, sentiment)
    score = scores.get(sentiment_key, 0.0)
    return float(score) if isinstance(score, (int, float)) else 0.0


def _create_success_response(
    data: Dict[str, Any], request_id: str, cache_hit: bool
) -> Dict[str, Any]:
    """Create successful API Gateway response."""
    # Add cache_hit to the response data
    response_data = data.copy()
    response_data["cache_hit"] = cache_hit

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
            "X-Cache-Hit": str(cache_hit).lower(),
        },
        "body": json_dumps(response_data),
    }


def _create_error_response(
    status_code: int, error_code: str, message: str, request_id: str
) -> Dict[str, Any]:
    """Create error API Gateway response."""
    error_response = ErrorResponse(
        error={
            "code": error_code,
            "message": message,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        message=None,
        details={"request_id": request_id},
    )

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "X-Request-ID": request_id},
        "body": json_dumps(
            error_response.model_dump()
            if hasattr(error_response, "model_dump")
            else error_response.dict()
        ),
    }
