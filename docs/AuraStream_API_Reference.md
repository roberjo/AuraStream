# AuraStream API Reference

## Table of Contents
1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Base URL and Endpoints](#base-url-and-endpoints)
4. [Synchronous Analysis API](#synchronous-analysis-api)
5. [Asynchronous Analysis API](#asynchronous-analysis-api)
6. [Job Status API](#job-status-api)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [SDKs and Examples](#sdks-and-examples)
10. [Webhooks](#webhooks)

---

## Getting Started

### Overview

AuraStream provides a RESTful API for sentiment analysis of text data. The API supports both real-time synchronous analysis for immediate results and asynchronous batch processing for large documents or bulk operations.

### Key Features

- **Real-time Analysis**: Get sentiment results in under 1 second
- **Batch Processing**: Handle large documents and bulk operations
- **Multi-language Support**: Automatic language detection
- **PII Protection**: Built-in personal information detection and redaction
- **Caching**: Intelligent caching reduces costs and improves performance
- **Webhooks**: Get notified when batch jobs complete

### Quick Start

```bash
# Install the AuraStream CLI
pip install aurastream-cli

# Set your API key
export AURASTREAM_API_KEY="your-api-key-here"

# Analyze text synchronously
aurastream analyze "I love this product!" --sync

# Analyze a document asynchronously
aurastream analyze document.txt --async
```

---

## Authentication

### API Keys

All API requests require authentication using an API key. Include your API key in the request header:

```http
X-API-Key: your-api-key-here
```

### Getting an API Key

1. Sign up for an AuraStream account
2. Navigate to the API Keys section in your dashboard
3. Generate a new API key
4. Store it securely (never commit to version control)

### API Key Security

- **Keep your API key secret**: Never expose it in client-side code
- **Use environment variables**: Store keys in environment variables
- **Rotate regularly**: Generate new keys periodically
- **Monitor usage**: Check your dashboard for unusual activity

---

## Base URL and Endpoints

### Base URL

```
https://api.aurastream.com/v1
```

### Environment-Specific URLs

| Environment | Base URL |
|-------------|----------|
| Production | `https://api.aurastream.com/v1` |
| Staging | `https://staging-api.aurastream.com/v1` |
| Development | `https://dev-api.aurastream.com/v1` |

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze/sync` | Synchronous sentiment analysis |
| `POST` | `/analyze/async` | Asynchronous sentiment analysis |
| `GET` | `/status/{job_id}` | Check job status |
| `DELETE` | `/jobs/{job_id}` | Cancel a job |
| `GET` | `/health` | Health check endpoint |

---

## Synchronous Analysis API

### Endpoint

```http
POST /v1/analyze/sync
```

### Purpose

Perform real-time sentiment analysis on short text inputs. Ideal for chat messages, social media posts, and customer feedback.

### Request

#### Headers

```http
Content-Type: application/json
X-API-Key: your-api-key-here
```

#### Request Body

```json
{
  "text": "I am so happy with this new solution!",
  "options": {
    "language_code": "en",
    "include_confidence": true,
    "include_pii_detection": true
  }
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to analyze (max 5,000 characters) |
| `options` | object | No | Additional analysis options |
| `options.language_code` | string | No | Language code (auto-detect if not provided) |
| `options.include_confidence` | boolean | No | Include confidence scores (default: true) |
| `options.include_pii_detection` | boolean | No | Include PII detection results (default: true) |

#### Supported Languages

| Language | Code | Auto-Detection |
|----------|------|----------------|
| English | `en` | ✅ |
| Spanish | `es` | ✅ |
| French | `fr` | ✅ |
| German | `de` | ✅ |
| Italian | `it` | ✅ |
| Portuguese | `pt` | ✅ |
| Chinese (Simplified) | `zh` | ✅ |
| Japanese | `ja` | ✅ |
| Korean | `ko` | ✅ |
| Arabic | `ar` | ✅ |

### Response

#### Success Response (200 OK)

```json
{
  "sentiment": "POSITIVE",
  "score": 0.925,
  "language_code": "en",
  "confidence": 0.98,
  "pii_detected": false,
  "processing_time_ms": 245,
  "cache_hit": false,
  "request_id": "req_123456789"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `sentiment` | string | Sentiment classification: `POSITIVE`, `NEGATIVE`, `NEUTRAL`, `MIXED` |
| `score` | float | Sentiment score (0.0 to 1.0) |
| `language_code` | string | Detected or specified language code |
| `confidence` | float | Confidence in the sentiment analysis (0.0 to 1.0) |
| `pii_detected` | boolean | Whether PII was detected in the text |
| `processing_time_ms` | integer | Time taken to process the request in milliseconds |
| `cache_hit` | boolean | Whether the result was served from cache |
| `request_id` | string | Unique identifier for the request |

### Example Requests

#### Basic Request

```bash
curl -X POST "https://api.aurastream.com/v1/analyze/sync" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "This product is amazing!"
  }'
```

#### Request with Options

```bash
curl -X POST "https://api.aurastream.com/v1/analyze/sync" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "Este producto es increíble!",
    "options": {
      "language_code": "es",
      "include_confidence": true,
      "include_pii_detection": false
    }
  }'
```

---

## Asynchronous Analysis API

### Endpoint

```http
POST /v1/analyze/async
```

### Purpose

Initiate batch processing for large documents or bulk sentiment analysis. Returns a job ID for tracking progress.

### Request

#### Headers

```http
Content-Type: application/json
X-API-Key: your-api-key-here
```

#### Request Body

```json
{
  "text": "Large document content here...",
  "source_id": "batch_001",
  "options": {
    "language_code": "en",
    "callback_url": "https://your-app.com/webhooks/aurastream",
    "include_confidence": true
  }
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to analyze (max 1MB) |
| `source_id` | string | No | Custom identifier for tracking |
| `options` | object | No | Additional analysis options |
| `options.language_code` | string | No | Language code (auto-detect if not provided) |
| `options.callback_url` | string | No | Webhook URL for completion notification |
| `options.include_confidence` | boolean | No | Include confidence scores (default: true) |

### Response

#### Success Response (202 Accepted)

```json
{
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "PENDING",
  "message": "Analysis initiated. Check status using the job ID.",
  "estimated_completion": "2024-01-15T10:05:00Z",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique identifier for the job |
| `status` | string | Current job status: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` |
| `message` | string | Human-readable status message |
| `estimated_completion` | string | Estimated completion time (ISO 8601) |
| `created_at` | string | Job creation time (ISO 8601) |

### Example Request

```bash
curl -X POST "https://api.aurastream.com/v1/analyze/async" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "This is a large document that needs sentiment analysis...",
    "source_id": "customer_feedback_batch_001",
    "options": {
      "callback_url": "https://myapp.com/webhooks/aurastream",
      "include_confidence": true
    }
  }'
```

---

## Job Status API

### Endpoint

```http
GET /v1/status/{job_id}
```

### Purpose

Check the status and retrieve results of an asynchronous analysis job.

### Request

#### Headers

```http
X-API-Key: your-api-key-here
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string | Yes | Job identifier returned from async analysis |

### Response

#### Job Pending (200 OK)

```json
{
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "PENDING",
  "created_at": "2024-01-15T10:00:00Z",
  "estimated_completion": "2024-01-15T10:05:00Z",
  "progress": {
    "percentage": 0,
    "stage": "queued"
  }
}
```

#### Job Processing (200 OK)

```json
{
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "PROCESSING",
  "created_at": "2024-01-15T10:00:00Z",
  "estimated_completion": "2024-01-15T10:05:00Z",
  "progress": {
    "percentage": 65,
    "stage": "analyzing"
  }
}
```

#### Job Completed (200 OK)

```json
{
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "COMPLETED",
  "created_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:04:30Z",
  "result": {
    "sentiment": "POSITIVE",
    "score": 0.89,
    "language_code": "en",
    "confidence": 0.95,
    "pii_detected": false,
    "processing_time_ms": 2340
  },
  "source_id": "customer_feedback_batch_001"
}
```

#### Job Failed (200 OK)

```json
{
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "FAILED",
  "created_at": "2024-01-15T10:00:00Z",
  "failed_at": "2024-01-15T10:02:15Z",
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Document too large for processing",
    "details": "Maximum document size is 1MB"
  },
  "source_id": "customer_feedback_batch_001"
}
```

### Example Request

```bash
curl -X GET "https://api.aurastream.com/v1/status/b78b0d2d-d55a-49a7-8f5a-39c59520c083" \
  -H "X-API-Key: your-api-key-here"
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `202` | Accepted (async job created) |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Invalid API key |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Job not found |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

### Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details (optional)",
    "request_id": "req_123456789",
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### Common Error Codes

#### Validation Errors (400)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Text field is required and cannot be empty",
    "field": "text",
    "request_id": "req_123456789"
  }
}
```

#### Authentication Errors (401)

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid API key",
    "request_id": "req_123456789"
  }
}
```

#### Rate Limiting (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds",
    "retry_after": 60,
    "request_id": "req_123456789"
  }
}
```

#### Service Errors (500)

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred. Please try again later",
    "request_id": "req_123456789"
  }
}
```

