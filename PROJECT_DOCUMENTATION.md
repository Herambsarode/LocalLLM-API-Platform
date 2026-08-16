# AI API Platform — Project Documentation

## 1. Project Overview

AI API Platform is a self-hosted, OpenAI-compatible API gateway for large language models served through LM Studio. It provides a familiar API surface for applications that already use OpenAI-style chat and completion clients while keeping model inference on infrastructure controlled by the operator.

The platform combines local model inference with authentication, user administration, rate limiting, quota enforcement, usage analytics, billing-ready records, health monitoring, and a lightweight web dashboard.

**Developed by Heramb Sarode and Shruti Bhavsar.**

## 2. Goals

The project is designed to:

- expose locally hosted LM Studio models through OpenAI-compatible endpoints;
- provide secure API-key and access-token authentication;
- support multiple users, roles, models, and API keys;
- enforce request and token quotas;
- record usage, latency, and operational metrics;
- provide administrative and monitoring endpoints;
- support local, Docker-based, and ngrok-assisted development workflows.

## 3. Why This Project Is Important

Modern applications increasingly depend on large language models, but directly connecting every application to a third-party cloud model can create concerns around privacy, recurring cost, internet dependency, vendor lock-in, and operational control. AI API Platform addresses these concerns by providing a controlled API layer between client applications and locally hosted models.

### Data privacy and ownership

Prompts, source code, business documents, and model responses can remain on infrastructure controlled by the operator. This is valuable for organizations handling confidential, academic, personal, or internal information that should not automatically be sent to an external model provider.

### Lower and more predictable operating cost

Locally hosted inference can reduce per-request API charges for suitable workloads. Hardware and electricity still have costs, but the platform gives operators direct control over model selection, resource usage, request limits, and capacity planning.

### Reduced vendor lock-in

The OpenAI-compatible interface allows many existing tools and SDK integrations to work with locally served models. Applications can change the model behind the platform without requiring a complete client-side integration rewrite.

### Centralized access control

LM Studio alone focuses on model serving. This project adds an application layer for users, roles, API keys, quotas, rate limits, usage records, and administrative controls. That makes a local model more practical for controlled multi-user access.

### Responsible resource sharing

Local AI hardware is limited and inference can be expensive. The queue, concurrency controls, rate limits, and token quotas help prevent a single client from exhausting the available GPU, memory, or processing capacity.

### Observability and accountability

Health checks, metrics, usage tracking, latency records, and dashboard data help operators understand whether the platform is available, how it is being used, and where performance problems occur. These capabilities are important when moving from a personal experiment to a shared service.

### Internet-independent local operation

The core API and model server can operate on a local network without exposing the service publicly. ngrok is optional and is intended for controlled development demonstrations or temporary remote access—not as a requirement for local inference.

### Learning and research value

The project demonstrates how API design, authentication, databases, asynchronous processing, LLM integration, monitoring, security, and deployment fit together in a complete AI system. It can therefore serve as a practical reference for students, researchers, and developers learning production-oriented AI engineering.

### Foundation for future development

The modular service, schema, router, and database structure provides a base for additional models, organization-level accounts, payment integration, distributed queues, advanced analytics, model routing, audit logs, and production deployment controls.

### Practical impact

In short, the platform turns a locally running model into a manageable service that applications and multiple users can access through a familiar API. Its importance is not only model inference; it is the security, governance, compatibility, and operational layer built around that inference.

## 4. Core Features

### OpenAI-compatible inference

- Chat Completions API
- Text Completions API
- Model discovery endpoint
- Compatibility with the OpenAI Python SDK and other OpenAI-compatible clients
- Configurable inference queue and concurrency controls

### Authentication and authorization

- User registration and login workflows
- JWT-based access tokens
- `sk_live_` application API keys
- API-key hashing before database storage
- Admin and regular-user roles

### Usage controls

- Per-key rate limiting
- Daily and monthly request quotas
- Daily and monthly token quotas
- Usage records by user, key, model, and time
- Prepaid-credit and transaction-ready database models

### Operations

- Health and readiness information
- LM Studio connectivity checks
- Inference queue status
- Prometheus-compatible metrics
- Dashboard APIs and static dashboard UI
- Structured request logging

### Deployment

- Native Python/Uvicorn execution
- Dockerfile and Docker Compose support
- PostgreSQL persistence
- Optional Redis integration
- ngrok support for development and demonstrations

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Validation and settings | Pydantic / pydantic-settings |
| ORM | SQLAlchemy AsyncIO |
| Database | PostgreSQL |
| Migrations | Alembic |
| LLM runtime | LM Studio |
| Authentication | JWT, bcrypt, hashed API keys |
| HTTP client | HTTPX |
| Metrics | Prometheus Client |
| Testing | pytest |
| Optional tunnel | ngrok |
| Containers | Docker / Docker Compose |

