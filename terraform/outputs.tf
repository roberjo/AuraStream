output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_gateway_execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "sentiment_cache_table_name" {
  description = "Sentiment cache DynamoDB table name"
  value       = aws_dynamodb_table.sentiment_cache.name
}

output "sentiment_cache_table_arn" {
  description = "Sentiment cache DynamoDB table ARN"
  value       = aws_dynamodb_table.sentiment_cache.arn
}

output "job_results_table_name" {
  description = "Job results DynamoDB table name"
  value       = aws_dynamodb_table.job_results.name
}

output "job_results_table_arn" {
  description = "Job results DynamoDB table ARN"
  value       = aws_dynamodb_table.job_results.arn
}

output "documents_bucket_name" {
  description = "Documents S3 bucket name"
  value       = aws_s3_bucket.documents.id
}

output "documents_bucket_arn" {
  description = "Documents S3 bucket ARN"
  value       = aws_s3_bucket.documents.arn
}

output "step_function_arn" {
  description = "Step Functions state machine ARN"
  value       = aws_sfn_state_machine.sentiment_analysis.arn
}

output "step_function_name" {
  description = "Step Functions state machine name"
  value       = aws_sfn_state_machine.sentiment_analysis.name
}

output "lambda_function_arns" {
  description = "Lambda function ARNs"
  value = {
    sync_handler   = aws_lambda_function.sync_handler.arn
    async_handler  = aws_lambda_function.async_handler.arn
    status_handler = aws_lambda_function.status_handler.arn
    health_handler = aws_lambda_function.health_handler.arn
    process_document = aws_lambda_function.process_document.arn
    update_job_status = aws_lambda_function.update_job_status.arn
  }
}

output "lambda_function_names" {
  description = "Lambda function names"
  value = {
    sync_handler   = aws_lambda_function.sync_handler.function_name
    async_handler  = aws_lambda_function.async_handler.function_name
    status_handler = aws_lambda_function.status_handler.function_name
    health_handler = aws_lambda_function.health_handler.function_name
    process_document = aws_lambda_function.process_document.function_name
    update_job_status = aws_lambda_function.update_job_status.function_name
  }
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value       = [for log_group in aws_cloudwatch_log_group.lambda_logs : log_group.name]
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "iam_role_arns" {
  description = "IAM role ARNs"
  value = {
    lambda_role        = aws_iam_role.lambda_role.arn
    step_function_role = aws_iam_role.step_function_role.arn
    comprehend_role    = aws_iam_role.comprehend_role.arn
  }
}

output "environment_info" {
  description = "Environment information"
  value = {
    environment = var.environment
    region      = var.aws_region
    account_id  = data.aws_caller_identity.current.account_id
    deployment_time = timestamp()
  }
}

output "cost_monitoring" {
  description = "Cost monitoring information"
  value = {
    budget_name = aws_budgets_budget.main.name
    budget_limit = aws_budgets_budget.main.limit_amount
    alert_email = var.alert_email
  }
}

output "security_info" {
  description = "Security configuration information"
  value = {
    encryption_enabled = true
    api_key_required = var.api_key_required
    xray_enabled = var.enable_xray
    monitoring_enabled = var.enable_monitoring
    security_monitoring_enabled = var.enable_security_monitoring
  }
}
