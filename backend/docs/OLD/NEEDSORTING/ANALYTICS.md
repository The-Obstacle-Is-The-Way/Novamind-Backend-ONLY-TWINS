# Analytics & Performance Scaling

This document outlines the architecture, components, and design decisions for the analytics and performance scaling features in the NOVAMIND platform.

## Architecture Overview

The system follows a distributed, asynchronous processing model with these key components:

1. **Analytics API Endpoints** - FastAPI routes for fetching analytics with asynchronous processing
2. **Redis-based Caching** - Distributed caching layer with TTL for high-performance analytics
3. **Distributed Rate Limiting** - Token bucket algorithm based rate limiting for API protection
4. **Background Processing** - Asynchronous task execution for computationally intensive operations

## Components

### 1. Analytics Endpoints

Located in `app/presentation/api/routes/analytics_endpoints.py`, these endpoints provide:

- Patient treatment outcomes analysis
- Practice-wide metrics
- Diagnosis distribution statistics
- Medication effectiveness analysis
- Treatment comparisons
- Patient risk stratification

The endpoints use a combination of:
- Background task processing for computationally intensive operations
- TTL-based caching with different cache durations based on data volatility
- Comprehensive request validation via Pydantic schemas
- HIPAA-compliant error handling that prevents PHI leakage

### 2. Redis Cache Service

Located in `app/infrastructure/cache/redis_cache.py`, this service provides:

- Distributed caching across multiple application instances
- JSON serialization/deserialization of complex objects
- Configurable TTL (Time-To-Live) for different data types
- Graceful fallback when Redis is unavailable
- Error handling for serialization and connection issues

### 3. Distributed Rate Limiter

Located in `app/infrastructure/security/rate_limiter.py`, this service implements:

- Token bucket algorithm with burst capacity
- Distributed rate limiting using Redis as shared memory
- Granular limiting based on IP address, API key, and user ID
- Different limit configurations for various endpoint types:
  - 5 requests/minute for login attempts
  - 30 requests/minute for analytics endpoints
  - 60 requests/minute for patient data endpoints
  - 1000 requests/minute for API-keyed requests
- Standard rate limit headers (X-RateLimit-*)

### 4. Rate Limiting Middleware

Located in `app/presentation/middleware/rate_limiting_middleware.py`, this middleware:

- Automatically applies rate limiting to all incoming requests
- Exempts specific paths (health checks, docs)
- Identifies the appropriate rate limit type based on request path
- Returns standardized 429 Too Many Requests responses when limits are exceeded

## Configuration

The system has several configurable parameters in `.env`:

- `REDIS_URL` - Redis connection string
- `REDIS_PASSWORD` - Optional Redis password
- `REDIS_SSL` - Whether to use SSL for Redis connections
- `REDIS_TIMEOUT` - Connection timeout in seconds
- `ENABLE_ANALYTICS` - Feature flag to enable/disable analytics endpoints

## Testing

Comprehensive test coverage is provided in:

- `tests/unit/infrastructure/cache/test_redis_cache.py`
- `tests/unit/infrastructure/security/test_rate_limiter.py`
- `tests/unit/presentation/middleware/test_rate_limiting_middleware.py`
- `tests/unit/presentation/api/routes/test_analytics_endpoints.py`

Run analytics-specific tests with:

```bash
./scripts/run_analytics_tests.sh
```

## Performance Considerations

- **Async Processing**: All expensive analytics operations are processed asynchronously
- **Caching Strategy**: Different TTLs based on data volatility (5 min for patient data, 15 min for practice-wide metrics)
- **Distributed Design**: All components support multi-instance deployments with Redis as a shared resource
- **Graceful Degradation**: Immediate responses with processing status, with background completion

## Security & Compliance

- **Rate Limiting**: Prevents brute force and DoS attacks
- **HIPAA Compliance**: No PHI in error messages, logs, or cache keys
- **Secure Configuration**: All secrets in environment variables
- **Audit**: Logs rate limiting events for security monitoring

## Future Enhancements

- Integration with a message queue (RabbitMQ/Kafka) for more robust task processing
- Pre-aggregation of common analytics queries in a dedicated analytics database
- Real-time analytics updates via WebSockets for dashboard displays
- Advanced outlier detection and anomaly reporting