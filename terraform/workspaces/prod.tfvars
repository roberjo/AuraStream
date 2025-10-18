# Production Environment Configuration
environment = "prod"
aws_region = "us-east-1"
log_level = "WARNING"
log_retention_days = 30
api_key_required = true
enable_xray = true
cache_ttl_days = 7
max_concurrent_requests = 1000
enable_cost_optimization = true
monthly_budget_limit = 5000
alert_email = "prod-alerts@aurastream.com"
enable_monitoring = true
enable_security_monitoring = true
backup_retention_days = 90
enable_auto_scaling = true
lambda_memory_size = 1024
lambda_timeout = 60
