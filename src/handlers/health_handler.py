"""Health check handler for AuraStream API."""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from src.models.response_models import HealthResponse
from src.utils.aws_clients import aws_clients
from src.utils.json_encoder import json_dumps

logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for health check endpoint.

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Check component health
        components = _check_components()

        # Determine overall health
        overall_status = (
            "healthy"
            if all(status == "healthy" for status in components.values())
            else "unhealthy"
        )

        # Create health response
        health_response = HealthResponse(
            status=overall_status, version="1.0.0", components=components
        )

        status_code = 200 if overall_status == "healthy" else 503

        logger.info(f"Health check completed: {overall_status}")

        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json_dumps(health_response.dict()),
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")

        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0",
                    "error": str(e),
                }
            ),
        }


def _check_components() -> Dict[str, str]:
    """
    Check health of system components.

    Returns:
        Dictionary of component statuses
    """
    components = {}

    # Check DynamoDB
    components["dynamodb"] = _check_dynamodb()

    # Check S3
    components["s3"] = _check_s3()

    # Check Comprehend
    components["comprehend"] = _check_comprehend()

    # Check Lambda
    components["lambda"] = _check_lambda()

    return components


def _check_dynamodb() -> str:
    """Check DynamoDB health."""
    try:
        dynamodb = aws_clients.get_dynamodb_resource()
        # Try to list tables as a health check
        list(dynamodb.tables.all())
        return "healthy"
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {str(e)}")
        return "unhealthy"


def _check_s3() -> str:
    """Check S3 health."""
    try:
        s3 = aws_clients.get_s3_client()
        # Try to list buckets as a health check
        s3.list_buckets()
        return "healthy"
    except Exception as e:
        logger.error(f"S3 health check failed: {str(e)}")
        return "unhealthy"


def _check_comprehend() -> str:
    """Check Amazon Comprehend health."""
    try:
        comprehend = aws_clients.get_comprehend_client()
        # Try a simple sentiment detection as a health check
        comprehend.detect_sentiment(Text="test", LanguageCode="en")
        return "healthy"
    except Exception as e:
        logger.error(f"Comprehend health check failed: {str(e)}")
        return "unhealthy"


def _check_lambda() -> str:
    """Check Lambda health."""
    try:
        # Lambda is healthy if we can execute this function
        return "healthy"
    except Exception as e:
        logger.error(f"Lambda health check failed: {str(e)}")
        return "unhealthy"