### Error Handling Best Practices

1. **Always check HTTP status codes**
2. **Parse error responses for detailed information**
3. **Implement retry logic for transient errors**
4. **Log error details for debugging**
5. **Handle rate limiting gracefully**

---

## Rate Limiting

### Rate Limits

| Plan | Requests per Minute | Requests per Hour | Burst Limit |
|------|-------------------|------------------|-------------|
| Free | 60 | 1,000 | 10 |
| Basic | 600 | 10,000 | 100 |
| Premium | 6,000 | 100,000 | 1,000 |
| Enterprise | Custom | Custom | Custom |

### Rate Limit Headers

All API responses include rate limit information:

```http
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 599
X-RateLimit-Reset: 1642248000
```

### Handling Rate Limits

When you exceed your rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds",
    "retry_after": 60
  }
}
```

**Best Practices**:
- Implement exponential backoff
- Use the `retry_after` value to determine wait time
- Monitor rate limit headers to avoid hitting limits
- Consider upgrading your plan for higher limits

---

## SDKs and Examples

### Official SDKs

#### Python SDK

```bash
pip install aurastream
```

```python
from aurastream import AuraStreamClient

# Initialize client
client = AuraStreamClient(api_key="your-api-key")

# Synchronous analysis
result = client.analyze_sync("I love this product!")
print(f"Sentiment: {result.sentiment}, Score: {result.score}")

