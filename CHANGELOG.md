# Changelog - نظام إدارة الاستلام المختبري

## [1.0.0] - 2026-05-27

### Added
- Complete PySide6 desktop application with SQLite
- FastAPI web backend with PostgreSQL
- Vue 3 PWA frontend with 9 functional pages
- JWT-based authentication with refresh tokens
- Role-based access control (Admin/Supervisor/User/Auditor)
- RESTful API with Swagger/ReDoc documentation
- Structured JSON logging system
- Centralized error handling with custom exceptions
- Rate limiting (login: 5/min, API: 100/min)
- Password strength validation
- Audit logging for all sensitive operations
- Dynamic receipt numbering (LAB-YYYY-XXXXXX)
- PDF generation with QR Code + Code128 barcode
- Attachment management with SHA-256 hash
- SQLite migration system with lock protection
- Backup system with retention policy
- 35 Iraqi health organization seed data
- Docker Compose setup (PostgreSQL + Backend + Frontend)
- CI/CD pipeline (GitHub Actions + Inno Setup)
- Comprehensive test suite (auth, RBAC, transactions, etc.)
- Arabic RTL support throughout
- PWA support with offline service worker config

### Security
- bcrypt password hashing (12 rounds)
- JWT HS256 with configurable expiry
- CORS with configurable origins
- Input validation via Pydantic
- SQL injection prevention (parameterized queries + ORM)
- Migration lock for concurrent safety
- Immutable audit logs

### Notes
- Default credentials: admin / Admin@123 (change immediately)
- Secret key auto-generated if not configured
- Desktop app runs fully offline with SQLite
- Web app requires PostgreSQL 16
