# Deployment Guide

## Architecture

```
Internet
    │
    ▼
Custom Domain (api.example.com)
    │
    ▼
Cloudflare / DNS
    │
    ▼
Reverse Proxy (Nginx/Caddy)
    │
    ▼
FastAPI Gateway (Port 8000)
    │
    ├── PostgreSQL (Port 5432)
    ├── Redis (Port 6379, optional)
    └── LM Studio (Port 1234)
```

## Option 1: Docker Compose (Recommended)

```yaml
# Already configured in docker-compose.yml
docker-compose up -d
```

Configure `.env` with your production settings first.

## Option 2: Native Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile -
```

## Option 3: Windows Service

Use NSSM to run as a Windows service:
```bash
nssm install AI_API "C:\path\to\venv\Scripts\uvicorn.exe"
nssm set AI_API AppParameters "app.main:app --host 0.0.0.0 --port 8000"
nssm set AI_API AppDirectory "C:\path\to\project"
nssm start AI_API
```

## Reverse Proxy Configuration

### Nginx

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

### Caddy

```
api.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy automatically handles Let's Encrypt SSL certificates.

## Cloudflare Tunnel (Alternative)

```bash
# Install cloudflared
cloudflared tunnel create ai-api
cloudflared tunnel route dns ai-api api.example.com

# Create config.yml
tunnel: <tunnel-id>
credentials-file: /home/user/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: api.example.com
    service: http://localhost:8000
  - service: http_status:404
```

## Environment Variables

Create a `.env` file with:

```env
APP_NAME=AI API Platform
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=<random-64-char-string>
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/ai_api
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
CORS_ORIGINS=https://app.example.com
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=<strong-password>
```

## Security Checklist

- [ ] Change SECRET_KEY to a random value
- [ ] Change DEFAULT_ADMIN_PASSWORD
- [ ] Use strong database credentials
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Configure CORS for your domain
- [ ] Never expose LM Studio directly (port 1234)
- [ ] Use firewall rules to restrict access
- [ ] Enable rate limiting
- [ ] Monitor logs for suspicious activity
- [ ] Regularly rotate API keys

## Maintenance

### Database Backups

```bash
pg_dump -U postgres ai_api > backup_$(date +%Y%m%d).sql
```

### Updating

```bash
git pull
pip install -r requirements.txt --upgrade
# Restart the service
```

### Monitoring

- Health check: `GET /health`
- Status: `GET /status`
- Metrics: `GET /metrics` (Prometheus format)
