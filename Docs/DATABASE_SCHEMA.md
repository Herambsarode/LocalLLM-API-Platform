# Database Schema

## Entity Relationship Diagram

```
users (1) ────── (N) api_keys
users (1) ────── (N) usage_records
users (1) ────── (1) quotas
users (1) ────── (1) billing_accounts
billing_accounts (1) ────── (N) billing_transactions
```

## Tables

### users
Stores user accounts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique user ID |
| name | VARCHAR(255) | NOT NULL | User display name |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Login email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| role | ENUM('admin','user') | NOT NULL, default 'user' | User role |
| is_active | BOOLEAN | NOT NULL, default true | Account status |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

Indexes: `ix_users_email`

### api_keys
Stores API keys for authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique key ID |
| user_id | UUID | FK -> users.id, CASCADE | Owner |
| key_prefix | VARCHAR(20) | NOT NULL | First 20 chars of key |
| key_hash | VARCHAR(128) | UNIQUE, NOT NULL, INDEX | SHA-256 hash |
| name | VARCHAR(255) | NULLABLE | Key nickname |
| is_active | BOOLEAN | NOT NULL, default true | Key status |
| expires_at | TIMESTAMPTZ | NULLABLE | Expiration time |
| last_used_at | TIMESTAMPTZ | NULLABLE | Last usage time |
| usage_count | INTEGER | NOT NULL, default 0 | Total uses |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

Indexes: `ix_api_keys_key_hash`, `ix_api_keys_user_id`

### usage_records
Tracks API usage per request.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Record ID |
| user_id | UUID | FK -> users.id, CASCADE, INDEX | User |
| api_key_id | UUID | FK -> api_keys.id, SET NULL | API key used |
| model | VARCHAR(255) | NOT NULL | Model used |
| request_count | INTEGER | NOT NULL, default 1 | Requests |
| prompt_tokens | INTEGER | NOT NULL, default 0 | Input tokens |
| completion_tokens | INTEGER | NOT NULL, default 0 | Output tokens |
| total_tokens | INTEGER | NOT NULL, default 0 | Total tokens |
| response_time_ms | FLOAT | NOT NULL, default 0 | Latency |
| ip_address | VARCHAR(45) | NULLABLE | Client IP |
| country | VARCHAR(100) | NULLABLE | Geo location |
| endpoint | VARCHAR(255) | NULLABLE | API endpoint |
| status_code | INTEGER | NULLABLE | Response status |
| created_at | TIMESTAMPTZ | NOT NULL, INDEX | Timestamp |

Indexes: `ix_usage_records_user_id`, `ix_usage_records_created_at`

### quotas
Per-user usage limits.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Quota ID |
| user_id | UUID | FK -> users.id, CASCADE, UNIQUE | User |
| daily_requests_limit | INTEGER | NOT NULL, default 1000 | Max requests/day |
| monthly_requests_limit | INTEGER | NOT NULL, default 30000 | Max requests/month |
| daily_tokens_limit | BIGINT | NOT NULL, default 100000 | Max tokens/day |
| monthly_tokens_limit | BIGINT | NOT NULL, default 3000000 | Max tokens/month |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

### billing_accounts
Prepaid credit accounts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Account ID |
| user_id | UUID | FK -> users.id, CASCADE, UNIQUE | User |
| credits | FLOAT | NOT NULL, default 0 | Current credits |
| balance | FLOAT | NOT NULL, default 0 | Monetary balance |
| lifetime_credits | FLOAT | NOT NULL, default 0 | Total credits purchased |
| lifetime_spent | FLOAT | NOT NULL, default 0 | Total credits used |
| is_active | BOOLEAN | NOT NULL, default true | Account status |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

### billing_transactions
Transaction history for billing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Transaction ID |
| account_id | UUID | FK -> billing_accounts.id, CASCADE, INDEX | Account |
| transaction_type | ENUM | NOT NULL | credit_purchase, usage_deduction, refund, admin_adjustment |
| amount | FLOAT | NOT NULL | Transaction amount |
| credits_before | FLOAT | NOT NULL | Credits before tx |
| credits_after | FLOAT | NOT NULL | Credits after tx |
| description | TEXT | NULLABLE | Transaction note |
| reference_id | VARCHAR(255) | NULLABLE | External reference |
| created_at | TIMESTAMPTZ | NOT NULL | Timestamp |

### models
Registered model configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Model ID |
| model_id | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Model identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| provider | VARCHAR(255) | NOT NULL, default 'lm_studio' | Provider |
| description | TEXT | NULLABLE | Description |
| context_length | INTEGER | NULLABLE | Context window |
| is_active | BOOLEAN | NOT NULL, default true | Model enabled |
| is_default | BOOLEAN | NOT NULL, default false | Default model |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |
