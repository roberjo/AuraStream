# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_monitoring ? 1 : 0
  dashboard_name = "${local.name_prefix}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.sync_handler.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics - Sync Handler"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.async_handler.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics - Async Handler"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.sentiment_cache.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ItemCount", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Metrics - Sentiment Cache"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.job_results.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ItemCount", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Metrics - Job Results"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 24
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/S3", "BucketSizeBytes", "BucketName", aws_s3_bucket.documents.id, "StorageType", "StandardStorage"],
            [".", "NumberOfObjects", ".", ".", ".", "AllStorageTypes"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "S3 Metrics - Documents Bucket"
          period  = 86400
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 30
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", aws_sfn_state_machine.sentiment_analysis.arn],
            [".", "ExecutionsSucceeded", ".", "."],
            [".", "ExecutionsFailed", ".", "."],
            [".", "ExecutionsAborted", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Step Functions Metrics"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  
  dimensions = {
    FunctionName = aws_lambda_function.sync_handler.function_name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000"
  alarm_description   = "This metric monitors lambda duration"
  
  dimensions = {
    FunctionName = aws_lambda_function.sync_handler.function_name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  count = var.enable_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors lambda throttles"
  
  dimensions = {
    FunctionName = aws_lambda_function.sync_handler.function_name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  count = var.enable_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors DynamoDB throttles"
  
  dimensions = {
    TableName = aws_dynamodb_table.sentiment_cache.name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "step_functions_failures" {
  count = var.enable_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-step-functions-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = "300"
  statistic           = "Sum"
  threshold           = "3"
  alarm_description   = "This metric monitors Step Functions failures"
  
  dimensions = {
    StateMachineArn = aws_sfn_state_machine.sentiment_analysis.arn
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

# Cost allocation tags
resource "aws_cost_allocation_tags" "main" {
  count = var.enable_cost_optimization ? 1 : 0
  tags = [
    {
      key   = "Project"
      value = "AuraStream"
    },
    {
      key   = "Environment"
      value = var.environment
    }
  ]
}

# Budget alerts
resource "aws_budgets_budget" "main" {
  count = var.enable_cost_optimization ? 1 : 0
  name         = "${local.name_prefix}-budget"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  cost_filters = {
    Tag = [
      "Project$AuraStream",
      "Environment$${var.environment}"
    ]
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
  
  tags = local.common_tags
}

# Custom metrics for business monitoring
resource "aws_cloudwatch_log_metric_filter" "sentiment_analysis_count" {
  count = var.enable_monitoring ? 1 : 0
  name           = "${local.name_prefix}-sentiment-analysis-count"
  log_group_name = aws_cloudwatch_log_group.lambda_logs[aws_lambda_function.sync_handler.function_name].name
  pattern        = "[timestamp, request_id, level, message=\"Successfully processed request\"]"

  metric_transformation {
    name      = "SentimentAnalysisCount"
    namespace = "AuraStream/Business"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "cache_hit_count" {
  count = var.enable_monitoring ? 1 : 0
  name           = "${local.name_prefix}-cache-hit-count"
  log_group_name = aws_cloudwatch_log_group.lambda_logs[aws_lambda_function.sync_handler.function_name].name
  pattern        = "[timestamp, request_id, level, message=\"Cache hit for request\"]"

  metric_transformation {
    name      = "CacheHitCount"
    namespace = "AuraStream/Performance"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "pii_detection_count" {
  count = var.enable_monitoring ? 1 : 0
  name           = "${local.name_prefix}-pii-detection-count"
  log_group_name = aws_cloudwatch_log_group.lambda_logs[aws_lambda_function.sync_handler.function_name].name
  pattern        = "[timestamp, request_id, level, message=\"PII detected in request\"]"

  metric_transformation {
    name      = "PIIDetectionCount"
    namespace = "AuraStream/Security"
    value     = "1"
  }
}

# API Gateway CloudWatch Log Group
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_monitoring ? 1 : 0
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.main.name}"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# API Gateway Stage with CloudWatch logging
resource "aws_api_gateway_stage" "main" {
  count = var.enable_monitoring ? 1 : 0
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  xray_tracing_enabled = var.enable_xray
}
