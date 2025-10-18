"""Update job status handler for Step Functions workflow."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.aws_clients import aws_clients
from src.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)
metrics = MetricsCollector()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating job status in Step Functions workflow.
    
    Args:
        event: Step Functions event data
        context: Lambda context
        
    Returns:
        Step Functions response
    """
    try:
        # Extract job information from event
        job_id = event.get('job_id')
        status = event.get('status', 'PROCESSING')
        result = event.get('result')
        error = event.get('error')
        
        if not job_id:
            raise ValueError("Job ID is required")
        
        logger.info(f"Updating job {job_id} status to {status}")
        
        # Update job status in DynamoDB
        success = _update_job_status(job_id, status, result, error)
        
        if not success:
            raise ValueError(f"Failed to update job {job_id} status")
        
        # Record metrics
        if status == 'COMPLETED':
            metrics.record_business_metric('JobsCompleted', 1, 'Count')
        elif status == 'FAILED':
            metrics.record_business_metric('JobsFailed', 1, 'Count')
        
        logger.info(f"Successfully updated job {job_id} status to {status}")
        
        return {
            'statusCode': 200,
            'job_id': job_id,
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        metrics.record_error('update_job_status_handler')
        
        # Re-raise for Step Functions error handling
        raise


def _update_job_status(job_id: str, status: str, result: Optional[Dict[str, Any]], error: Optional[Dict[str, Any]]) -> bool:
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
        table_name = os.environ.get('JOB_RESULTS_TABLE', 'AuraStream-JobResults')
        table = dynamodb.Table(table_name)
        
        update_expression = "SET #status = :status, #updated_at = :updated_at"
        expression_attribute_names = {
            '#status': 'status',
            '#updated_at': 'updated_at'
        }
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if result:
            update_expression += ", #result = :result, #completed_at = :completed_at"
            expression_attribute_names['#result'] = 'result'
            expression_attribute_names['#completed_at'] = 'completed_at'
            expression_attribute_values[':result'] = result
            expression_attribute_values[':completed_at'] = datetime.utcnow().isoformat()
        
        if error:
            update_expression += ", #error = :error"
            expression_attribute_names['#error'] = 'error'
            expression_attribute_values[':error'] = error
        
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Updated job {job_id} status to {status}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating job {job_id} status: {str(e)}")
        return False