## 6. High-Level Architecture

```text
Client Application
        |
        | OpenAI-compatible HTTP request
        v
FastAPI Middleware
  - Request logging
  - API-key authentication
  - Rate limiting
        |
        v
API Routers
  - Authentication
  - Chat and completions
  - Models
  - Admin
  - Dashboard
  - Monitoring
        |
        +--------------------+
        |                    |
        v                    v
Application Services     PostgreSQL
  - Inference queue      - Users
  - LM Studio client     - API keys
  - Quotas               - Models
  - Usage tracking       - Usage
  - Monitoring           - Billing records
        |
        v
LM Studio Local Server
```

The middleware authenticates and limits incoming requests before the routers dispatch work to the service layer. Inference requests pass through a bounded queue and are forwarded to LM Studio. Usage and quota information is maintained in PostgreSQL.

## 7. Request Lifecycle

1. A client sends an HTTP request with an application API key or access token.
2. Logging middleware assigns and records request context.
3. Authentication middleware validates the supplied credentials.
4. Rate-limiting logic checks the permitted request window.
5. The router validates the request body with a Pydantic schema.
6. Quota services verify request and token allowances.
7. The inference queue controls concurrent model work.
8. The LM Studio service forwards the request to the local model server.
9. The response is converted to an OpenAI-compatible schema.
10. Usage, token, status, and latency data are recorded.

## 8. Repository Structure

