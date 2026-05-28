# Security Policy - نظام إدارة الاستلام المختبري

## Authentication

- Passwords hashed with **bcrypt** (12 salt rounds)
- JWT tokens with **HS256** algorithm, configurable expiry (default: 120 min)
- Refresh tokens supported (default: 7 days)
- Rate limiting: 5 login attempts per minute per IP

## Password Policy

- Minimum 8 characters
- Requires: uppercase, lowercase, digit, special character
- Maximum 128 characters

## Authorization (RBAC)

| Role | Permissions |
|------|------------|
| Admin | Full system access |
| Supervisor | CRUD transactions, view users, manage orgs |
| User | View and create transactions |
| Auditor | View dashboard and audit logs |

## Data Protection

- **SQLite**: WAL mode, foreign keys enforced
- **PostgreSQL**: Connection pooling, SSL recommended
- **Attachments**: SHA-256 hash verification, image compression
- **Backups**: Automated optional, retention configurable

## API Security

- CORS: Configurable allowed origins (default: localhost)
- All endpoints except `/auth/login` and `/health` require JWT
- Input validation via Pydantic schemas
- SQL injection prevented via parameterized queries / ORM

## Reporting Vulnerabilities

For security issues, contact the system administrator immediately.
Do not disclose vulnerabilities publicly until they are resolved.

## Production Deployment Checklist

- [ ] Change default admin password (`Admin@123`)
- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Restrict CORS origins to specific domains
- [ ] Enable HTTPS (reverse proxy: nginx/caddy)
- [ ] Configure proper database credentials
- [ ] Enable auto-backup
- [ ] Set log level to `WARNING` in production
- [ ] Regular security audits
