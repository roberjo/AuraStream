"""Job status handler for AuraStream API."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.models.response_models import ErrorResponse, JobStatusResponse
from src.monitoring.metrics import MetricsCollector
from src.utils.aws_clients import aws_clients
from src.utils.constants import ERROR_CODES
from src.utils.json_encoder import json_dumps
from src.utils.validators import InputValidator

logger = logging.getLogger(__name__)
metrics = MetricsCollector()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for job status check.

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Extract job ID from path parameters
        job_id = event.get("pathParameters", {}).get("job_id")

        if not job_id:
            return _create_error_response(
                ERROR_CODES["VALIDATION_ERROR"],
                "VALIDATION_ERROR",
                "Job ID is required",
                context.aws_request_id if context else "unknown",
            )

        # Validate job ID format
        if not InputValidator.validate_job_id(job_id):
            return _create_error_response(
                ERROR_CODES["VALIDATION_ERROR"],
                "VALIDATION_ERROR",
                "Invalid job ID format",
                context.aws_request_id if context else "unknown",
            )

        # Get job status from DynamoDB
        job_data = _get_job_status(job_id)

        if not job_data:
            return _create_error_response(
                ERROR_CODES["NOT_FOUND"],
                "NOT_FOUND",
                "Job not found",
                context.aws_request_id if context else "unknown",
            )

        # Create response
        # Handle datetime parsing with 'Z' suffix
        created_at_str = job_data["created_at"]
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"
        created_at = datetime.fromisoformat(created_at_str)

        completed_at = None
        if job_data.get("completed_at"):
            completed_at_str = job_data["completed_at"]
            if completed_at_str.endswith("Z"):
                completed_at_str = completed_at_str[:-1] + "+00:00"
            completed_at = datetime.fromisoformat(completed_at_str)

        response = JobStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            created_at=created_at,
            completed_at=completed_at,
            result=job_data.get("result"),
            error=job_data.get("error"),
            source_id=job_data.get("source_id"),
            progress=job_data.get("progress"),
        )

        # Record metrics
        metrics.record_api_usage(
            endpoint="/status/{job_id}",
            customer_id=job_data.get("source_id", "anonymous"),
            response_time=100,  # Typical response time for status check
            status_code=200,
        )

        logger.info(f"Retrieved status for job {job_id}: {job_data['status']}")
        return _create_success_response(
            response.model_dump()
            if hasattr(response, "model_dump")
            else response.dict(),
            context.aws_request_id if context else "unknown",
        )

    except Exception as e:
        logger.error(f"Error retrieving job status: {str(e)}")
        metrics.record_error("status_handler")
        return _create_error_response(
            ERROR_CODES["INTERNAL_ERROR"],
            "INTERNAL_ERROR",
            "An internal error occurred",
            context.aws_request_id if context else "unknown",
        )


def _get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job status from DynamoDB.

    Args:
        job_id: Job identifier

    Returns:
        Job data if found, None otherwise
    """
    try:
        import os

        dynamodb = aws_clients.get_dynamodb_resource()
        table_name = os.environ.get("JOB_RESULTS_TABLE", "AuraStream-JobResults")
        table = dynamodb.Table(table_name)

        response = table.get_item(Key={"job_id": job_id})

        if "Item" in response:
            item = response["Item"]
            return dict(item) if isinstance(item, dict) else None

        return None

    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        return None


def _create_success_response(data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """Create successful API Gateway response."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "X-Request-ID": request_id},
        "body": json_dumps(data),
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
