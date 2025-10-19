"""Application constants."""

# API Configuration
API_VERSION = "v1"
MAX_TEXT_LENGTH_SYNC = 5000
MAX_TEXT_LENGTH_ASYNC = 1048576  # 1MB

# Sentiment Analysis
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar"]

SENTIMENT_TYPES = ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"]

# Cache Configuration
CACHE_TTL_DEFAULT = 86400  # 24 hours
CACHE_TTL_SHORT = 3600  # 1 hour
CACHE_TTL_LONG = 604800  # 7 days

# Performance Limits
MAX_CONCURRENT_REQUESTS = 1000
MAX_BATCH_SIZE = 100
DEFAULT_TIMEOUT = 30

# Error Codes
ERROR_CODES = {
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "RATE_LIMIT_EXCEEDED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# AWS Service Limits
COMPREHEND_MAX_CHARS = 5000
COMPREHEND_BATCH_MAX_ITEMS = 25
DYNAMODB_MAX_ITEM_SIZE = 400000  # 400KB

# Monitoring
METRICS_NAMESPACE = "AuraStream"
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Security
PII_ENTITIES = [
    "NAME",
    "EMAIL",
    "PHONE",
    "SSN",
    "CREDIT_DEBIT_NUMBER",
    "ADDRESS",
    "DATE_TIME",
    "PASSPORT_NUMBER",
    "DRIVER_ID",
]

# Rate Limiting
RATE_LIMITS = {
    "free": {"requests_per_minute": 60, "requests_per_hour": 1000},
    "basic": {"requests_per_minute": 600, "requests_per_hour": 10000},
    "premium": {"requests_per_minute": 6000, "requests_per_hour": 100000},
}
