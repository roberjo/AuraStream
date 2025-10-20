"""Process document handler for Step Functions workflow."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

from src.monitoring.metrics import MetricsCollector
from src.utils.aws_clients import aws_clients

logger = logging.getLogger(__name__)
metrics = MetricsCollector()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing documents in Step Functions workflow.

    Args:
        event: Step Functions event data
        context: Lambda context

    Returns:
        Step Functions response
    """
    try:
        # Extract job information from event
        job_id = event.get("job_id")
        options = event.get("options", {})

        if not job_id:
            raise ValueError("Job ID is required")

        logger.info(f"Processing document for job {job_id}")

        # Get document from S3
        document_text = _get_document_from_s3(job_id)
        if not document_text:
            raise ValueError(f"Document not found for job {job_id}")

        # Process document with Amazon Comprehend
        sentiment_result = _process_with_comprehend(document_text, options)

        # Update job status with result
        _update_job_status(job_id, "COMPLETED", sentiment_result, None)

        # Record metrics
        metrics.record_sentiment_analysis(
            sentiment=sentiment_result.get("Sentiment", "UNKNOWN"),
            confidence=sentiment_result.get("SentimentScore", {}).get(
                sentiment_result.get("Sentiment", "POSITIVE"), 0.0
            ),
            processing_time=0,  # Will be calculated by Step Functions
        )

        logger.info(f"Successfully processed document for job {job_id}")

        return {
            "statusCode": 200,
            "job_id": job_id,
            "status": "COMPLETED",
            "result": sentiment_result,
            "processed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

        # Update job status with error
        job_id = event.get("job_id", "unknown")
        _update_job_status(
            job_id,
            "FAILED",
            None,
            {
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
            },
        )

        metrics.record_error("process_document_handler")

        # Re-raise for Step Functions error handling
        raise


def _get_document_from_s3(job_id: str) -> Optional[str]:
    """
    Get document from S3.

    Args:
        job_id: Job identifier

    Returns:
        Document text if found, None otherwise
    """
    try:
        import os

        s3 = aws_clients.get_s3_client()
        bucket_name = os.environ.get("DOCUMENTS_BUCKET", "aurastream-documents")

        response = s3.get_object(Bucket=bucket_name, Key=f"documents/{job_id}.txt")

        document_text = response["Body"].read().decode("utf-8")
        logger.info(f"Retrieved document for job {job_id} from S3")
        return str(document_text)

    except Exception as e:
        logger.error(f"Error retrieving document for job {job_id}: {str(e)}")
        return None


def _process_with_comprehend(text: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process text with Amazon Comprehend.

    Args:
        text: Text to analyze
        options: Analysis options

    Returns:
        Sentiment analysis result
    """
    try:
        comprehend = aws_clients.get_comprehend_client()

        # For large texts, use batch processing
        if len(text) > 5000:
            return _process_large_text_with_comprehend(text, options)

        # For smaller texts, use real-time processing
        params = {"Text": text, "LanguageCode": options.get("language_code", "en")}

        response = comprehend.detect_sentiment(**params)

        # Add processing metadata
        result = {
            "Sentiment": response["Sentiment"],
            "SentimentScore": response["SentimentScore"],
            "LanguageCode": response.get("LanguageCode", "en"),
            "ProcessingMethod": "real-time",
            "TextLength": len(text),
            "ProcessedAt": datetime.utcnow().isoformat(),
        }

        logger.info(f"Processed text with Comprehend: {response['Sentiment']}")
        return result

    except Exception as e:
        logger.error(f"Error processing text with Comprehend: {str(e)}")
        raise


def _process_large_text_with_comprehend(
    text: str, options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process large text with Amazon Comprehend batch processing.

    Args:
        text: Text to analyze
        options: Analysis options

    Returns:
        Sentiment analysis result
    """
    try:
        import os
        import uuid

        comprehend = aws_clients.get_comprehend_client()
        s3 = aws_clients.get_s3_client()

        # Create batch job
        job_name = f"aurastream-batch-{uuid.uuid4()}"
        bucket_name = os.environ.get("DOCUMENTS_BUCKET", "aurastream-documents")

        # Upload text to S3 for batch processing
        input_key = f"batch-input/{job_name}.txt"
        s3.put_object(
            Bucket=bucket_name,
            Key=input_key,
            Body=text.encode("utf-8"),
            ContentType="text/plain",
        )

        # Start batch sentiment detection job
        response = comprehend.start_sentiment_detection_job(
            JobName=job_name,
            InputDataConfig={
                "S3Uri": f"s3://{bucket_name}/{input_key}",
                "InputFormat": "ONE_DOC_PER_FILE",
            },
            OutputDataConfig={"S3Uri": f"s3://{bucket_name}/batch-output/"},
            DataAccessRoleArn=os.environ.get("COMPREHEND_ROLE_ARN", ""),
            LanguageCode=options.get("language_code", "en"),
        )

        # For now, return a placeholder result
        # In a real implementation, you would poll for job completion
        result = {
            "Sentiment": "PROCESSING",
            "SentimentScore": {
                "Positive": 0.0,
                "Negative": 0.0,
                "Neutral": 0.0,
                "Mixed": 0.0,
            },
            "LanguageCode": options.get("language_code", "en"),
            "ProcessingMethod": "batch",
            "BatchJobId": response["JobId"],
            "TextLength": len(text),
            "ProcessedAt": datetime.utcnow().isoformat(),
        }

        logger.info(f"Started batch processing job {response['JobId']} for large text")
        return result

    except Exception as e:
        logger.error(f"Error processing large text with Comprehend: {str(e)}")
        raise


def _update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]],
    error: Optional[Dict[str, Any]],
) -> bool:
    """
    Update job status in DynamoDB.

    Args:
        job_id: Job identifier
        status: New status
        result: Analysis result
        error: Error information

    Returns:
        True if updated successfully
    """
    try:
        import os

        dynamodb = aws_clients.get_dynamodb_resource()
        table_name = os.environ.get("JOB_RESULTS_TABLE", "AuraStream-JobResults")
        table = dynamodb.Table(table_name)

        update_expression = "SET #status = :status, #updated_at = :updated_at"
        expression_attribute_names = {"#status": "status", "#updated_at": "updated_at"}
        expression_attribute_values: Dict[str, Union[str, Dict[str, Any]]] = {
            ":status": status,
            ":updated_at": datetime.utcnow().isoformat(),
        }

        if result:
            update_expression += ", #result = :result, #completed_at = :completed_at"
            expression_attribute_names["#result"] = "result"
            expression_attribute_names["#completed_at"] = "completed_at"
            expression_attribute_values[":result"] = result
            expression_attribute_values[":completed_at"] = datetime.utcnow().isoformat()

        if error:
            update_expression += ", #error = :error"
            expression_attribute_names["#error"] = "error"
            expression_attribute_values[":error"] = error

        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )

        logger.info(f"Updated job {job_id} status to {status}")
        return True

    except Exception as e:
        logger.error(f"Error updating job {job_id} status: {str(e)}")
        return False
