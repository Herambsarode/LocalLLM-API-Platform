# API Reference

## OpenAI Compatible Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint. Supports streaming.

**Request:**
```json
{
  "model": "deepseek-coder-v2",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "deepseek-coder-v2",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

### POST /v1/completions

OpenAI-compatible text completions endpoint.

**Request:**
```json
{
  "model": "deepseek-coder-v2",
  "prompt": "Once upon a time",
  "max_tokens": 100,
  "temperature": 0.8
}
```

### GET /v1/models

List available models.

### GET /v1/models/{model_id}

Retrieve a specific model.

---

## Authentication Endpoints

### POST /auth/register

Create a new user account.

| Field | Type | Required |
|-------|------|----------|
| name | string | Yes |
| email | string | Yes |
| password | string | Yes (min 8 chars) |
| role | string | No (default: "user") |

### POST /auth/login

Login and receive JWT token.

| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| password | string | Yes |

### GET /auth/me

Get current user info (requires JWT).

### POST /auth/api-keys

Create a new API key.

| Field | Type | Required |
|-------|------|----------|
| name | string | No |
| expires_at | datetime | No |

**Response includes `raw_key` - show once only.**

### GET /auth/api-keys

List user's API keys.

### PUT /auth/api-keys/{id}

Update API key (name, is_active, expires_at).

### DELETE /auth/api-keys/{id}

Delete an API key.

### POST /auth/api-keys/{id}/rotate

Rotate API key (generates new key, invalidates old).

---

## Admin Endpoints (Requires JWT + Admin Role)

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users | List all users |
| POST | /admin/users | Create user |
| GET | /admin/users/{id} | Get user |
| PUT | /admin/users/{id} | Update user |
| DELETE | /admin/users/{id} | Delete user |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users/{id}/api-keys | List user's keys |
| PUT | /admin/api-keys/{id} | Update any key |
| DELETE | /admin/api-keys/{id} | Delete any key |

### Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/models | List all models |
| POST | /admin/models | Add model |
| PUT | /admin/models/{id} | Update model |
| DELETE | /admin/models/{id} | Delete model |

### Quotas

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users/{id}/quota | Get user quota |
| PUT | /admin/users/{id}/quota | Update user quota |

### Usage

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users/{id}/usage | Get user usage summary |

---

## Dashboard Endpoints (Requires JWT + Admin Role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dashboard/analytics/daily | Daily request analytics |
| GET | /dashboard/analytics/monthly | Monthly request analytics |
| GET | /dashboard/analytics/models | Model usage breakdown |
| GET | /dashboard/analytics/my-usage | Current user's usage |
| GET | /dashboard/system | System status (CPU, RAM, GPU) |
| GET | /dashboard/gpu | GPU status |
| GET | /dashboard/metrics | Summary metrics |

---

## Monitoring Endpoints (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check (DB + LM Studio) |
| GET | /status | System status |
| GET | /metrics | Prometheus metrics |

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": {
    "message": "Invalid or expired API key",
    "type": "auth_error"
  }
}
```

### 429 Too Many Requests
```json
{
  "error": {
    "message": "Rate limit exceeded. Please wait before retrying.",
    "type": "rate_limit_error"
  }
}
```

### 502 Bad Gateway
```json
{
  "detail": "LM Studio error: ..."
}
```

## SDK Compatibility

This API is fully compatible with the OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk_live_your_key_here"
)

# Chat completions
response = client.chat.completions.create(
    model="deepseek-coder-v2",
    messages=[{"role": "user", "content": "Hello"}]
)

# Streaming
stream = client.chat.completions.create(
    model="deepseek-coder-v2",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")

# List models
models = client.models.list()
```
