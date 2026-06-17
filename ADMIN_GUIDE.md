# Admin Guide - نظام إدارة الاستلام المختبري

## Installation

### Desktop Application

1. Download `LabReceiptSystem.exe` from the release
2. Run the installer
3. Application will create necessary folders in `%LOCALAPPDATA%/LabReceiptSystem/`

### Web Backend

```bash
# Clone repository
git clone git@github.com:samertts/Receipt-and-delivery.git
cd Receipt-and-delivery

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+psycopg://lab_user:lab_pass@localhost:5432/lab_txn |
| SECRET_KEY | JWT signing key | (required) |
| ALLOWED_ORIGINS | CORS origins | http://localhost:5173 |
| LOG_LEVEL | Logging level | INFO |

### Desktop Settings

Access via Settings page in the application:

| Setting | Description | Default |
|---------|-------------|---------|
| receipt.numbering_prefix | Receipt number prefix | RCP |
| receipt.font_size | PDF font size | 12 |
| backup.auto_enabled | Auto-backup | false |
| session.timeout_minutes | Session timeout | 30 |

## User Management

### Roles

| Role | Permissions |
|------|------------|
| Admin | Full access |
| Supervisor | Most operations, no user/settings management |
| User | Receipts create/read, organizations read |
| Auditor | Read-only access |

### Creating Users

1. Navigate to Users page
2. Click "Create User"
3. Enter username, full name, password, role
4. Password must be 8+ chars with uppercase, lowercase, digit, special char

## Backup & Recovery

### Creating Backups

1. Navigate to Backup page
2. Click "Create Backup"
3. Backup stored in `%LOCALAPPDATA%/LabReceiptSystem/database/backups/`

### Restoring Backups

1. Navigate to Backup page
2. Click "Restore" on desired backup
3. Confirm restoration

### Automated Backups

Enable in Settings → backup.auto_enabled

## Monitoring

### Health Endpoints

- `GET /health` — Overall status
- `GET /health/live` — Liveness probe
- `GET /health/ready` — Readiness probe
- `GET /health/version` — Version info
- `GET /health/dependencies` — Dependency status

### Audit Logs

Access via Audit page or API:
```
GET /api/audit-logs
```

## Troubleshooting

### Database Issues

1. Run startup diagnostics (automatic on launch)
2. Check database integrity via Backup page
3. Restore from backup if needed

### Sync Issues

1. Check sync status on dashboard
2. Verify network connectivity
3. Check API server availability

### Performance Issues

1. Check database indexes (startup diagnostics)
2. Verify WAL mode is enabled
3. Monitor rate limiting logs
