# AuraStream Terraform Infrastructure

This directory contains the Terraform configuration for deploying AuraStream infrastructure to AWS using Terraform Cloud.

## Overview

The Terraform configuration creates a complete serverless sentiment analysis platform with:

- **API Gateway**: RESTful API endpoints
- **Lambda Functions**: Serverless compute for sentiment analysis
- **DynamoDB**: NoSQL database for caching and job results
- **S3**: Object storage for document processing
- **Step Functions**: Workflow orchestration
- **SQS**: Message queuing for async processing
- **SNS**: Notification service for alerts
- **CloudWatch**: Monitoring and logging
- **WAF**: Web application firewall
- **CloudTrail**: Audit logging
- **KMS**: Encryption key management

## Prerequisites

1. **Terraform Cloud Account**: Sign up at [terraform.io](https://app.terraform.io)
2. **AWS Account**: With appropriate permissions
3. **Terraform CLI**: Version 1.0 or higher
4. **AWS CLI**: Configured with credentials

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Select Workspace

```bash
# For development
terraform workspace select aurastream-dev

# For staging
terraform workspace select aurastream-staging

# For production
terraform workspace select aurastream-prod
```

### 3. Plan Deployment

```bash
# Development
terraform plan -var-file="workspaces/dev.tfvars"

# Staging
terraform plan -var-file="workspaces/staging.tfvars"

# Production
terraform plan -var-file="workspaces/prod.tfvars"
```

### 4. Apply Changes

```bash
# Development
terraform apply -var-file="workspaces/dev.tfvars"

# Staging
terraform apply -var-file="workspaces/staging.tfvars"

# Production
terraform apply -var-file="workspaces/prod.tfvars"
```

## File Structure

```
terraform/
├── main.tf                 # Main infrastructure resources
├── iam.tf                  # IAM roles and policies
├── monitoring.tf           # CloudWatch monitoring and alerts
├── security.tf             # Security resources (WAF, CloudTrail, etc.)
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── versions.tf             # Provider requirements
├── workspaces/             # Environment-specific configurations
│   ├── dev.tfvars         # Development environment
│   ├── staging.tfvars     # Staging environment
│   └── prod.tfvars        # Production environment
└── README.md              # This file
```

## Environment Configuration

### Development (`dev.tfvars`)
- **Purpose**: Local development and testing
- **Features**: Debug logging, no API key required, minimal resources
- **Budget**: $100/month
- **Resources**: 256MB Lambda, 7-day log retention

### Staging (`staging.tfvars`)
- **Purpose**: Pre-production testing
- **Features**: Production-like settings, API key required, moderate resources
- **Budget**: $500/month
- **Resources**: 512MB Lambda, 14-day log retention

### Production (`prod.tfvars`)
- **Purpose**: Live production environment
- **Features**: Full security, monitoring, high availability
- **Budget**: $5000/month
- **Resources**: 1024MB Lambda, 30-day log retention

## Key Resources

### API Gateway
- **REST API**: Main API endpoint
- **Resources**: `/analyze/sync`, `/analyze/async`, `/status/{job_id}`, `/health`
- **Methods**: POST for analysis, GET for status and health
- **Integration**: Lambda proxy integration

### Lambda Functions
- **sync_handler**: Real-time sentiment analysis
- **async_handler**: Asynchronous job submission
- **status_handler**: Job status retrieval
- **health_handler**: Health check endpoint
- **process_document**: Document processing in Step Functions
- **update_job_status**: Job status updates

### DynamoDB Tables
- **sentiment_cache**: Cached sentiment analysis results
- **job_results**: Asynchronous job results and status

### S3 Bucket
- **documents**: Storage for large documents and processing results
- **Features**: Versioning, encryption, lifecycle policies

### Step Functions
- **sentiment_analysis**: Workflow for processing large documents
- **States**: ProcessDocument → UpdateJobStatus

### Monitoring
- **CloudWatch Dashboard**: Real-time metrics visualization
- **Alarms**: Error rates, duration, throttles, failures
- **Log Groups**: Centralized logging for all Lambda functions
- **Custom Metrics**: Business metrics (sentiment analysis count, cache hits)

### Security
- **WAF**: Web application firewall with rate limiting
- **CloudTrail**: Audit logging for all API calls
- **KMS**: Encryption key management
- **GuardDuty**: Threat detection (optional)
- **Config**: Compliance monitoring

## Variables

### Required Variables
- `environment`: Environment name (dev, staging, prod)
- `aws_region`: AWS region for deployment
- `alert_email`: Email address for alerts

### Optional Variables
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_retention_days`: CloudWatch log retention period
- `api_key_required`: Whether API key authentication is required
- `enable_xray`: Enable X-Ray tracing
- `cache_ttl_days`: Cache TTL in days
- `max_concurrent_requests`: Maximum concurrent requests
- `enable_cost_optimization`: Enable cost optimization features
- `monthly_budget_limit`: Monthly budget limit in USD
- `enable_monitoring`: Enable comprehensive monitoring
- `enable_security_monitoring`: Enable security monitoring
- `backup_retention_days`: Backup retention period
- `enable_auto_scaling`: Enable auto-scaling
- `lambda_memory_size`: Lambda function memory size
- `lambda_timeout`: Lambda function timeout

## Outputs

The configuration provides comprehensive outputs including:

- **API Gateway**: URL, ID, execution ARN
- **Lambda Functions**: ARNs and names for all functions
- **DynamoDB**: Table names and ARNs
- **S3**: Bucket name and ARN
- **Step Functions**: State machine ARN and name
- **CloudWatch**: Log group names and dashboard URL
- **SNS**: Topic ARN for alerts
- **IAM**: Role ARNs for all services
- **Environment**: Environment information and deployment time
- **Cost**: Budget information and monitoring
- **Security**: Security configuration status

## Deployment Commands

### Using Makefile

```bash
# Initialize Terraform
make terraform-init

# Plan deployment
make terraform-plan

# Deploy to development
make deploy-dev

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod

# Format Terraform files
make terraform-fmt

# List workspaces
make terraform-workspace
```

### Using Terraform CLI

```bash
# Initialize
terraform init

# Select workspace
terraform workspace select aurastream-dev

# Plan
terraform plan -var-file="workspaces/dev.tfvars"

# Apply
terraform apply -var-file="workspaces/dev.tfvars"

# Destroy (use with caution)
terraform destroy -var-file="workspaces/dev.tfvars"
```

## CI/CD Integration

The configuration includes GitHub Actions workflows for automated deployment:

- **Pull Request**: Terraform plan validation
- **Development**: Auto-deploy on push to `develop` branch
- **Production**: Auto-deploy on push to `main` branch

## Security Considerations

1. **Least Privilege**: IAM roles with minimal required permissions
2. **Encryption**: All data encrypted at rest and in transit
3. **Network Security**: VPC endpoints and security groups
4. **Audit Logging**: CloudTrail for all API calls
5. **Secrets Management**: Sensitive data in Terraform Cloud variables
6. **WAF Protection**: Rate limiting and attack prevention

## Cost Optimization

1. **Pay-per-Request**: DynamoDB and Lambda pricing
2. **S3 Lifecycle**: Automatic transition to cheaper storage classes
3. **Log Retention**: Configurable log retention periods
4. **Budget Alerts**: Cost monitoring and alerts
5. **Resource Tagging**: Cost allocation and tracking

## Troubleshooting

### Common Issues

1. **State Lock**: Use `terraform force-unlock <lock-id>` if needed
2. **Permission Errors**: Verify AWS credentials and IAM permissions
3. **Resource Conflicts**: Check for existing resources with same names
4. **Variable Issues**: Ensure all required variables are set

### Debug Commands

```bash
# Enable debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Show current state
terraform show

# List resources
terraform state list
```

## Best Practices

1. **Version Control**: All Terraform code in Git
2. **Code Review**: Mandatory PR reviews for infrastructure changes
3. **Testing**: Terraform plan validation in CI/CD
4. **Documentation**: Keep this README updated
5. **State Management**: Use Terraform Cloud for state storage
6. **Environment Isolation**: Separate workspaces for each environment
7. **Security**: Regular security audits and updates
8. **Monitoring**: Comprehensive monitoring and alerting

## Support

For issues and questions:

1. Check the [Terraform Cloud Deployment Guide](../docs/AuraStream_Terraform_Cloud_Deployment_Guide.md)
2. Review the [Operations Runbook](../docs/AuraStream_Operations_Runbook.md)
3. Check the [Security & Compliance Guide](../docs/AuraStream_Security_Compliance_Guide.md)
4. Open an issue in the GitHub repository

## License

This Terraform configuration is part of the AuraStream project and is licensed under the same terms as the main project.
