# Staging Environment Configuration
environment = "staging"
aws_region = "us-east-1"
log_level = "INFO"
log_retention_days = 14
api_key_required = true
enable_xray = true
cache_ttl_days = 1
max_concurrent_requests = 500
enable_cost_optimization = true
monthly_budget_limit = 500
alert_email = "staging-alerts@aurastream.com"
enable_monitoring = true
enable_security_monitoring = true
backup_retention_days = 14
enable_auto_scaling = true
lambda_memory_size = 512
lambda_timeout = 30