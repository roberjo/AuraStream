# AuraStream: LLM Guide & Implementation Plan

## Table of Contents
1. [Project Overview for LLMs](#project-overview-for-llms)
2. [Current System Architecture](#current-system-architecture)
3. [Implementation Plan](#implementation-plan)
4. [Technical Specifications](#technical-specifications)
5. [Development Workflow](#development-workflow)

---

## Project Overview for LLMs

### What is AuraStream?
AuraStream is a **serverless sentiment analysis platform** built on AWS that provides a unified API for analyzing customer feedback data. It serves two primary use cases:

- **Real-time Analysis**: Low-latency sentiment analysis for chat/live agents (≤1 second response time)
- **Batch Processing**: High-volume analysis for product teams doing overnight data processing

### Core Value Proposition
- **Single API Endpoint**: Unified interface for both real-time and batch sentiment analysis
- **Cost-Optimized**: Serverless architecture with pay-per-use pricing
- **Highly Scalable**: Auto-scaling AWS services handle variable workloads
- **Enterprise-Ready**: Built with security, compliance, and operational excellence in mind

### Technology Stack
- **Platform**: AWS Serverless (Lambda, API Gateway, Step Functions, S3, DynamoDB, SQS)
- **Runtime**: Python 3.9+
- **ML Service**: Amazon Comprehend (managed sentiment analysis)
- **Infrastructure**: AWS SAM or Terraform
- **Monitoring**: AWS CloudWatch, X-Ray (planned)

---

## Current System Architecture

### Dual-Path Design

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (v1)                        │
│              (Authentication, Rate Limiting)                │
└────────────┬──────────────────────────┬────────────────────┘
             │                          │
    ┌────────▼────────┐        ┌───────▼────────┐
    │  Sync Lambda    │        │  Async Lambda  │
    │  (Real-time)    │        │  (Job Init)    │
    └────────┬────────┘        └───────┬────────┘
             │                          │
    ┌────────▼────────┐                │
    │   Comprehend    │                ▼
    │ DetectSentiment │           S3 Bucket
    └────────┬────────┘         (Document Store)
             │                          │
    ┌────────▼────────┐        ┌───────▼────────┐
    │  DLQ (Failures) │        │ Step Functions │
    │                 │        │  (Orchestrate) │
    └─────────────────┘        └───────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │   Comprehend    │
                               │   Batch API     │
                               └───────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │    DynamoDB     │
                               │  (Job Results)  │
                               └─────────────────┘
```

### API Endpoints

#### Synchronous Analysis
- **Endpoint**: `POST /v1/analyze/sync`
- **Purpose**: Real-time sentiment analysis
- **Input**: `{"text": "I love this product!"}`
- **Output**: `{"sentiment": "POSITIVE", "score": 0.925, "language_code": "en"}`

#### Asynchronous Analysis
- **Endpoint**: `POST /v1/analyze/async`
- **Purpose**: Initiate batch processing job
- **Input**: `{"text": "Large document...", "source_id": "batch_001"}`
- **Output**: `{"job_id": "uuid", "message": "Analysis initiated"}`

#### Status Check
- **Endpoint**: `GET /v1/status/{job_id}`
- **Purpose**: Retrieve batch job results
- **Output**: `{"status": "COMPLETED", "result": {...}}`

---

## Implementation Plan

### Phase 1: Production-Readiness Hardening (Weeks 1-4)

#### 1.1 Caching Implementation
**Priority**: High | **Effort**: 3 days

**Objective**: Reduce Comprehend API costs by 40-60% through intelligent caching

**Implementation**:
```python
# Cache Strategy
- Cache Key: SHA256 hash of normalized text
- TTL: 24 hours (configurable)
- Storage: DynamoDB with TTL attribute
- Cache Hit Response: < 100ms
```

**Files to Create/Modify**:
- `src/cache/sentiment_cache.py` - Cache management logic
- `src/utils/text_normalizer.py` - Text normalization for consistent hashing
- `template.yaml` - Add DynamoDB cache table
- `src/handlers/sync_handler.py` - Integrate cache check

**Testing**:
- Unit tests for cache hit/miss scenarios
- Load testing with repeated queries
- Cost analysis before/after implementation

#### 1.2 Enhanced Error Handling
**Priority**: High | **Effort**: 4 days

**Objective**: Implement robust error handling with retry logic and circuit breaker

**Implementation**:
```python
# Error Handling Strategy
- Retry Logic: 3 attempts with exponential backoff (1s, 2s, 4s)
- Circuit Breaker: Open after 5 consecutive failures
- Error Classification: Validation, Service, Quota, System errors
- DLQ Integration: Failed messages after all retries
```

**Files to Create/Modify**:
- `src/error_handling/retry_handler.py` - Retry logic with backoff
- `src/error_handling/circuit_breaker.py` - Circuit breaker implementation
- `src/error_handling/error_classifier.py` - Error type classification
- `src/handlers/base_handler.py` - Common error handling patterns

**Error Response Format**:
```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "API quota exceeded. Retry after 2024-01-15T10:30:00Z",
    "retry_after": 3600,
    "request_id": "req_123456"
  }
}
```

#### 1.3 PII Protection
**Priority**: High | **Effort**: 5 days

**Objective**: Detect and protect PII in customer feedback data

**Implementation**:
```python
# PII Protection Pipeline
Input Text → PII Detection (Comprehend) → Redaction/Masking → Sentiment Analysis
```

**Files to Create/Modify**:
- `src/pii/pii_detector.py` - PII detection using Comprehend
- `src/pii/pii_redactor.py` - PII redaction/masking logic
- `src/handlers/sync_handler.py` - Integrate PII pipeline
- `src/handlers/async_handler.py` - Integrate PII pipeline

**PII Types to Detect**:
- Names, Email addresses, Phone numbers
- Credit card numbers, SSNs
- IP addresses, MAC addresses
- Custom patterns (customer IDs, order numbers)

**Redaction Strategy**:
```python
# Example redaction
Original: "John Smith (john@example.com) loves the product"
Redacted: "[NAME] ([EMAIL]) loves the product"
```

### Phase 2: Complete Documentation (Weeks 2-3)

#### 2.1 System Design Document Completion
**Priority**: Medium | **Effort**: 2 days

**Missing Sections to Complete**:

**Data Model (Complete)**:
```json
{
  "sync_request": {
    "text": "string (required, max 5000 chars)",
    "options": {
      "language_code": "string (optional, auto-detect if not provided)",
      "include_confidence": "boolean (default: true)"
    }
  },
  "async_request": {
    "text": "string (required, max 1MB)",
    "source_id": "string (optional, for tracking)",
    "options": {
      "language_code": "string (optional)",
      "callback_url": "string (optional, webhook endpoint)"
    }
  },
  "sync_response": {
    "sentiment": "POSITIVE|NEGATIVE|NEUTRAL|MIXED",
    "score": "float (0.0-1.0)",
    "language_code": "string",
    "confidence": "float (0.0-1.0)",
    "pii_detected": "boolean",
    "processing_time_ms": "integer"
  },
  "async_response": {
    "job_id": "string (UUID)",
    "status": "PENDING|PROCESSING|COMPLETED|FAILED",
    "estimated_completion": "ISO 8601 timestamp",
    "result": "object (when status=COMPLETED)"
  }
}
```

**Security & Compliance (Enhanced)**:
- Data encryption at rest (S3, DynamoDB)
- Data encryption in transit (TLS 1.2+)
- API Gateway WAF rules
- CloudTrail audit logging
- GDPR/CCPA compliance measures

#### 2.2 API Specification Completion
**Priority**: Medium | **Effort**: 2 days

**Missing Sections**:

**Complete Status Response Examples**:
```json
// Job Pending
{
  "status": "PENDING",
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "created_at": "2024-01-15T10:00:00Z",
  "estimated_completion": "2024-01-15T10:05:00Z"
}

// Job Completed
{
  "status": "COMPLETED",
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "result": {
    "sentiment": "POSITIVE",
    "score": 0.89,
    "language_code": "en",
    "processing_time_ms": 2340
  },
  "completed_at": "2024-01-15T10:04:30Z"
}

// Job Failed
{
  "status": "FAILED",
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Document too large for processing"
  },
  "failed_at": "2024-01-15T10:02:15Z"
}
```

**Error Response Specifications**:
```json
// 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Text field is required and cannot be empty",
    "field": "text"
  }
}

