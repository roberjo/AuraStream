# AuraStream Terraform Cloud Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Terraform Cloud Setup](#terraform-cloud-setup)
3. [Infrastructure Configuration](#infrastructure-configuration)
4. [Environment Management](#environment-management)
5. [Deployment Workflows](#deployment-workflows)
6. [State Management](#state-management)
7. [Security & Compliance](#security--compliance)
8. [Monitoring & Observability](#monitoring--observability)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

This guide provides comprehensive instructions for deploying AuraStream infrastructure using Terraform Cloud. Terraform Cloud offers enterprise-grade infrastructure management with state management, collaboration features, and automated deployments.

### Benefits of Terraform Cloud
- **Centralized State Management**: Secure, encrypted state storage
- **Collaboration**: Team-based access control and approval workflows
- **Automation**: Automated plan and apply workflows
- **Security**: Secure variable management and audit trails
- **Scalability**: Multi-environment support with workspaces

---

## Terraform Cloud Setup

### Prerequisites
- Terraform Cloud account
- AWS account with appropriate permissions
- GitHub repository access
- AWS CLI configured locally

### 1. Create Terraform Cloud Organization

```bash
# Install Terraform CLI
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Login to Terraform Cloud
terraform login
```

### 2. Configure AWS Provider

Create `terraform/versions.tf`:
```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  cloud {
    organization = "aurastream"
    workspaces {
      name = "aurastream-*"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AuraStream"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "https://github.com/your-org/aurastream"
    }
  }
}
```

### 3. Create Terraform Cloud Workspaces

#### Development Workspace
```bash
# Create development workspace
terraform workspace new aurastream-dev
```

#### Staging Workspace
```bash
# Create staging workspace
terraform workspace new aurastream-staging
```

#### Production Workspace
```bash
# Create production workspace
terraform workspace new aurastream-prod
```

---

## Infrastructure Configuration

### 1. Main Configuration

Create `terraform/main.tf`:
```hcl
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

# Lambda Functions
resource "aws_lambda_function" "sync_handler" {
  filename         = "../dist/sync_handler.zip"
  function_name    = "${local.name_prefix}-sync-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.sync_handler.lambda_handler"
  source_code_hash = data.archive_file.sync_handler_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 512
  
  environment {
    variables = {
      SENTIMENT_CACHE_TABLE = aws_dynamodb_table.sentiment_cache.name
      COMPREHEND_ROLE_ARN   = aws_iam_role.comprehend_role.arn
      ENVIRONMENT          = var.environment
      LOG_LEVEL           = var.log_level
    }
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
  timeout         = 30
  memory_size     = 512
  
  environment {
    variables = {
      DOCUMENTS_BUCKET     = aws_s3_bucket.documents.id
      JOB_RESULTS_TABLE    = aws_dynamodb_table.job_results.name
      STEP_FUNCTION_ARN    = aws_sfn_state_machine.sentiment_analysis.arn
      ENVIRONMENT          = var.environment
      LOG_LEVEL           = var.log_level
    }
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
  timeout         = 30
  memory_size     = 512
  
  environment {
    variables = {
      JOB_RESULTS_TABLE = aws_dynamodb_table.job_results.name
      ENVIRONMENT       = var.environment
      LOG_LEVEL        = var.log_level
    }
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
  timeout         = 30
  memory_size     = 512
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      LOG_LEVEL  = var.log_level
    }
  }
  
  tags = local.common_tags
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

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.sync_handler.function_name,
    aws_lambda_function.async_handler.function_name,
    aws_lambda_function.status_handler.function_name,
    aws_lambda_function.health_handler.function_name
  ])
  
  name              = "/aws/lambda/${each.key}"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}
```

### 2. Variables Configuration

Create `terraform/variables.tf`:
```hcl
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "log_level" {
  description = "Log level for Lambda functions"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "api_key_required" {
  description = "Whether API key is required"
  type        = bool
  default     = true
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "cache_ttl_days" {
  description = "Cache TTL in days"
  type        = number
  default     = 1
}

variable "max_concurrent_requests" {
  description = "Maximum concurrent requests"
  type        = number
  default     = 1000
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}
```

### 3. Outputs Configuration

Create `terraform/outputs.tf`:
```hcl
output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "sentiment_cache_table_name" {
  description = "Sentiment cache DynamoDB table name"
  value       = aws_dynamodb_table.sentiment_cache.name
}

output "job_results_table_name" {
  description = "Job results DynamoDB table name"
  value       = aws_dynamodb_table.job_results.name
}

output "documents_bucket_name" {
  description = "Documents S3 bucket name"
  value       = aws_s3_bucket.documents.id
}

output "step_function_arn" {
  description = "Step Functions state machine ARN"
  value       = aws_sfn_state_machine.sentiment_analysis.arn
}

output "lambda_function_arns" {
  description = "Lambda function ARNs"
  value = {
    sync_handler   = aws_lambda_function.sync_handler.arn
    async_handler  = aws_lambda_function.async_handler.arn
    status_handler = aws_lambda_function.status_handler.arn
    health_handler = aws_lambda_function.health_handler.arn
  }
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value       = [for log_group in aws_cloudwatch_log_group.lambda_logs : log_group.name]
}
```

---

## Environment Management

### 1. Terraform Cloud Workspace Configuration

#### Development Workspace
```hcl
# terraform/workspaces/dev.tfvars
environment = "dev"
log_level = "DEBUG"
log_retention_days = 7
api_key_required = false
enable_xray = true
cache_ttl_days = 1
max_concurrent_requests = 100
enable_cost_optimization = true
```

#### Staging Workspace
```hcl
# terraform/workspaces/staging.tfvars
environment = "staging"
log_level = "INFO"
log_retention_days = 14
api_key_required = true
enable_xray = true
cache_ttl_days = 1
max_concurrent_requests = 500
enable_cost_optimization = true
```

#### Production Workspace
```hcl
# terraform/workspaces/prod.tfvars
environment = "prod"
log_level = "WARNING"
log_retention_days = 30
api_key_required = true
enable_xray = true
cache_ttl_days = 7
max_concurrent_requests = 1000
enable_cost_optimization = true
```

### 2. Environment-Specific Variables

Set in Terraform Cloud workspace variables:

#### Sensitive Variables (Mark as sensitive)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `API_KEY_SECRET`
- `COMPREHEND_ROLE_ARN`

#### Non-Sensitive Variables
- `TF_VAR_environment`
- `TF_VAR_aws_region`
- `TF_VAR_log_level`
- `TF_VAR_log_retention_days`

---

## Deployment Workflows

### 1. GitHub Actions Integration

Create `.github/workflows/terraform-deploy.yml`:
```yaml
name: Terraform Deploy

on:
  push:
    branches: [main, develop]
    paths: ['terraform/**']
  pull_request:
    branches: [main]
    paths: ['terraform/**']

env:
  TF_CLI_ARGS: -no-color

jobs:
  terraform-plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.6.0
    
    - name: Terraform Format Check
      run: terraform fmt -check -recursive
    
    - name: Terraform Init
      run: terraform init
      working-directory: terraform
    
    - name: Terraform Validate
      run: terraform validate
      working-directory: terraform
    
    - name: Terraform Plan
      run: terraform plan -var-file="workspaces/${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}.tfvars"
      working-directory: terraform
      env:
        TF_CLOUD_ORGANIZATION: aurastream
        TF_WORKSPACE: aurastream-${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}
    
    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const output = `#### Terraform Plan 📖
          \`\`\`
          ${process.env.TF_PLAN}
          \`\`\`
          *Pusher: @${{ github.actor }}, Action: \`${{ github.event_name }}\`*`;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: output
          })

  terraform-apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: terraform-plan
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.6.0
    
    - name: Terraform Init
      run: terraform init
      working-directory: terraform
    
    - name: Terraform Apply
      run: terraform apply -auto-approve -var-file="workspaces/prod.tfvars"
      working-directory: terraform
      env:
        TF_CLOUD_ORGANIZATION: aurastream
        TF_WORKSPACE: aurastream-prod
```

### 2. Manual Deployment

```bash
# Initialize Terraform
cd terraform
terraform init

# Select workspace
terraform workspace select aurastream-dev

# Plan deployment
terraform plan -var-file="workspaces/dev.tfvars"

# Apply changes
terraform apply -var-file="workspaces/dev.tfvars"

# Verify deployment
terraform output
```

---

## State Management

### 1. Remote State Configuration

Terraform Cloud automatically manages state with:
- **Encryption**: State encrypted at rest and in transit
- **Locking**: Automatic state locking during operations
- **Versioning**: State history and rollback capabilities
- **Access Control**: Team-based permissions

### 2. State Security

```hcl
# terraform/backend.tf
terraform {
  backend "remote" {
    organization = "aurastream"
    
    workspaces {
      name = "aurastream-*"
    }
  }
}
```

### 3. State Operations

```bash
# List workspaces
terraform workspace list

# Show current state
terraform show

# Import existing resources
terraform import aws_s3_bucket.documents existing-bucket-name

# Remove resources from state
terraform state rm aws_s3_bucket.old_bucket
```

---

## Security & Compliance

### 1. IAM Roles and Policies

Create `terraform/iam.tf`:
```hcl
# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Comprehend policy
resource "aws_iam_role_policy" "lambda_comprehend" {
  name = "${local.name_prefix}-lambda-comprehend"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectSentiment",
          "comprehend:DetectPiiEntities",
          "comprehend:StartSentimentDetectionJob",
          "comprehend:DescribeSentimentDetectionJob"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda DynamoDB policy
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${local.name_prefix}-lambda-dynamodb"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.sentiment_cache.arn,
          aws_dynamodb_table.job_results.arn
        ]
      }
    ]
  })
}