# Asynchronous analysis
job = client.analyze_async("Large document content...")
print(f"Job ID: {job.job_id}")

# Check job status
status = client.get_job_status(job.job_id)
if status.status == "COMPLETED":
    print(f"Result: {status.result}")
```

#### JavaScript SDK

```bash
npm install aurastream
```

```javascript
const AuraStream = require('aurastream');

// Initialize client
const client = new AuraStream({ apiKey: 'your-api-key' });

// Synchronous analysis
client.analyzeSync('I love this product!')
  .then(result => {
    console.log(`Sentiment: ${result.sentiment}, Score: ${result.score}`);
  });

// Asynchronous analysis
client.analyzeAsync('Large document content...')
  .then(job => {
    console.log(`Job ID: ${job.job_id}`);
    return client.getJobStatus(job.job_id);
  })
  .then(status => {
    if (status.status === 'COMPLETED') {
      console.log(`Result: ${status.result}`);
    }
  });
```

### cURL Examples

#### Synchronous Analysis

```bash
curl -X POST "https://api.aurastream.com/v1/analyze/sync" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "This product exceeded my expectations!"
  }'
```

#### Asynchronous Analysis

```bash
curl -X POST "https://api.aurastream.com/v1/analyze/async" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "Large document content...",
    "source_id": "batch_001"
  }'
```

#### Check Job Status

```bash
curl -X GET "https://api.aurastream.com/v1/status/job-id-here" \
  -H "X-API-Key: your-api-key-here"
```

---

## Webhooks

### Overview

Webhooks allow you to receive real-time notifications when asynchronous jobs complete. This eliminates the need to poll the status endpoint.

### Webhook Configuration

Set the `callback_url` in your async analysis request:

```json
{
  "text": "Document to analyze...",
  "options": {
    "callback_url": "https://your-app.com/webhooks/aurastream"
  }
}
```

### Webhook Payload

When a job completes, AuraStream will send a POST request to your callback URL:

```json
{
  "event": "job.completed",
  "job_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083",
  "status": "COMPLETED",
  "result": {
    "sentiment": "POSITIVE",
    "score": 0.89,
    "language_code": "en",
    "confidence": 0.95
  },
  "source_id": "batch_001",
  "completed_at": "2024-01-15T10:04:30Z"
}
```

### Webhook Security

Webhooks include a signature header for verification:

```http
X-AuraStream-Signature: sha256=abc123...
```

Verify the signature to ensure the webhook is from AuraStream:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

### Webhook Retry Policy

- **Retry Attempts**: 3 attempts
- **Retry Interval**: 1 minute, 5 minutes, 15 minutes
- **Timeout**: 30 seconds per attempt
- **Success Response**: HTTP 200-299

### Webhook Best Practices

1. **Respond quickly**: Keep webhook handlers under 30 seconds
2. **Verify signatures**: Always verify webhook authenticity
3. **Handle duplicates**: Implement idempotency for webhook processing
4. **Log webhook events**: Keep audit trail of all webhook calls
5. **Test webhooks**: Use tools like ngrok for local testing

---

This API reference provides comprehensive documentation for integrating with the AuraStream sentiment analysis service. For additional support, visit our [support center](https://support.aurastream.com) or contact our developer team.
