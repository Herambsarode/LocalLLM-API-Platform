# Architecture

## Overview

The AI API Platform is built using Clean Architecture principles with FastAPI, SQLAlchemy, and Pydantic v2.

## Project Structure

```
app/
├── main.py                    # FastAPI application entry point
├── core/                      # Core configuration and utilities
│   ├── config.py             # Settings management (Pydantic Settings)
│   ├── database.py           # Database engine and session management
│   ├── security.py           # Encryption, hashing, JWT utilities
│   ├── dependencies.py       # FastAPI dependency injection
│   └── events.py             # Startup/shutdown event handlers
├── api/                       # API layer
│   ├── routers/              # Route handlers
│   │   ├── chat.py          # POST /v1/chat/completions
│   │   ├── completions.py   # POST /v1/completions
│   │   ├── models.py        # GET /v1/models
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── admin.py         # Admin management endpoints
│   │   ├── dashboard.py     # Dashboard/analytics endpoints
│   │   └── monitoring.py    # Health/status/metrics endpoints
│   └── middleware/           # ASGI middleware
│       ├── auth.py          # API key authentication
│       ├── rate_limit.py    # Rate limiting
│       └── logging.py       # Request logging
├── database/                  # Data access layer
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py          # User model
│   │   ├── api_key.py       # APIKey model
│   │   ├── usage.py         # UsageRecord model
│   │   ├── quota.py         # Quota model
│   │   ├── model.py         # Model registry
│   │   └── billing.py       # Billing models
│   └── session.py           # Session exports
├── schemas/                   # Pydantic v2 schemas
│   ├── user.py              # User request/response schemas
│   ├── api_key.py           # API key schemas
│   ├── usage.py             # Usage schemas
│   ├── quota.py             # Quota schemas
│   ├── model.py             # Model schemas
│   ├── chat.py              # Chat completion schemas
│   ├── completions.py       # Text completion schemas
│   └── dashboard.py         # Dashboard response schemas
├── services/                  # Business logic layer
│   ├── auth_service.py      # Authentication logic
│   ├── user_service.py      # User CRUD operations
│   ├── api_key_service.py   # API key management
│   ├── usage_service.py     # Usage tracking and analytics
│   ├── quota_service.py     # Quota enforcement
│   ├── model_service.py     # Model registry management
│   ├── lm_studio_service.py # LM Studio API integration
│   └── monitoring_service.py # System monitoring
├── utils/                    # Utility functions
│   ├── hashing.py           # Hashing utilities
│   ├── key_generator.py     # API key generation
│   └── metrics.py           # Prometheus metrics
└── tests/                    # Test suite
    ├── conftest.py          # Test fixtures
    ├── test_auth.py         # Auth tests
    ├── test_api_keys.py     # API key tests
    ├── test_chat.py         # Chat tests
    ├── test_completions.py  # Completions tests
    └── test_rate_limit.py   # Rate limiter tests
```

## Architecture Layers

### 1. API Layer (`app/api/`)
- FastAPI routers handle HTTP requests/responses
- Middleware handles cross-cutting concerns:
  - Authentication (API Key validation)
  - Rate Limiting
  - Request Logging
- Pydantic schemas validate input/output

### 2. Service Layer (`app/services/`)
- Contains all business logic
- Services are stateless and receive DB sessions via dependency injection
- `LMStudioService` handles proxying to LM Studio

### 3. Data Layer (`app/database/`)
- SQLAlchemy ORM models define database schema
- Async session management with asyncpg
- Repositories pattern via service classes

### 4. Core Layer (`app/core/`)
- Configuration via Pydantic Settings (`.env` file)
- Security utilities (hashing, JWT, API key generation)
- Database engine and session factory
- FastAPI dependency injection

## Request Flow

```
Client Request
    │
    ▼
FastAPI Application
    │
    ├── CORS Middleware
    ├── APIKeyAuth Middleware ───► Validates Bearer token
    ├── RateLimit Middleware ───► Checks rate limits
    ├── Logging Middleware ─────► Logs request/response
    │
    ▼
Router Handler
    │
    ├── QuotaService ───────────► Checks usage limits
    ├── LMStudioService ────────► Proxies to local model
    │       │
    │       ▼
    │   LM Studio (localhost:1234)
    │
    ├── UsageService ───────────► Records usage stats
    │
    ▼
Client Response
```

## Middleware Pipeline

1. **CORSMiddleware** - Handles CORS headers
2. **APIKeyAuthMiddleware** - Validates Bearer token, sets `request.state.user_id` and `request.state.api_key_id`
3. **RateLimitMiddleware** - Per-key rate limiting, returns 429 if exceeded
4. **LoggingMiddleware** - Logs method, path, status, duration

## Data Flow

1. Request arrives with `Authorization: Bearer sk_live_...`
2. Auth middleware hashes the key and looks up in database
3. If valid, sets `user_id` and `api_key_id` in request state
4. Rate limiter checks per-key usage
5. Router handler:
   a. Checks quota (daily/monthly limits)
   b. Forwards request to LM Studio
   c. Records usage in database
6. Returns OpenAI-compatible response

## Design Patterns

- **Dependency Injection**: Services receive DB sessions via FastAPI's `Depends()`
- **Repository Pattern**: Services abstract database operations
- **Middleware Pattern**: Cross-cutting concerns in middleware pipeline
- **Factory Pattern**: Session factory for database connections
- **Singleton Pattern**: Settings and rate limiter instances
- **Async/Await**: End-to-end async operations for scalability
