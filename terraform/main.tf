# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  common_tags = {
    Project     = "AuraStream"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "https://github.com/your-org/aurastream"
  }
  
  name_prefix = "aurastream-${var.environment}"
}

# API Gateway
resource "aws_api_gateway_rest_api" "main" {
  name        = "${local.name_prefix}-api"
  description = "AuraStream Sentiment Analysis API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  
  tags = local.common_tags
}

resource "aws_api_gateway_resource" "analyze" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "analyze"
}

resource "aws_api_gateway_resource" "analyze_sync" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.analyze.id
  path_part   = "sync"
}

resource "aws_api_gateway_resource" "analyze_async" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.analyze.id
  path_part   = "async"
}

resource "aws_api_gateway_resource" "status" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "status"
}

resource "aws_api_gateway_resource" "status_job_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.status.id
  path_part   = "{job_id}"
}

resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "health"
}

# Lambda Functions
resource "aws_lambda_function" "sync_handler" {
  filename         = "../dist/sync_handler.zip"
  function_name    = "${local.name_prefix}-sync-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.sync_handler.lambda_handler"
  source_code_hash = data.archive_file.sync_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      SENTIMENT_CACHE_TABLE = aws_dynamodb_table.sentiment_cache.name
      COMPREHEND_ROLE_ARN   = aws_iam_role.comprehend_role.arn
      ENVIRONMENT          = var.environment
      LOG_LEVEL           = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

resource "aws_lambda_function" "async_handler" {
  filename         = "../dist/async_handler.zip"
  function_name    = "${local.name_prefix}-async-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.async_handler.lambda_handler"
  source_code_hash = data.archive_file.async_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      DOCUMENTS_BUCKET     = aws_s3_bucket.documents.id
      JOB_RESULTS_TABLE    = aws_dynamodb_table.job_results.name
      STEP_FUNCTION_ARN    = aws_sfn_state_machine.sentiment_analysis.arn
      ENVIRONMENT          = var.environment
      LOG_LEVEL           = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

resource "aws_lambda_function" "status_handler" {
  filename         = "../dist/status_handler.zip"
  function_name    = "${local.name_prefix}-status-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.status_handler.lambda_handler"
  source_code_hash = data.archive_file.status_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      JOB_RESULTS_TABLE = aws_dynamodb_table.job_results.name
      ENVIRONMENT       = var.environment
      LOG_LEVEL        = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

resource "aws_lambda_function" "health_handler" {
  filename         = "../dist/health_handler.zip"
  function_name    = "${local.name_prefix}-health-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.health_handler.lambda_handler"
  source_code_hash = data.archive_file.health_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      LOG_LEVEL  = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

resource "aws_lambda_function" "process_document" {
  filename         = "../dist/process_document_handler.zip"
  function_name    = "${local.name_prefix}-process-document"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.process_document_handler.lambda_handler"
  source_code_hash = data.archive_file.process_document_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      JOB_RESULTS_TABLE = aws_dynamodb_table.job_results.name
      DOCUMENTS_BUCKET  = aws_s3_bucket.documents.id
      ENVIRONMENT       = var.environment
      LOG_LEVEL        = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

resource "aws_lambda_function" "update_job_status" {
  filename         = "../dist/update_job_status_handler.zip"
  function_name    = "${local.name_prefix}-update-job-status"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.update_job_status_handler.lambda_handler"
  source_code_hash = data.archive_file.update_job_status_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  environment {
    variables = {
      JOB_RESULTS_TABLE = aws_dynamodb_table.job_results.name
      ENVIRONMENT       = var.environment
      LOG_LEVEL        = var.log_level
    }
  }
  
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }
  
  tags = local.common_tags
}

# Lambda Permissions
resource "aws_lambda_permission" "api_gateway_sync" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_async" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.async_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_status" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.status_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_health" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Gateway Methods
resource "aws_api_gateway_method" "sync_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.analyze_sync.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = var.api_key_required
}

resource "aws_api_gateway_method" "async_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.analyze_async.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = var.api_key_required
}

resource "aws_api_gateway_method" "status_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.status_job_id.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = var.api_key_required
}

resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

# API Gateway Integrations
resource "aws_api_gateway_integration" "sync_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.analyze_sync.id
  http_method = aws_api_gateway_method.sync_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sync_handler.invoke_arn
}

