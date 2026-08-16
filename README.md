# AI API Platform

A production-ready, OpenAI-compatible API platform for self-hosted LLMs via LM Studio.

Developed by [Heramb Sarode](https://github.com/Herambsarode) and [Shruti Bhavsar](https://github.com/Shrutibhavsar3240).

## Why This Project Matters

AI API Platform turns a locally hosted language model into a controlled, reusable service. It helps keep sensitive prompts and responses on operator-managed infrastructure, reduces dependence on a single cloud-model provider, and gives existing OpenAI-compatible applications a familiar integration interface. Authentication, quotas, rate limits, usage tracking, monitoring, and an inference queue make local AI safer and more practical for multiple users. The project is also a complete learning reference for building secure, observable, database-backed AI systems rather than only running a model locally.

## Features

- **OpenAI Compatible** - Drop-in replacement for OpenAI API. Works with existing OpenAI SDKs.
- **Self-Hosted** - Run your own LLM models locally via LM Studio.
- **API Key Authentication** - Secure `sk_live_` prefixed API keys with hashing.
- **User Management** - Multi-user support with admin and user roles.
- **Usage Tracking** - Track requests, tokens, latency per user and API key.
- **Rate Limiting** - Per-key rate limiting with configurable windows.
- **Quota Management** - Daily and monthly limits on requests and tokens.
- **Billing Ready** - Prepaid credit system with transaction history.
- **Multi-Model** - Route requests to multiple local models.
- **Monitoring** - Health checks, GPU status, Prometheus metrics.
- **Dashboard APIs** - Analytics, usage reports, system status.
- **Docker Support** - Easy deployment with Docker Compose.

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- LM Studio with a local model loaded
- Redis (optional)

### Setup

1. Clone the repository and enter the project directory:

   ```bash
   git clone <repository-url>
   cd API_DEMO
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up the environment:

   ```bash
   cp .env.example .env
   # Windows PowerShell: Copy-Item .env.example .env
   ```

   Replace all example secrets, database credentials, and admin credentials in `.env`.

4. Start PostgreSQL, start the LM Studio local server, and run migrations:

   ```bash
   alembic upgrade head
   ```

5. Start the API:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. Open:

   - Dashboard: `http://localhost:8000/dashboard`
   - Swagger API docs: `http://localhost:8000/docs`
   - Health endpoint: `http://localhost:8000/health`

### Docker

```bash
docker compose up --build
```

## API Usage

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://your-server:8000/v1",
    api_key="sk_live_xxxxxxxxxxxxxxxxxxxxx"
)

response = client.chat.completions.create(
    model="deepseek-coder-v2",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Documentation

- [Complete Project Documentation](PROJECT_DOCUMENTATION.md)
- [Complete Setup Guide with ngrok](SETUP.md)
- [Installation Guide](Docs/INSTALL.md)
- [Deployment Guide](Docs/DEPLOYMENT.md)
- [Security Overview](Docs/SECURITY.md)
- [API Reference](Docs/API_REFERENCE.md)
- [Database Schema](Docs/DATABASE_SCHEMA.md)
- [Architecture](Docs/ARCHITECTURE.md)
- [GitHub Upload Checklist (Marathi)](GITHUB_UPLOAD_CHECKLIST_MR.md)

## Security

Never commit `.env`, `ngrok.yml`, `API_INFO.txt`, API keys, access tokens, database dumps, logs, or downloaded executables. Use `.env.example` only as a public configuration template. If a secret was ever committed or shared, revoke it and generate a new one; deleting it from the latest file does not remove it from Git history.

## Contributors

- [Heramb Sarode](https://github.com/Herambsarode)
- [Shruti Bhavsar](https://github.com/Shrutibhavsar3240)
