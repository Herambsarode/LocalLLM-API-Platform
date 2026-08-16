# Security Overview

## Authentication

### API Key Authentication
- All OpenAI-compatible endpoints require `Authorization: Bearer sk_live_...`
- API keys are hashed with SHA-256 before storage
- Raw keys are shown only once at creation
- Keys can be rotated, disabled, or deleted

### JWT Authentication
- Admin dashboard uses JWT tokens
- Tokens expire after configurable period (default: 60 minutes)
- Passwords hashed with bcrypt (12 rounds)

## API Key Format

```
sk_live_<64-hex-characters>
```

Total length: 72 characters
- Prefix: `sk_live_` (8 chars)
- Random: 64 hex chars (256 bits of entropy)

## Security Measures

### HTTPS
- All traffic must use HTTPS in production
- TLS termination handled by reverse proxy (Nginx/Caddy)
- Let's Encrypt for free SSL certificates

### CORS
- Configurable allowed origins
- Default: `*` for development
- Lock down to specific domains in production

### Input Validation
- Pydantic v2 schemas validate all input
- SQL injection protection via SQLAlchemy ORM
- Request size limits applied

### Password Security
- bcrypt hashing with 12 rounds
- Minimum 8 character requirement
- Stored as salted hashes only

### API Key Security
- SHA-256 hashed before storage
- Never stored in plaintext
- Key prefix stored for identification only
- Only the full key hash is stored

### Rate Limiting
- Configurable per-key rate limits
- Returns 429 Too Many Requests
- Prevents abuse and DoS attacks

### Headers
```http
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

## Environment Variables

All secrets must be set via environment variables:
- `SECRET_KEY` - JWT signing secret (minimum 64 characters)
- `DATABASE_URL` - Database connection string with credentials
- `DEFAULT_ADMIN_PASSWORD` - Initial admin password (change immediately)

## Best Practices

1. **Never expose LM Studio directly** - Always go through the API gateway
2. **Use firewall rules** - Restrict access to ports 1234 (LM Studio) and 5432 (PostgreSQL)
3. **Rotate API keys regularly** - Use the rotation endpoint
4. **Monitor logs** - Check for unusual patterns in API usage
5. **Use strong secrets** - Generate random SECRET_KEY and admin passwords
6. **Regular updates** - Keep dependencies updated for security patches
7. **Database encryption** - Use encrypted database connections
8. **Network isolation** - Run services in separate Docker networks

## Threat Model

| Threat | Mitigation |
|--------|------------|
| API key theft | Hashing, rotation, HTTPS |
| Brute force | Rate limiting, bcrypt |
| SQL injection | ORM, parameterized queries |
| XSS | Input validation, CORS |
| DoS | Rate limiting, quotas |
| Data breach | Encrypted storage, hashed secrets |
| MITM | HTTPS-only, HSTS |