// 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds",
    "retry_after": 60
  }
}

// 503 Service Unavailable
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Sentiment analysis service temporarily unavailable",
    "retry_after": 30
  }
}
```

### Phase 3: Operational Maturity (Weeks 3-6)

#### 3.1 Monitoring & Observability
**Priority**: High | **Effort**: 5 days

**CloudWatch Dashboards**:

**Synchronous Health Dashboard**:
- P99 Latency (target: < 1000ms)
- Error Rate (target: < 1%)
- Cache Hit Rate (target: > 60%)
- Cold Start Duration
- Comprehend API Success Rate

**Asynchronous Health Dashboard**:
- Step Function Success Rate
- SQS Queue Depth
- DynamoDB Read/Write Capacity
- Job Processing Time Distribution
- Failed Job Analysis

**Custom Metrics**:
```python
# Business Metrics
- Sentiment Distribution (Positive/Negative/Neutral ratios)
- Average Confidence Scores
- Cost per Analysis
- API Usage by Customer
- PII Detection Rate
```

**Files to Create**:
- `src/monitoring/metrics.py` - Custom CloudWatch metrics
- `src/monitoring/alerts.py` - Alert configuration
- `cloudformation/monitoring.yaml` - CloudWatch dashboards
- `scripts/setup_monitoring.py` - Monitoring setup script

#### 3.2 Distributed Tracing
**Priority**: Medium | **Effort**: 3 days

**Implementation**:
- Enable AWS X-Ray for all Lambda functions
- Add custom segments for external API calls
- Implement trace context propagation
- Create X-Ray service map

**Files to Create/Modify**:
- `src/tracing/xray_config.py` - X-Ray configuration
- `src/handlers/*.py` - Add tracing decorators
- `template.yaml` - Enable X-Ray for Lambda functions

#### 3.3 Testing Strategy
**Priority**: High | **Effort**: 6 days

**Unit Testing**:
```python
# Test Coverage Targets
- Core business logic: 90%
- Error handling: 85%
- PII detection: 95%
- Cache logic: 90%
```

**Integration Testing**:
- API Gateway integration tests
- DynamoDB integration tests
- Comprehend API mocking
- Step Functions workflow tests

**Load Testing**:
- Sync endpoint: 1000 RPS sustained
- Async endpoint: 100 jobs/minute
- Cache performance under load
- Error rate under stress

**Files to Create**:
- `tests/unit/` - Unit test suite
- `tests/integration/` - Integration tests
- `tests/load/` - Load testing scripts
- `pytest.ini` - Test configuration
- `scripts/run_tests.py` - Test runner

#### 3.4 CI/CD Pipeline
**Priority**: High | **Effort**: 4 days

**GitHub Actions Workflow**:
```yaml
# .github/workflows/deploy.yml
name: Deploy AuraStream
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
      - name: Run linting
        run: flake8 src/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to AWS
        run: sam deploy --no-confirm-changeset
```

**Files to Create**:
- `.github/workflows/deploy.yml` - CI/CD pipeline
- `.github/workflows/test.yml` - Test pipeline
- `scripts/deploy.sh` - Deployment script
- `requirements-dev.txt` - Development dependencies

### Phase 4: Cost Controls (Weeks 4-5)

#### 4.1 Usage Monitoring & Billing
**Priority**: High | **Effort**: 3 days

**Cost Tracking**:
- Per-customer usage tracking
- Cost allocation by API endpoint
- Monthly cost reports
- Budget alerts and limits

**Implementation**:
```python
# Usage Tracking
- API calls per customer
- Text length processed
- Comprehend API costs
- Infrastructure costs (Lambda, DynamoDB, etc.)
```

**Files to Create**:
- `src/billing/usage_tracker.py` - Usage tracking logic
- `src/billing/cost_calculator.py` - Cost calculation
- `cloudformation/billing.yaml` - Billing infrastructure
- `scripts/generate_billing_report.py` - Monthly reports

#### 4.2 Rate Limiting & Quotas
**Priority**: High | **Effort**: 2 days

**API Gateway Usage Plans**:
- Tier 1: 1000 requests/hour (Free tier)
- Tier 2: 10,000 requests/hour (Basic)
- Tier 3: 100,000 requests/hour (Premium)

**Implementation**:
- API Gateway throttling
- Customer-specific rate limits
- Burst capacity handling
- Quota exceeded responses

**Files to Create/Modify**:
- `template.yaml` - API Gateway usage plans
- `src/rate_limiting/quota_manager.py` - Quota management
- `src/handlers/base_handler.py` - Rate limit checking

---

## Technical Specifications

### Infrastructure Requirements

#### AWS Services Used
- **API Gateway**: REST API with custom authorizers
- **Lambda**: Python 3.9 runtime, 256MB-1GB memory
- **DynamoDB**: On-demand billing with TTL
- **S3**: Document storage with lifecycle policies
- **Step Functions**: Workflow orchestration
- **SQS**: Dead letter queues for failed messages
- **CloudWatch**: Monitoring and alerting
- **X-Ray**: Distributed tracing
- **Comprehend**: Sentiment analysis API

#### Security Requirements
- **Authentication**: API Keys + IAM roles
- **Encryption**: AES-256 at rest, TLS 1.2+ in transit
- **Network**: VPC endpoints for private communication
- **Compliance**: GDPR, CCPA, SOC 2 Type II

#### Performance Requirements
- **Sync Response Time**: P99 < 1000ms
- **Async Job Processing**: < 5 minutes for 1MB documents
- **Availability**: 99.9% uptime SLA
- **Throughput**: 1000 RPS sustained, 5000 RPS burst

### Development Environment Setup

#### Prerequisites
```bash
# Required Tools
- AWS CLI v2
- AWS SAM CLI
- Python 3.9+
- Docker
- Node.js 16+ (for testing tools)
```

#### Local Development
```bash
# Setup
git clone <repository>
cd AuraStream
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Local Testing
sam local start-api
sam local invoke SyncHandler --event events/sync_event.json

# Run Tests
pytest tests/
```

---

## Development Workflow

### Code Organization
```
AuraStream/
├── src/
│   ├── handlers/          # Lambda function handlers
│   ├── cache/            # Caching logic
│   ├── error_handling/   # Error handling utilities
│   ├── pii/              # PII detection and redaction
│   ├── monitoring/       # CloudWatch metrics
│   ├── billing/          # Usage tracking
│   └── utils/            # Common utilities
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── load/             # Load tests
├── cloudformation/       # Infrastructure templates
├── scripts/              # Deployment and utility scripts
├── docs/                 # Documentation
└── events/               # Test events for local development
```

### Git Workflow
1. **Feature Branches**: Create feature branches from `main`
2. **Pull Requests**: All changes via PR with required reviews
3. **Testing**: All PRs must pass tests and linting
4. **Deployment**: Auto-deploy to staging on PR merge
5. **Production**: Manual deployment from `main` branch

### Code Standards
- **Python**: PEP 8 style guide
- **Documentation**: Google-style docstrings
- **Testing**: Minimum 80% code coverage
- **Security**: OWASP security guidelines
- **Performance**: P99 latency requirements

---

## Success Metrics

### Technical Metrics
- **Response Time**: P99 < 1000ms for sync requests
- **Error Rate**: < 1% for all endpoints
- **Cache Hit Rate**: > 60% for repeated queries
- **Cost Efficiency**: < $0.01 per analysis
- **Availability**: 99.9% uptime

### Business Metrics
- **Customer Satisfaction**: > 4.5/5 rating
- **API Adoption**: 100+ active customers
- **Processing Volume**: 1M+ analyses/month
- **Cost Savings**: 40% reduction through caching

### Operational Metrics
- **Deployment Frequency**: Daily deployments
- **Lead Time**: < 1 hour from commit to production
- **MTTR**: < 30 minutes for critical issues
- **Test Coverage**: > 80% code coverage

---

This implementation plan provides a comprehensive roadmap for transforming AuraStream from a proof-of-concept to a production-ready, enterprise-grade sentiment analysis platform. Each phase builds upon the previous one, ensuring a systematic approach to improvement while maintaining system stability.