resource "aws_api_gateway_integration" "async_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.analyze_async.id
  http_method = aws_api_gateway_method.async_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.async_handler.invoke_arn
}

resource "aws_api_gateway_integration" "status_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.status_job_id.id
  http_method = aws_api_gateway_method.status_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.status_handler.invoke_arn
}

resource "aws_api_gateway_integration" "health_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.health_handler.invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.sync_integration,
    aws_api_gateway_integration.async_integration,
    aws_api_gateway_integration.status_integration,
    aws_api_gateway_integration.health_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }
}

# DynamoDB Tables
resource "aws_dynamodb_table" "sentiment_cache" {
  name           = "${local.name_prefix}-sentiment-cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "text_hash"
  
  attribute {
    name = "text_hash"
    type = "S"
  }
  
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = local.common_tags
}

resource "aws_dynamodb_table" "job_results" {
  name           = "${local.name_prefix}-job-results"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "job_id"
  
  attribute {
    name = "job_id"
    type = "S"
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = local.common_tags
}

# S3 Bucket
resource "aws_s3_bucket" "documents" {
  bucket = "${local.name_prefix}-documents-${data.aws_caller_identity.current.account_id}"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  rule {
    id     = "delete_old_versions"
    status = "Enabled"
    
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
  
  rule {
    id     = "transition_to_ia"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "sentiment_analysis" {
  name     = "${local.name_prefix}-sentiment-analysis"
  role_arn = aws_iam_role.step_function_role.arn
  
  definition = jsonencode({
    Comment = "AuraStream Sentiment Analysis Workflow"
    StartAt = "ProcessDocument"
    States = {
      ProcessDocument = {
        Type     = "Task"
        Resource = aws_lambda_function.process_document.arn
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
            ResultPath  = "$.error"
          }
        ]
        Next = "UpdateJobStatus"
      }
      UpdateJobStatus = {
        Type     = "Task"
        Resource = aws_lambda_function.update_job_status.arn
        End      = true
      }
      HandleError = {
        Type     = "Task"
        Resource = aws_lambda_function.update_job_status.arn
        End      = true
      }
    }
  })
  
  tags = local.common_tags
}

# SQS Queues
resource "aws_sqs_queue" "dead_letter_queue" {
  name                      = "${local.name_prefix}-dlq"
  message_retention_seconds = 1209600 # 14 days
  
  tags = local.common_tags
}

resource "aws_sqs_queue" "processing_queue" {
  name                      = "${local.name_prefix}-processing-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 10
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = 3
  })
  
  tags = local.common_tags
}

# SNS Topics
resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
  
  tags = local.common_tags
}

resource "aws_sns_topic" "notifications" {
  name = "${local.name_prefix}-notifications"
  
  tags = local.common_tags
}

# SNS Topic Subscriptions
resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.sync_handler.function_name,
    aws_lambda_function.async_handler.function_name,
    aws_lambda_function.status_handler.function_name,
    aws_lambda_function.health_handler.function_name,
    aws_lambda_function.process_document.function_name,
    aws_lambda_function.update_job_status.function_name
  ])
  
  name              = "/aws/lambda/${each.key}"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# Archive files for Lambda deployment packages
data "archive_file" "sync_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/sync_handler.zip"
}

data "archive_file" "async_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/async_handler.zip"
}

data "archive_file" "status_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/status_handler.zip"
}

data "archive_file" "health_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/health_handler.zip"
}

data "archive_file" "process_document_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/process_document_handler.zip"
}

data "archive_file" "update_job_status_handler_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../dist/update_job_status_handler.zip"
}
