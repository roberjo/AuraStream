# WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 4

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.max_concurrent_requests
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = local.common_tags
}

# WAF Association with API Gateway
resource "aws_wafv2_web_acl_association" "api_gateway" {
  count        = var.enable_security_monitoring ? 1 : 0
  resource_arn = aws_api_gateway_stage.main[0].arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# CloudTrail
resource "aws_cloudtrail" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  name                          = "${local.name_prefix}-cloudtrail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.documents.arn}/*"]
    }
  }

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    data_resource {
      type   = "AWS::DynamoDB::Table"
      values = [aws_dynamodb_table.sentiment_cache.arn, aws_dynamodb_table.job_results.arn]
    }
  }

  tags = local.common_tags
}

# S3 Bucket for CloudTrail
resource "aws_s3_bucket" "cloudtrail" {
  count = var.enable_security_monitoring ? 1 : 0
  bucket = "${local.name_prefix}-cloudtrail-${data.aws_caller_identity.current.account_id}"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "cloudtrail" {
  count = var.enable_security_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "cloudtrail" {
  count = var.enable_security_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count = var.enable_security_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  count = var.enable_security_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail[0].arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail[0].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# KMS Key for encryption
resource "aws_kms_key" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  description             = "KMS key for AuraStream encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = local.common_tags
}

resource "aws_kms_alias" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  name          = "alias/${local.name_prefix}-key"
  target_key_id = aws_kms_key.main[0].key_id
}

# Security Group for VPC endpoints (if needed)
resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_security_monitoring ? 1 : 0
  name        = "${local.name_prefix}-vpc-endpoints"
  description = "Security group for VPC endpoints"
  vpc_id      = data.aws_vpc.main[0].id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main[0].cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# VPC Data Source (if VPC is used)
data "aws_vpc" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  default = true
}

# GuardDuty (if enabled)
resource "aws_guardduty_detector" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  enable = true

  tags = local.common_tags
}

# Config Rule for compliance
resource "aws_config_config_rule" "dynamodb_encryption" {
  count = var.enable_security_monitoring ? 1 : 0
  name = "${local.name_prefix}-dynamodb-encryption"

  source {
    owner             = "AWS"
    source_identifier = "DYNAMODB_TABLE_ENCRYPTION_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_configuration_recorder" "main" {
  count = var.enable_security_monitoring ? 1 : 0
  name     = "${local.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config_role[0].arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_iam_role" "config_role" {
  count = var.enable_security_monitoring ? 1 : 0
  name = "${local.name_prefix}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "config_role" {
  count = var.enable_security_monitoring ? 1 : 0
  role       = aws_iam_role.config_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# Security monitoring alarms
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  count = var.enable_security_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "This metric monitors WAF blocked requests"
  
  dimensions = {
    WebACL = aws_wafv2_web_acl.main[0].name
    Region = var.aws_region
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "unauthorized_api_calls" {
  count = var.enable_security_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-unauthorized-api-calls"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnauthorizedAPICalls"
  namespace           = "AWS/CloudTrail"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors unauthorized API calls"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = local.common_tags
}