# Lambda S3 policy
resource "aws_iam_role_policy" "lambda_s3" {
  name = "${local.name_prefix}-lambda-s3"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.documents.arn}/*"
      }
    ]
  })
}

# Step Functions execution role
resource "aws_iam_role" "step_function_role" {
  name = "${local.name_prefix}-step-function-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Step Functions Lambda policy
resource "aws_iam_role_policy" "step_function_lambda" {
  name = "${local.name_prefix}-step-function-lambda"
  role = aws_iam_role.step_function_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.process_document.arn,
          aws_lambda_function.update_job_status.arn
        ]
      }
    ]
  })
}

# Comprehend service role
resource "aws_iam_role" "comprehend_role" {
  name = "${local.name_prefix}-comprehend-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "comprehend.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Comprehend S3 access policy
resource "aws_iam_role_policy_attachment" "comprehend_s3" {
  role       = aws_iam_role.comprehend_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}
```

### 2. Security Best Practices

- **Least Privilege**: IAM roles with minimal required permissions
- **Encryption**: All data encrypted at rest and in transit
- **Network Security**: VPC endpoints and security groups
- **Audit Logging**: CloudTrail and CloudWatch logging
- **Secrets Management**: AWS Secrets Manager for sensitive data

---

## Monitoring & Observability

### 1. CloudWatch Dashboards

Create `terraform/monitoring.tf`:
```hcl
# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
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
            [".", "Duration", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics"
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
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.sentiment_cache.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Metrics"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
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
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
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
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
  
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
```

### 2. Cost Monitoring

```hcl
# Cost allocation tags
resource "aws_cost_allocation_tags" "main" {
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
}
```

---

## Troubleshooting

### 1. Common Issues

#### State Lock Issues
```bash
# Force unlock state (use with caution)
terraform force-unlock <lock-id>
```

#### Resource Conflicts
```bash
# Import existing resources
terraform import aws_s3_bucket.documents existing-bucket-name

# Remove from state
terraform state rm aws_s3_bucket.old_bucket
```

#### Permission Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Terraform Cloud token
terraform login
```

### 2. Debugging

```bash
# Enable debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log

# Run with verbose output
terraform plan -verbose
terraform apply -verbose
```

### 3. Rollback Procedures

```bash
# Rollback to previous state
terraform workspace select aurastream-prod
terraform state list
terraform apply -target=aws_lambda_function.sync_handler

# Emergency rollback
terraform destroy -target=aws_lambda_function.sync_handler
terraform apply -target=aws_lambda_function.sync_handler
```

---

## Best Practices

### 1. Infrastructure as Code

- **Version Control**: All Terraform code in Git
- **Code Review**: Mandatory PR reviews for infrastructure changes
- **Testing**: Terraform plan validation in CI/CD
- **Documentation**: Comprehensive documentation for all resources

### 2. Environment Management

- **Workspace Isolation**: Separate workspaces for each environment
- **Variable Management**: Environment-specific variables in Terraform Cloud
- **State Management**: Remote state with encryption and locking
- **Access Control**: Team-based permissions and approval workflows

### 3. Security

- **Least Privilege**: Minimal IAM permissions
- **Encryption**: All data encrypted at rest and in transit
- **Secrets Management**: Sensitive data in Terraform Cloud variables
- **Audit Logging**: Comprehensive logging and monitoring

### 4. Monitoring

- **Dashboards**: Real-time monitoring dashboards
- **Alerts**: Proactive alerting for issues
- **Cost Monitoring**: Budget alerts and cost optimization
- **Performance**: SLA monitoring and optimization

### 5. Deployment

- **Automation**: Automated deployments via GitHub Actions
- **Approval Workflows**: Manual approval for production changes
- **Rollback**: Quick rollback procedures
- **Testing**: Comprehensive testing before deployment

---

This comprehensive Terraform Cloud deployment guide provides everything needed to deploy and manage AuraStream infrastructure with enterprise-grade reliability, security, and scalability.
