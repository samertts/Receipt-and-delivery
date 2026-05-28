# Architecture Document - نظام إدارة الاستلام المختبري

## Overview

The system follows a **dual-architecture** approach:

1. **Desktop Application** (PySide6 + SQLite): Complete offline desktop app for laboratory environments
2. **Web Application** (FastAPI + PostgreSQL + Vue 3): RESTful API with modern PWA frontend

Both share the same domain model and business logic principles.

---

## Architecture Diagrams

### Desktop App Architecture

```
┌─────────────────────────────────────────┐
│              PySide6 UI                 │
│  Login → MainWindow → Pages            │
├─────────────────────────────────────────┤
│              Services Layer             │
│  AuthService  UserService  ReceiptService│
│  OrgService   CatalogService BackupSvc  │
├─────────────────────────────────────────┤
│           Data Access Layer             │
│  BaseRepository  connection_scope       │
├─────────────────────────────────────────┤
│            SQLite Database              │
│  13 tables + WAL mode + Migrations     │
└─────────────────────────────────────────┘
```

### Web API Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Vue 3   │────▶│  FastAPI │────▶│PostgreSQL│
│  PWA     │     │  REST    │     │          │
└──────────┘     └──────────┘     └──────────┘
     │                │
     │                ├── Auth (JWT + bcrypt)
     │                ├── Rate Limiting
     │                ├── Audit Logging
     │                ├── Structured Logging
     │                └── Centralized Error Handling
     │
     ├── Pinia Stores
     ├── Axios Client
     └── Service Worker (PWA)
```

---

## Database Schema

### SQLite (Desktop) - 13 tables

| Table | Purpose |
|-------|---------|
| `meta` | Key-value metadata store |
| `organizations` | Health institutions (35 Iraqi labs) |
| `users` | System users with roles |
| `transaction_types` | Dynamic transaction catalog |
| `sample_types` | Dynamic sample catalog |
| `templates` | Receipt templates |
| `receipts` | Main transaction records |
| `receipt_items` | Line items with sample counts |
| `attachments` | File attachments with SHA-256 |
| `settings` | Application settings |
| `schema_version` | Schema version tracking |
| `migration_history` | Migration audit trail |
| `migration_lock` | Concurrent migration protection |
| `backups` | Backup records |
| `audit_logs` | Immutable audit trail |

### PostgreSQL (Web) - 6 tables

Same domain model with UUID primary keys and proper foreign key relationships.

---

## Security Architecture

- **Password Hashing**: bcrypt (12 rounds)
- **Authentication**: JWT (HS256) with configurable expiry
- **RBAC**: 4 roles with hierarchical permissions
- **Rate Limiting**: Per-IP for login (5/min) and API (100/min)
- **Audit Logging**: All sensitive operations logged
- **CORS**: Configurable allowed origins
- **Input Validation**: Pydantic schemas + SQL parameterization

---

## Key Design Decisions

1. **Offline-first**: Desktop app works completely offline with SQLite
2. **Dual deployment**: Same system can run as desktop app or web app
3. **Dynamic catalogs**: Transaction types and sample types are DB-driven
4. **Immutable audit logs**: WAL mode + insert-only pattern
5. **Migration system**: Lock-based concurrent migration protection
6. **PDF generation**: ReportLab with QR + Code128 barcode
