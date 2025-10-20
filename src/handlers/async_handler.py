"""Asynchronous sentiment analysis handler."""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError

from src.models.request_models import AsyncSentimentAnalysisRequest
from src.models.response_models import AsyncJobResponse, ErrorResponse
from src.monitoring.metrics import MetricsCollector
from src.utils.aws_clients import aws_clients
from src.utils.constants import ERROR_CODES, MAX_TEXT_LENGTH_ASYNC
from src.utils.json_encoder import json_dumps
from src.utils.validators import InputValidator

logger = logging.getLogger(__name__)
metrics = MetricsCollector()


def _validate_request(
    request: AsyncSentimentAnalysisRequest, request_id: str
) -> Optional[Dict[str, Any]]:
    """Validate the request and return error response if invalid."""
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

    # Validate text length
    if len(request.text) > MAX_TEXT_LENGTH_ASYNC:
        return _create_error_response(
            ERROR_CODES["VALIDATION_ERROR"],
            "VALIDATION_ERROR",
            f"Text exceeds maximum length of {MAX_TEXT_LENGTH_ASYNC} characters",
            request_id,
        )

    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for asynchronous sentiment analysis.

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
        request = AsyncSentimentAnalysisRequest(**request_data)
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
        # Validate request
        validation_error = _validate_request(request, request_id)
        if validation_error:
            return validation_error

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Store job in DynamoDB
        job_stored = _store_job(job_id, request, request_id)
        if not job_stored:
            return _create_error_response(
                ERROR_CODES["INTERNAL_ERROR"],
                "INTERNAL_ERROR",
                "Failed to store job information",
                request_id,
            )

        # Store document in S3
        document_stored = _store_document(job_id, request.text, request_id)
        if not document_stored:
            return _create_error_response(
                ERROR_CODES["INTERNAL_ERROR"],
                "INTERNAL_ERROR",
                "Failed to store document",
                request_id,
            )

        # Start Step Functions execution
        execution_started = _start_step_function(job_id, request, request_id)
        if not execution_started:
            return _create_error_response(
                ERROR_CODES["INTERNAL_ERROR"],
                "INTERNAL_ERROR",
                "Failed to start processing",
                request_id,
            )

        # Create response
        response = AsyncJobResponse(
            job_id=job_id,
            status="PROCESSING",
            message="Job submitted successfully",
            estimated_completion=_calculate_estimated_completion(
                request.text
            ).isoformat(),
            created_at=datetime.now(timezone.utc),
        )

        # Record metrics
        metrics.record_api_usage(
            endpoint="/analyze/async",
            customer_id=request.source_id or "anonymous",
            response_time=int((time.time() - start_time) * 1000),
            status_code=202,
        )

        logger.info(
            f"Successfully submitted async job {job_id} for request {request_id}"
        )
        return _create_success_response(response.dict(), request_id)

    except Exception as e:
        logger.error(f"Error processing async request {request_id}: {str(e)}")
        metrics.record_error("async_handler")
        return _create_error_response(
            ERROR_CODES["INTERNAL_ERROR"],
            "INTERNAL_ERROR",
            "An internal error occurred",
            request_id,
        )


def _store_job(
    job_id: str, request: AsyncSentimentAnalysisRequest, request_id: str
) -> bool:
    """
    Store job information in DynamoDB.

    Args:
        job_id: Job identifier
        request: Async request data
        request_id: Request identifier

    Returns:
        True if stored successfully
    """
    try:
        import os

        dynamodb = aws_clients.get_dynamodb_resource()
        table_name = os.environ.get("JOB_RESULTS_TABLE", "AuraStream-JobResults")
        table = dynamodb.Table(table_name)

        job_item = {
            "job_id": job_id,
            "status": "PROCESSING",
            "created_at": datetime.utcnow().isoformat(),
            "source_id": request.source_id,
            "text_length": len(request.text),
            "options": request.options or {},
            "request_id": request_id,
        }

        table.put_item(Item=job_item)
        logger.info(f"Stored job {job_id} in DynamoDB")
        return True

    except Exception as e:
        logger.error(f"Error storing job {job_id}: {str(e)}")
        return False


def _store_document(job_id: str, text: str, request_id: str) -> bool:
    """
    Store document in S3.

    Args:
        job_id: Job identifier
        text: Document text
        request_id: Request identifier

    Returns:
        True if stored successfully
    """
    try:
        import os

        s3 = aws_clients.get_s3_client()
        bucket_name = os.environ.get("DOCUMENTS_BUCKET", "aurastream-documents")

        # Store document with job ID as key
        s3.put_object(
            Bucket=bucket_name,
            Key=f"documents/{job_id}.txt",
            Body=text.encode("utf-8"),
            ContentType="text/plain",
            Metadata={
                "job_id": job_id,
                "request_id": request_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Stored document for job {job_id} in S3")
        return True

    except Exception as e:
        logger.error(f"Error storing document for job {job_id}: {str(e)}")
        return False


def _start_step_function(
    job_id: str, request: AsyncSentimentAnalysisRequest, request_id: str
) -> bool:
    """
    Start Step Functions execution.

    Args:
        job_id: Job identifier
        request: Async request data
        request_id: Request identifier

    Returns:
        True if started successfully
    """
    try:
        import os

        stepfunctions = aws_clients.get_stepfunctions_client()
        state_machine_arn = os.environ.get("STEP_FUNCTION_ARN", "")

        if not state_machine_arn:
            logger.error("STEP_FUNCTION_ARN environment variable not set")
            return False

        execution_input = {
            "job_id": job_id,
            "source_id": request.source_id,
            "options": request.options or {},
            "request_id": request_id,
        }

        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"aurastream-{job_id}",
            input=json.dumps(execution_input),
        )

        logger.info(
            f"Started Step Functions execution for job {job_id}: "
            f"{response['executionArn']}"
        )
        return True

    except Exception as e:
        logger.error(f"Error starting Step Functions for job {job_id}: {str(e)}")
        return False


def _calculate_estimated_completion(text: str) -> datetime:
    """
    Calculate estimated completion time based on text length.

    Args:
        text: Document text

    Returns:
        Estimated completion time
    """
    # Base processing time: 30 seconds
    base_time = 30

    # Additional time based on text length (1 second per 1000 characters)
    additional_time = len(text) / 1000

    total_seconds = base_time + additional_time

    return datetime.now(timezone.utc) + timedelta(seconds=total_seconds)


def _create_success_response(data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """Create successful API Gateway response."""
    return {
        "statusCode": 202,
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
        }
    )

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "X-Request-ID": request_id},
        "body": json_dumps(error_response.dict()),
    }
