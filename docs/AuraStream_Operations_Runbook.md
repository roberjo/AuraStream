# AuraStream Operations Runbook

## Table of Contents
1. [Overview](#overview)
2. [System Health Monitoring](#system-health-monitoring)
3. [Incident Response](#incident-response)
4. [Routine Operations](#routine-operations)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Performance Optimization](#performance-optimization)
7. [Security Operations](#security-operations)
8. [Backup and Recovery](#backup-and-recovery)
9. [Capacity Planning](#capacity-planning)
10. [Emergency Procedures](#emergency-procedures)

---

## Overview

### Purpose

This runbook provides operational procedures for maintaining, monitoring, and troubleshooting the AuraStream sentiment analysis platform. It serves as the primary reference for operations teams, SREs, and on-call engineers.

### System Components

- **API Gateway**: REST API endpoint and request routing
- **Lambda Functions**: Serverless compute for request processing
- **DynamoDB**: NoSQL database for caching and job results
- **S3**: Object storage for documents and backups
- **Step Functions**: Workflow orchestration for batch processing
- **CloudWatch**: Monitoring, logging, and alerting
- **Amazon Comprehend**: ML service for sentiment analysis

### Service Level Objectives (SLOs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Availability** | 99.9% | Monthly uptime |
| **Latency (P99)** | < 1000ms | Sync API response time |
| **Error Rate** | < 1% | 4xx/5xx error percentage |
| **Throughput** | 1000 RPS | Sustained requests per second |
| **Job Processing** | < 5 minutes | Async job completion time |

---

## System Health Monitoring

### Key Metrics Dashboard

#### Real-Time Health Dashboard

**Primary Metrics**:
- API Gateway 4xx/5xx error rate
- Lambda function duration and errors
- DynamoDB throttling events
- Comprehend API success rate
- Cache hit rate percentage

**Secondary Metrics**:
- Request volume trends
- Cost per analysis
- Customer usage patterns
- PII detection rate

#### CloudWatch Dashboards

**Operational Dashboard** (`AuraStream-Operations`):
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "4XXError", "ApiName", "aurastream-api"],
          ["AWS/ApiGateway", "5XXError", "ApiName", "aurastream-api"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Gateway Errors"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", "FunctionName", "SyncHandler"],
          ["AWS/Lambda", "Errors", "FunctionName", "SyncHandler"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Performance"
      }
    }
  ]
}
```

### Alerting Configuration

#### Critical Alerts (PagerDuty)

| Alert | Condition | Action |
|-------|-----------|--------|
| **High Error Rate** | Error rate > 5% for 5 minutes | Page on-call engineer |
| **Service Down** | Health check failures > 3 | Page on-call engineer |
| **High Latency** | P99 latency > 2000ms for 10 minutes | Page on-call engineer |
| **Cost Anomaly** | Daily cost > 150% of baseline | Page engineering manager |

#### Warning Alerts (Slack)

| Alert | Condition | Action |
|-------|-----------|--------|
| **Cache Hit Rate Low** | Cache hit rate < 50% for 30 minutes | Slack notification |
| **DynamoDB Throttling** | Throttling events > 10 in 5 minutes | Slack notification |
| **Queue Depth High** | SQS queue depth > 100 messages | Slack notification |
| **Lambda Cold Starts** | Cold start duration > 5 seconds | Slack notification |

### Health Check Endpoints

#### API Health Check

```bash
# Basic health check
curl -X GET "https://api.aurastream.com/v1/health"

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.2.3",
  "components": {
    "api_gateway": "healthy",
    "lambda": "healthy",
    "dynamodb": "healthy",
    "comprehend": "healthy"
  }
}
```

#### Component Health Checks

```bash
# Check DynamoDB connectivity
aws dynamodb describe-table --table-name AuraStream-SentimentCache

# Check Lambda function status
aws lambda get-function --function-name SyncHandler

# Check S3 bucket access
aws s3 ls s3://aura-stream-documents/

# Check Comprehend service
aws comprehend detect-sentiment --text "test" --language-code en
```

---

## Incident Response

### Incident Severity Levels

#### P1 - Critical (Response: 15 minutes)
- Service completely down
- Data loss or corruption
- Security breach
- Customer-facing functionality broken

#### P2 - High (Response: 1 hour)
- Significant performance degradation
- Partial service outage
- High error rates
- Customer impact

#### P3 - Medium (Response: 4 hours)
- Minor performance issues
- Non-critical feature failures
- Monitoring alerts
- Internal tool issues

#### P4 - Low (Response: 24 hours)
- Documentation issues
- Enhancement requests
- Non-urgent bugs

### Incident Response Process

#### 1. Detection and Assessment

```bash
# Check system status
curl -X GET "https://api.aurastream.com/v1/health"

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=aurastream-api \
  --start-time 2024-01-15T09:00:00Z \
  --end-time 2024-01-15T10:00:00Z \
  --period 300 \
  --statistics Sum

# Check recent logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/SyncHandler \
  --start-time 1642248000000 \
  --end-time 1642251600000
```

#### 2. Communication

**Immediate Actions**:
1. Acknowledge incident in PagerDuty
2. Post in #incidents Slack channel
3. Update status page if customer-facing
4. Notify stakeholders

**Communication Template**:
```
🚨 INCIDENT: [P1/P2/P3/P4] - [Brief Description]
Status: Investigating
Impact: [Customer impact description]
ETA: [Estimated resolution time]
Owner: [Incident commander]
```

#### 3. Investigation

**Common Investigation Steps**:

1. **Check Recent Deployments**
   ```bash
   # Check recent CloudFormation changes
   aws cloudformation describe-stack-events \
     --stack-name aurastream-prod \
     --max-items 20
   ```

2. **Analyze Error Patterns**
   ```bash
   # Check error logs
   aws logs filter-log-events \
     --log-group-name /aws/lambda/SyncHandler \
     --filter-pattern "ERROR"
   ```

3. **Check Resource Utilization**
   ```bash
   # Check Lambda concurrency
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name ConcurrentExecutions \
     --dimensions Name=FunctionName,Value=SyncHandler \
     --start-time 2024-01-15T09:00:00Z \
     --end-time 2024-01-15T10:00:00Z \
     --period 300 \
     --statistics Maximum
   ```

#### 4. Resolution

**Common Resolution Actions**:

1. **Scale Resources**
   ```bash
   # Increase Lambda concurrency
   aws lambda put-provisioned-concurrency-config \
     --function-name SyncHandler \
     --provisioned-concurrency-config ProvisionedConcurrencyConfig={ProvisionedConcurrency=100}
   ```

2. **Restart Services**
   ```bash
   # Update Lambda function to trigger restart
   aws lambda update-function-code \
     --function-name SyncHandler \
     --s3-bucket deployment-bucket \
     --s3-key function.zip
   ```

3. **Failover to DR Region**
   ```bash
   # Update Route 53 health checks
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z123456789 \
     --change-batch file://failover.json
   ```

#### 5. Post-Incident

**Post-Incident Actions**:
1. Update incident status to resolved
2. Conduct post-mortem within 48 hours
3. Document lessons learned
4. Update runbook with new procedures
5. Implement preventive measures

### Common Incident Scenarios

#### Scenario 1: High Error Rate

**Symptoms**:
- API Gateway 5xx errors > 10%
- Customer complaints
- Monitoring alerts firing

**Investigation**:
```bash
# Check Lambda function errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SyncHandler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check DynamoDB throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=AuraStream-SentimentCache \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --period 300 \
  --statistics Sum
```

**Resolution**:
1. Check for DynamoDB throttling
2. Increase DynamoDB capacity if needed
3. Check Lambda function logs for errors
4. Restart Lambda function if necessary

#### Scenario 2: High Latency

**Symptoms**:
- P99 latency > 2000ms
- Customer complaints about slow responses
- Timeout errors

**Investigation**:
```bash
# Check Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=SyncHandler \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --period 300 \
  --statistics p99

# Check Comprehend API latency
aws logs filter-log-events \
  --log-group-name /aws/lambda/SyncHandler \
  --filter-pattern "comprehend" \
  --start-time $(date -d '1 hour ago' +%s)000
```

**Resolution**:
1. Check Comprehend API status
2. Implement circuit breaker if Comprehend is slow
3. Increase Lambda memory allocation
4. Check for cold start issues

#### Scenario 3: Service Completely Down

**Symptoms**:
- All API requests failing
- Health check endpoint down
- No Lambda function invocations

**Investigation**:
```bash
# Check API Gateway status
aws apigateway get-rest-api --rest-api-id your-api-id

# Check Lambda function status
aws lambda get-function --function-name SyncHandler

# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name aurastream-prod
```

**Resolution**:
1. Check AWS service status
2. Verify IAM permissions
3. Check for resource limits
4. Consider failover to DR region

---

## Routine Operations

### Daily Operations

#### Morning Health Check (9:00 AM)

```bash
#!/bin/bash
# scripts/daily_health_check.sh

echo "=== AuraStream Daily Health Check ==="
echo "Date: $(date)"
echo ""

# Check API health
echo "1. API Health Check:"
curl -s -X GET "https://api.aurastream.com/v1/health" | jq '.'

# Check error rates
echo "2. Error Rate Check:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=aurastream-api \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Sum

# Check cache hit rate
echo "3. Cache Hit Rate:"
aws cloudwatch get-metric-statistics \
  --namespace AuraStream \
  --metric-name CacheHitRate \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Average

# Check costs
echo "4. Daily Cost Check:"
aws ce get-cost-and-usage \
  --time-period Start=2024-01-14,End=2024-01-15 \
  --granularity DAILY \
  --metrics BlendedCost

echo "=== Health Check Complete ==="
```

#### Performance Review

**Daily Metrics to Review**:
- API response times (P50, P95, P99)
- Error rates by endpoint
- Cache hit rates
- Cost per analysis
- Customer usage patterns

### Weekly Operations

#### Capacity Planning Review

```bash
#!/bin/bash
# scripts/weekly_capacity_review.sh

echo "=== Weekly Capacity Review ==="
echo "Week of: $(date)"

# Lambda concurrency trends
echo "1. Lambda Concurrency Trends:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=SyncHandler \
  --start-time $(date -d '7 days ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Maximum

# DynamoDB capacity utilization
echo "2. DynamoDB Capacity Utilization:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=AuraStream-SentimentCache \
  --start-time $(date -d '7 days ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Maximum

# Cost trends
echo "3. Weekly Cost Trends:"
aws ce get-cost-and-usage \
  --time-period Start=2024-01-08,End=2024-01-15 \
  --granularity DAILY \
  --metrics BlendedCost

echo "=== Capacity Review Complete ==="
```

#### Security Review

**Weekly Security Tasks**:
1. Review access logs for anomalies
2. Check for failed authentication attempts
3. Verify API key usage patterns
4. Review IAM permissions
5. Check for security vulnerabilities

### Monthly Operations

#### Cost Optimization Review

```bash
#!/bin/bash
# scripts/monthly_cost_review.sh

echo "=== Monthly Cost Optimization Review ==="
echo "Month: $(date +%Y-%m)"

# Monthly cost breakdown
echo "1. Monthly Cost Breakdown:"
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --group-by Type=DIMENSION,Key=SERVICE \
  --metrics BlendedCost

# Cost per analysis trend
echo "2. Cost per Analysis Trend:"
# Calculate based on usage metrics and costs

# Resource utilization analysis
echo "3. Resource Utilization Analysis:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=SyncHandler \
  --start-time $(date -d '30 days ago' +%s) \
  --end-time $(date +%s) \
  --period 86400 \
  --statistics Average

echo "=== Cost Review Complete ==="
```

#### Disaster Recovery Testing

**Monthly DR Tests**:
1. Test backup restoration
2. Verify cross-region replication
3. Test failover procedures
4. Validate recovery time objectives
5. Update DR documentation

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. High Lambda Cold Start Duration

**Symptoms**:
- First request after idle period is slow
- P99 latency spikes
- Customer complaints about slow responses

**Diagnosis**:
```bash
# Check cold start metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name InitDuration \
  --dimensions Name=FunctionName,Value=SyncHandler \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --period 300 \
  --statistics Average
```

**Solutions**:
1. **Enable Provisioned Concurrency**
   ```bash
   aws lambda put-provisioned-concurrency-config \
     --function-name SyncHandler \
     --provisioned-concurrency-config ProvisionedConcurrencyConfig={ProvisionedConcurrency=10}
   ```

2. **Optimize Lambda Package Size**
   - Remove unused dependencies
   - Use Lambda layers for common libraries
   - Minimize import statements

3. **Use ARM64 Architecture**
   ```yaml
   # In template.yaml
   Properties:
     Architectures:
       - arm64
   ```

#### 2. DynamoDB Throttling

**Symptoms**:
- DynamoDB throttling errors in logs
- High latency for cache operations
- Reduced cache hit rates

**Diagnosis**:
```bash
# Check throttling metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=AuraStream-SentimentCache \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --period 300 \
  --statistics Sum
```

**Solutions**:
1. **Switch to On-Demand Billing**
   ```bash
   aws dynamodb update-table \
     --table-name AuraStream-SentimentCache \
     --billing-mode PAY_PER_REQUEST
   ```

2. **Implement Exponential Backoff**
   ```python
   import boto3
   from botocore.exceptions import ClientError
   import time
   import random

   def dynamodb_operation_with_retry(operation, max_retries=3):
       for attempt in range(max_retries):
           try:
               return operation()
           except ClientError as e:
               if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   time.sleep(wait_time)
                   continue
               raise
   ```

3. **Optimize Query Patterns**
   - Use batch operations where possible
   - Implement connection pooling
   - Cache frequently accessed data

#### 3. Comprehend API Failures

**Symptoms**:
- Comprehend API errors in logs
- High error rates for sentiment analysis
- Timeout errors

**Diagnosis**:
```bash
# Check Comprehend API errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SyncHandler \
  --filter-pattern "comprehend" \
  --start-time $(date -d '1 hour ago' +%s)000
```

**Solutions**:
1. **Implement Circuit Breaker**
   ```python
   class ComprehendCircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
       
       def call(self, func, *args, **kwargs):
           if self.state == 'OPEN':
               if time.time() - self.last_failure_time > self.timeout:
                   self.state = 'HALF_OPEN'
               else:
                   raise Exception("Circuit breaker is OPEN")
           
           try:
               result = func(*args, **kwargs)
               if self.state == 'HALF_OPEN':
                   self.state = 'CLOSED'
                   self.failure_count = 0
               return result
           except Exception as e:
               self.failure_count += 1
               self.last_failure_time = time.time()
               
               if self.failure_count >= self.failure_threshold:
                   self.state = 'OPEN'
               raise
   ```

2. **Implement Retry Logic**
   ```python
   import boto3
   from botocore.exceptions import ClientError
   import time

   def comprehend_with_retry(text, language_code, max_retries=3):
       comprehend = boto3.client('comprehend')
       
       for attempt in range(max_retries):
           try:
               response = comprehend.detect_sentiment(
                   Text=text,
                   LanguageCode=language_code
               )
               return response
           except ClientError as e:
               if e.response['Error']['Code'] in ['ThrottlingException', 'ServiceUnavailableException']:
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   time.sleep(wait_time)
                   continue
               raise
   ```

#### 4. Cache Hit Rate Issues

**Symptoms**:
- Low cache hit rates (< 50%)
- High Comprehend API costs
- Increased latency

**Diagnosis**:
```bash
# Check cache hit rate
aws cloudwatch get-metric-statistics \
  --namespace AuraStream \
  --metric-name CacheHitRate \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Average
```

**Solutions**:
1. **Improve Text Normalization**
   ```python
   import re
   import hashlib

   def normalize_text(text):
       # Convert to lowercase
       text = text.lower()
       
       # Remove extra whitespace
       text = re.sub(r'\s+', ' ', text)
       
       # Remove punctuation (optional)
       text = re.sub(r'[^\w\s]', '', text)
       
       # Trim whitespace
       text = text.strip()
       
       return text

   def generate_cache_key(text):
       normalized = normalize_text(text)
       return hashlib.sha256(normalized.encode()).hexdigest()
   ```

2. **Optimize TTL Settings**
   ```python
   # Adjust TTL based on text type
   def get_cache_ttl(text):
       if len(text) < 100:  # Short texts change frequently
           return 3600  # 1 hour
       elif len(text) < 1000:  # Medium texts
           return 86400  # 24 hours
       else:  # Long texts are more stable
           return 604800  # 7 days
   ```

3. **Implement Cache Warming**
   ```python
   def warm_cache(popular_texts):
       for text in popular_texts:
           try:
               result = analyze_sentiment(text)
               cache.set(generate_cache_key(text), result)
           except Exception as e:
               logger.warning(f"Failed to warm cache for text: {e}")
   ```

### Performance Tuning

#### Lambda Optimization

1. **Memory Allocation**
   ```yaml
   # In template.yaml
   Properties:
     MemorySize: 512  # Start with 512MB, adjust based on usage
     Timeout: 30  # 30 seconds timeout
   ```

2. **Environment Variables**
   ```python
   import os
   
   # Use environment variables for configuration
   CACHE_TTL = int(os.environ.get('CACHE_TTL', 86400))
   MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
   ENABLE_PII_DETECTION = os.environ.get('ENABLE_PII_DETECTION', 'true').lower() == 'true'
   ```

3. **Connection Pooling**
   ```python
   import boto3
   from botocore.config import Config

   # Configure connection pooling
   config = Config(
       max_pool_connections=50,
       retries={'max_attempts': 3}
   )
   
   dynamodb = boto3.resource('dynamodb', config=config)
   comprehend = boto3.client('comprehend', config=config)
   ```

#### DynamoDB Optimization

1. **Query Optimization**
   ```python
   # Use batch operations
   def batch_get_cached_results(cache_keys):
       with dynamodb.batch_get_item() as batch:
           batch.get_item(
               RequestItems={
                   'AuraStream-SentimentCache': {
                       'Keys': [{'text_hash': key} for key in cache_keys]
                   }
               }
           )
   ```

2. **Index Optimization**
   ```yaml
   # Add GSI for common query patterns
   GlobalSecondaryIndexes:
     - IndexName: CreatedAtIndex
       KeySchema:
         - AttributeName: created_at
           KeyType: HASH
       Projection:
         ProjectionType: ALL
   ```

---

## Performance Optimization

### Monitoring Performance Metrics

#### Key Performance Indicators

1. **Response Time Metrics**
   - P50, P95, P99 latency
   - Cold start duration
   - Cache hit latency

2. **Throughput Metrics**
   - Requests per second
   - Concurrent executions
   - Queue processing rate

3. **Resource Utilization**
   - Lambda memory usage
   - DynamoDB read/write capacity
   - API Gateway throttling

#### Performance Testing

```bash
#!/bin/bash
# scripts/performance_test.sh

echo "=== AuraStream Performance Test ==="

# Test sync endpoint
echo "1. Testing Sync Endpoint:"
for i in {1..100}; do
  curl -s -w "%{time_total}\n" -o /dev/null \
    -X POST "https://api.aurastream.com/v1/analyze/sync" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"text": "This is a test message for performance testing"}' &
done
wait

# Test async endpoint
echo "2. Testing Async Endpoint:"
for i in {1..10}; do
  curl -s -w "%{time_total}\n" -o /dev/null \
    -X POST "https://api.aurastream.com/v1/analyze/async" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"text": "This is a large document for async processing test"}' &
done
wait

echo "=== Performance Test Complete ==="
```

### Optimization Strategies

#### 1. Caching Optimization

```python
# Implement multi-level caching
class MultiLevelCache:
    def __init__(self):
        self.memory_cache = {}  # In-memory cache
        self.dynamodb_cache = DynamoDBCache()  # Persistent cache
    
    def get(self, key):
        # Check memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Check DynamoDB cache
        result = self.dynamodb_cache.get(key)
        if result:
            self.memory_cache[key] = result
            return result
        
        return None
    
    def set(self, key, value, ttl=3600):
        # Set in both caches
        self.memory_cache[key] = value
        self.dynamodb_cache.set(key, value, ttl)
```

#### 2. Batch Processing Optimization

```python
# Optimize batch operations
def batch_analyze_sentiments(texts):
    # Group texts by language for batch processing
    texts_by_language = {}
    for text in texts:
        language = detect_language(text)
        if language not in texts_by_language:
            texts_by_language[language] = []
        texts_by_language[language].append(text)
    
    results = []
    for language, language_texts in texts_by_language.items():
        # Use Comprehend batch API for each language
        batch_results = comprehend.batch_detect_sentiment(
            TextList=language_texts,
            LanguageCode=language
        )
        results.extend(batch_results['ResultList'])
    
    return results
```

#### 3. Connection Optimization

```python
# Optimize AWS client connections
import boto3
from botocore.config import Config

# Global clients with optimized configuration
config = Config(
    max_pool_connections=100,
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    read_timeout=30,
    connect_timeout=10
)

# Reuse clients across Lambda invocations
dynamodb = boto3.resource('dynamodb', config=config)
comprehend = boto3.client('comprehend', config=config)
```

---

## Security Operations

### Security Monitoring

#### Security Metrics

1. **Authentication Metrics**
   - Failed API key attempts
   - Invalid authentication requests
   - API key usage patterns

2. **Authorization Metrics**
   - Permission denied errors
   - Unauthorized access attempts
   - IAM policy violations

3. **Data Protection Metrics**
   - PII detection rate
   - Data encryption compliance
   - Access pattern anomalies

#### Security Alerts

```bash
# Monitor failed authentication attempts
aws logs filter-log-events \
  --log-group-name /aws/apigateway/aurastream-api \
  --filter-pattern "401" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check for suspicious API usage patterns
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 4XXError \
  --dimensions Name=ApiName,Value=aurastream-api \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Sum
```

### Security Incident Response

#### Security Incident Types

1. **API Key Compromise**
   - Immediate revocation of compromised key
   - Investigation of usage patterns
   - Notification to affected customers

2. **Data Breach**
   - Immediate containment
   - Forensic investigation
   - Regulatory notification if required

3. **DDoS Attack**
   - Enable AWS Shield
   - Implement rate limiting
   - Monitor for attack patterns

#### Security Response Procedures

```bash
#!/bin/bash
# scripts/security_incident_response.sh

echo "=== Security Incident Response ==="

# 1. Revoke compromised API key
echo "1. Revoking compromised API key..."
aws apigateway delete-api-key --api-key $COMPROMISED_API_KEY

# 2. Check usage patterns
echo "2. Checking usage patterns..."
aws logs filter-log-events \
  --log-group-name /aws/apigateway/aurastream-api \
  --filter-pattern $COMPROMISED_API_KEY \
  --start-time $(date -d '7 days ago' +%s)000

# 3. Enable additional monitoring
echo "3. Enabling additional monitoring..."
aws cloudwatch put-metric-alarm \
  --alarm-name "High-API-Errors" \
  --alarm-description "High number of API errors" \
  --metric-name 4XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold

echo "=== Security Response Complete ==="
```

---

## Backup and Recovery

### Backup Strategy

#### Data Backup

1. **DynamoDB Backups**
   ```bash
   # Enable point-in-time recovery
   aws dynamodb update-continuous-backups \
     --table-name AuraStream-SentimentCache \
     --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
   
   # Create on-demand backup
   aws dynamodb create-backup \
     --table-name AuraStream-SentimentCache \
     --backup-name "backup-$(date +%Y%m%d-%H%M%S)"
   ```

2. **S3 Cross-Region Replication**
   ```bash
   # Configure cross-region replication
   aws s3api put-bucket-replication \
     --bucket aura-stream-documents \
     --replication-configuration file://replication-config.json
   ```

3. **Lambda Code Backup**
   ```bash
   # Backup Lambda function code
   aws lambda get-function \
     --function-name SyncHandler \
     --query 'Code.Location' \
     --output text | xargs wget -O sync-handler.zip
   ```

#### Infrastructure Backup

1. **CloudFormation Templates**
   - Version controlled in Git
   - Automated backup to S3
   - Cross-region replication

2. **Configuration Backup**
   - Parameter Store values
   - Secrets Manager secrets
   - IAM policies and roles

### Recovery Procedures

#### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour

#### Recovery Steps

```bash
#!/bin/bash
# scripts/disaster_recovery.sh

echo "=== Disaster Recovery Procedure ==="

# 1. Assess the situation
echo "1. Assessing disaster situation..."
aws cloudformation describe-stacks --stack-name aurastream-prod

# 2. Activate DR region
echo "2. Activating DR region..."
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name aurastream-dr \
  --region us-west-2 \
  --capabilities CAPABILITY_IAM

# 3. Restore data
echo "3. Restoring data..."
aws dynamodb restore-table-from-backup \
  --target-table-name AuraStream-SentimentCache \
  --backup-arn $BACKUP_ARN

# 4. Update DNS
echo "4. Updating DNS..."
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://failover.json

# 5. Validate service
echo "5. Validating service..."
curl -X GET "https://api.aurastream.com/v1/health"

echo "=== Disaster Recovery Complete ==="
```

---

## Capacity Planning

### Capacity Metrics

#### Current Capacity

1. **API Gateway**
   - Default throttling: 10,000 requests/second
   - Burst capacity: 5,000 requests
   - Regional limits: 10,000 requests/second

2. **Lambda**
   - Concurrent executions: 1,000 (default)
   - Memory allocation: 512MB per function
   - Timeout: 30 seconds

3. **DynamoDB**
   - On-demand billing mode
   - Auto-scaling enabled
   - No capacity limits

#### Capacity Planning Process

```bash
#!/bin/bash
# scripts/capacity_planning.sh

echo "=== Capacity Planning Analysis ==="

# 1. Analyze current usage
echo "1. Analyzing current usage..."
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=aurastream-api \
  --start-time $(date -d '30 days ago' +%s) \
  --end-time $(date +%s) \
  --period 86400 \
  --statistics Sum

# 2. Project future growth
echo "2. Projecting future growth..."
# Calculate growth rate and project 3 months ahead

# 3. Identify bottlenecks
echo "3. Identifying bottlenecks..."
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=SyncHandler \
  --start-time $(date -d '7 days ago' +%s) \
  --end-time $(date +%s) \
  --period 3600 \
  --statistics Maximum

# 4. Recommend scaling actions
echo "4. Recommending scaling actions..."
# Based on analysis, recommend:
# - Increase Lambda concurrency limits
# - Add provisioned concurrency
# - Scale DynamoDB capacity
# - Implement auto-scaling

echo "=== Capacity Planning Complete ==="
```

### Scaling Strategies

#### Horizontal Scaling

1. **Lambda Concurrency**
   ```bash
   # Increase concurrent execution limit
   aws lambda put-reserved-concurrency-config \
     --function-name SyncHandler \
     --reserved-concurrency-config ReservedConcurrencyConfig={ReservedConcurrency=2000}
   ```

2. **API Gateway Throttling**
   ```bash
   # Create usage plan with higher limits
   aws apigateway create-usage-plan \
     --name "High-Volume-Plan" \
     --throttle burstLimit=10000,rateLimit=1000
   ```

#### Vertical Scaling

1. **Lambda Memory**
   ```yaml
   # In template.yaml
   Properties:
     MemorySize: 1024  # Increase from 512MB to 1GB
   ```

2. **DynamoDB Capacity**
   ```bash
   # Switch to provisioned capacity for predictable workloads
   aws dynamodb update-table \
     --table-name AuraStream-SentimentCache \
     --billing-mode PROVISIONED \
     --provisioned-throughput ReadCapacityUnits=1000,WriteCapacityUnits=1000
   ```

---

## Emergency Procedures

### Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| **On-Call Engineer** | +1-555-ONCALL | PagerDuty |
| **Engineering Manager** | +1-555-MANAGER | Direct |
| **CTO** | +1-555-CTO | Direct |
| **AWS Support** | Enterprise Support | AWS Console |

### Emergency Procedures

#### Service Outage

1. **Immediate Actions** (0-15 minutes)
   - Acknowledge incident in PagerDuty
   - Post in #incidents Slack channel
   - Check AWS service status
   - Verify system health

2. **Investigation** (15-30 minutes)
   - Check CloudWatch metrics
   - Review recent deployments
   - Analyze error logs
   - Test individual components

3. **Resolution** (30-60 minutes)
   - Implement fix or workaround
   - Monitor system recovery
   - Validate functionality
   - Communicate status updates

4. **Post-Incident** (1-24 hours)
   - Conduct post-mortem
   - Document lessons learned
   - Implement preventive measures
   - Update runbook

#### Data Loss

1. **Immediate Actions**
   - Stop all write operations
   - Assess scope of data loss
   - Notify stakeholders
   - Begin forensic investigation

2. **Recovery**
   - Restore from backups
   - Validate data integrity
   - Test system functionality
   - Resume normal operations

3. **Communication**
   - Notify affected customers
   - Provide status updates
   - Document incident timeline
   - Conduct post-mortem

#### Security Breach

1. **Immediate Actions**
   - Contain the breach
   - Preserve evidence
   - Notify security team
   - Activate incident response

2. **Investigation**
   - Forensic analysis
   - Identify attack vector
   - Assess data exposure
   - Document findings

3. **Recovery**
   - Patch vulnerabilities
   - Reset compromised credentials
   - Implement additional security measures
   - Monitor for continued threats

4. **Communication**
   - Notify legal team
   - Prepare customer notifications
   - Coordinate with authorities if required
   - Document incident response

### Emergency Runbooks

#### Runbook: Complete Service Restart

```bash
#!/bin/bash
# scripts/emergency_restart.sh

echo "=== Emergency Service Restart ==="

# 1. Stop all Lambda functions
echo "1. Stopping Lambda functions..."
aws lambda update-function-configuration \
  --function-name SyncHandler \
  --environment Variables={ENABLED=false}

# 2. Clear caches
echo "2. Clearing caches..."
aws dynamodb scan \
  --table-name AuraStream-SentimentCache \
  --projection-expression "text_hash" \
  --query "Items[*].text_hash.S" \
  --output text | xargs -I {} aws dynamodb delete-item \
  --table-name AuraStream-SentimentCache \
  --key "{\"text_hash\":{\"S\":\"{}\"}}"

# 3. Restart Lambda functions
echo "3. Restarting Lambda functions..."
aws lambda update-function-configuration \
  --function-name SyncHandler \
  --environment Variables={ENABLED=true}

# 4. Validate service
echo "4. Validating service..."
sleep 30
curl -X GET "https://api.aurastream.com/v1/health"

echo "=== Emergency Restart Complete ==="
```

#### Runbook: Failover to DR Region

```bash
#!/bin/bash
# scripts/emergency_failover.sh

echo "=== Emergency Failover to DR Region ==="

# 1. Update health checks
echo "1. Updating health checks..."
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://failover.json

# 2. Activate DR resources
echo "2. Activating DR resources..."
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name aurastream-dr \
  --region us-west-2 \
  --capabilities CAPABILITY_IAM

# 3. Restore data
echo "3. Restoring data..."
aws dynamodb restore-table-from-backup \
  --target-table-name AuraStream-SentimentCache \
  --backup-arn $BACKUP_ARN

# 4. Validate DR environment
echo "4. Validating DR environment..."
curl -X GET "https://dr-api.aurastream.com/v1/health"

echo "=== Emergency Failover Complete ==="
```

---

This operations runbook provides comprehensive procedures for maintaining, monitoring, and troubleshooting the AuraStream platform. It serves as the primary reference for operations teams and should be regularly updated based on system changes and lessons learned from incidents.