```text
API_DEMO/
|-- alembic/                    # Database migration environment
|   `-- versions/               # Versioned schema migrations
|-- app/
|   |-- api/
|   |   |-- middleware/         # Authentication, logging, rate limiting
|   |   `-- routers/            # HTTP endpoint groups
|   |-- core/                   # Configuration, database and lifecycle logic
|   |-- database/
|   |   `-- models/             # SQLAlchemy database models
|   |-- schemas/                # Pydantic request/response schemas
|   |-- services/               # Business and integration services
|   |-- static/                 # Dashboard frontend
|   |-- tests/                  # Automated tests
|   |-- utils/                  # Hashing, key generation and metrics
|   `-- main.py                 # FastAPI application entry point
|-- Docs/                       # Detailed technical reference documents
|-- scripts/                    # Maintenance scripts
|-- .env.example                # Public configuration template
|-- docker-compose.yml          # API, PostgreSQL and Redis services
|-- Dockerfile                  # API container image
|-- requirements.txt            # Python dependencies
|-- SETUP.md                    # Complete local and ngrok setup guide
`-- README.md                   # Repository landing page
```

## 9. Main API Groups

The exact request and response schemas are available through Swagger at `/docs` and in [API_REFERENCE.md](Docs/API_REFERENCE.md).

| Area | Typical path | Purpose |
|---|---|---|
| Health | `/health` | Application, database and LM Studio status |
| Models | `/v1/models` | List available models |
| Chat | `/v1/chat/completions` | OpenAI-compatible chat inference |
| Completions | `/v1/completions` | OpenAI-compatible text completion |
| Authentication | `/auth/*` | Registration, login and access tokens |
| Administration | `/admin/*` | Users, keys, models, quotas and administration |
| Dashboard | `/dashboard/*` | Usage and operational dashboard data |
| Metrics | `/metrics` | Prometheus metrics when enabled |

Endpoint availability and authorization requirements should be verified in the generated Swagger specification for the running version.

## 10. Quick Start

For full prerequisites and ngrok instructions, see [SETUP.md](SETUP.md).

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
# Update .env with secure local values.

alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 11. OpenAI SDK Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="sk_live_your_generated_api_key",
)

response = client.chat.completions.create(
    model="your-loaded-model-id",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain asynchronous Python."},
    ],
)

print(response.choices[0].message.content)
```

## 12. cURL Example

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_your_generated_api_key" \
  -d '{
    "model": "your-loaded-model-id",
    "messages": [
      {"role": "user", "content": "Hello from the API"}
    ]
  }'
```

## 13. Configuration

Configuration is loaded from environment variables and `.env`. Important settings include:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing secret; use a long random value |
| `DATABASE_URL` | Async PostgreSQL connection URL |
| `DATABASE_SYNC_URL` | Synchronous PostgreSQL URL for migrations |
| `LM_STUDIO_BASE_URL` | LM Studio OpenAI-compatible base URL |
| `LM_STUDIO_READ_TIMEOUT` | Inference response timeout; `0` permits long generations |
| `INFERENCE_CONCURRENCY` | Concurrent inference jobs |
| `INFERENCE_QUEUE_SIZE` | Maximum queued inference requests |
| `RATE_LIMIT_REQUESTS` | Requests allowed in one rate-limit window |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window duration |
| `DEFAULT_DAILY_REQUESTS` | Default daily request quota |
| `DEFAULT_MONTHLY_REQUESTS` | Default monthly request quota |
| `CORS_ORIGINS` | Allowed browser origins |
| `DEFAULT_ADMIN_EMAIL` | Initial administrator email |
| `DEFAULT_ADMIN_PASSWORD` | Initial administrator password |
| `METRICS_ENABLED` | Enables or disables metrics |

Use [.env.example](.env.example) as the configuration template. Never place real credentials in `.env.example`.

## 14. Docker Deployment

Create `.env` first and replace all example credentials. Then run:

```powershell
docker compose up --build
```

The default compose configuration starts:

- the API on port `8000`;
- PostgreSQL on port `5432`;
- Redis on port `6379`.

LM Studio normally runs on the host. Container-to-host networking may require a platform-specific LM Studio URL instead of `localhost`.

## 15. ngrok Development Access

After the local API is healthy:

```powershell
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
ngrok http 8000
```

Use the generated HTTPS URL as the public base URL. The ngrok authtoken authenticates the ngrok agent; it is not an application API key and must never be committed.

See [SETUP.md](SETUP.md) for installation, credential safety, fixed-domain guidance, and error resolution.

## 16. Security Guidance

- Never commit `.env`, `ngrok.yml`, `API_INFO.txt`, logs, database dumps, or real API keys.
- Rotate a credential immediately if it is exposed, even if the file is later deleted.
- Use a unique random `SECRET_KEY` in every environment.
- Replace the default administrator password before starting the service.
- Restrict `CORS_ORIGINS` in production.
- Place the API behind TLS and a trusted reverse proxy for production use.
- Restrict public access to administration and metrics endpoints.
- Use least-privilege PostgreSQL credentials.
- Review request logs so authorization headers and sensitive payloads are not persisted.
- Keep Python packages, LM Studio, ngrok, PostgreSQL, and the operating system updated.

Additional guidance is available in [SECURITY.md](Docs/SECURITY.md).

## 17. Testing

With the virtual environment active and development dependencies installed:

```powershell
pytest app/tests -q
```

The test suite covers authentication, API keys, chat, completions, rate limiting, and LM Studio service behavior.

Before opening a pull request, run:

```powershell
pytest app/tests -q
git diff --check
```

## 18. Troubleshooting

### API does not start

- Confirm the virtual environment is active.
- Confirm dependencies are installed.
- Check that port `8000` is not already in use.
- Verify PostgreSQL credentials and migration status.

### Database connection fails

- Confirm PostgreSQL is running.
- Verify both database URLs in `.env`.
- Confirm that the database and user exist.
- Run `alembic upgrade head`.

### LM Studio is unavailable

- Start the LM Studio local server.
- Load a compatible model.
- Verify `LM_STUDIO_BASE_URL`.
- Test `http://127.0.0.1:1234/v1/models`.

### Inference is slow or times out

- Reduce the requested output-token limit.
- Use a smaller or more highly quantized model.
- Check GPU and system memory.
- Review queue size and concurrency settings.
- Keep the read timeout at `0` when long local inference is expected.

### ngrok reports `ERR_NGROK_8012`

The tunnel is active but the local API is unavailable. Start Uvicorn and verify `/health` locally.

### ngrok reports `ERR_NGROK_3200`

The public endpoint is offline. Restart the ngrok agent with `ngrok http 8000`.

## 19. Documentation Index

- [Complete Setup Guide](SETUP.md)
- [API Reference](Docs/API_REFERENCE.md)
- [Architecture](Docs/ARCHITECTURE.md)
- [Database Schema](Docs/DATABASE_SCHEMA.md)
- [Deployment Guide](Docs/DEPLOYMENT.md)
- [Installation Guide](Docs/INSTALL.md)
- [Security Guide](Docs/SECURITY.md)
- [GitHub Upload Checklist](GITHUB_UPLOAD_CHECKLIST_MR.md)

## 20. Contributors

- **Heramb Sarode**
- **Shruti Bhavsar**

## 21. License

No license is granted unless a `LICENSE` file is added to the repository. Before publishing the project for reuse, the maintainers should select and include an appropriate open-source or proprietary license.
