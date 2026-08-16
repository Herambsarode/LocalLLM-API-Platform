# Installation Guide

## Prerequisites

- Python 3.12+
- PostgreSQL 16+
- LM Studio (running with local models)
- Redis (optional, for distributed rate limiting)

## Local Installation (Windows/Linux)

### 1. Install PostgreSQL

**Windows:**
Download from https://www.postgresql.org/download/windows/

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

Create database:
```bash
createdb ai_api
```

### 2. Clone and Setup

```bash
git clone <repo-url>
cd AI_API_Platform
python -m venv venv
source venv/bin/activate  # Linux
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_api
DATABASE_SYNC_URL=postgresql://user:password@localhost:5432/ai_api
LM_STUDIO_BASE_URL=http://localhost:1234/v1
SECRET_KEY=generate-a-random-secret-key
```

### 4. Setup LM Studio

1. Download from https://lmstudio.ai
2. Load a GGUF model (e.g., DeepSeek-Coder-V2-Lite-Instruct)
3. Start the local inference server (default: http://localhost:1234)
4. Enable CORS in LM Studio settings

### 5. Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Verify Installation

```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

## Docker Installation

```bash
docker-compose up -d
```

This starts:
- AI API Platform on port 8000
- PostgreSQL on port 5432
- Redis on port 6379

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://...` |
| `LM_STUDIO_BASE_URL` | LM Studio API URL | `http://localhost:1234/v1` |
| `LM_STUDIO_READ_TIMEOUT` | Response timeout in seconds (`0` disables it) | `0` |
| `LM_STUDIO_CONNECT_TIMEOUT` | Connection timeout in seconds | `10` |
| `LM_STUDIO_DEFAULT_MAX_TOKENS` | Default output budget for every model | `4096` |
| `SECRET_KEY` | JWT signing secret | (required) |
| `RATE_LIMIT_REQUESTS` | Max requests per window | 100 |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window | 60 |
| `DEFAULT_DAILY_REQUESTS` | Default daily request quota | 1000 |
| `DEFAULT_MONTHLY_REQUESTS` | Default monthly request quota | 30000 |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `LOG_LEVEL` | Logging level | `INFO` |
