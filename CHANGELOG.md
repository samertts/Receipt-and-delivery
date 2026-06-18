# Changelog - نظام إدارة الاستلام المختبري

جميع التغييرات المهمة على المشروع سيتم توثيقها في هذا الملف.

يعتمد هذا المشروع على مبادئ Semantic Versioning.

---

# [1.2.0-rc1] - 2026-06-17

الحالة: Release Candidate

## Added

* Centralized dependency injection container (ServiceContainer)
* Service layer for all backend API routes
* DashboardService, DesktopAuditService, DesktopSettingsService, BackupListingService
* Health endpoints: /health, /health/live, /health/ready, /health/version, /health/dependencies
* Last-admin protection (cannot delete last admin)
* Self-role-change protection (admin cannot change own role)
* Fail-closed permission decorator (raises error when user=None)

## Changed

* All API routes now use service layer (AuthService, UserService, OrganizationService, TransactionService, AuditService, SyncService)
* Error response format standardized: error_code and status_code moved to meta block
* Response envelope middleware cleaned up (removed duplicate)
* Desktop UI pages (dashboard, audit, settings, backup) now use service layer

## Fixed

* Cross-layer violations in desktop UI (12 violations eliminated)
* UI call sites bypassing authorization (receipts_page.py, receipt_dialog.py)
* Test fixture ordering issues (conftest.py rewritten for robustness)
* Ruff lint errors (unused imports)

## Security

* Fail-closed @with_permission decorator
* Last-admin protection
* Self-role-change protection
* All endpoints verified with RBAC

---

# [1.2.0-dev] - Development Branch

الحالة: Development Only

الفرع:

feature/v1.2.0-dev

لم يتم دمج هذه التغييرات في الإنتاج.

## Added

* Refresh Token Rotation with Blacklist
* Logout Endpoint with Token Blacklisting
* Change Password Endpoint
* Redis-backed Rate Limiter with In-Memory Fallback
* Transaction Deep Update (Add/Delete Items via PUT)
* Pagination using X-Total-Count
* Organization Search Dropdowns
* Sample Type Autocomplete
* Audit Changes JSON Viewer
* Dashboard Accurate Counters
* Network Connectivity Diagnostics
* Real HTTP Transport in APIClient

## Changed

* Block inactive users from login and protected endpoints
* Rename RateLimiter to MemoryRateLimiter
* Remove unused ROLE_HIERARCHY
* Restrict transaction deletion to administrators

## Notes

This branch is under development and is not part of the production release.

---

# [1.1.0] - 2026-06-08

الحالة: Production Release

Tag:

v1.1.0

## Fixed

### Full-Text Search (FTS)

* Fixed SQLite content-sync FTS compatibility issues
* Fixed hyphen handling in search queries
* Fixed hard delete cleanup for FTS records
* Preserved FTS entries during soft delete
* Rebuilt FTS entries correctly during restore operations

### Backup & Recovery

* Replaced file-copy backups with sqlite3.Connection.backup()
* Added WAL checkpoint handling
* Improved backup consistency during active database usage
* Fixed unclosed recovery connections
* Protected recovery procedures against WAL-related failures

### Attachments

* Added SHA-256 duplicate detection
* Prevented duplicate file storage

### Diagnostics

* Expanded startup diagnostics to validate all production indexes

### Security

* Block inactive users at login
* Block inactive users on protected endpoints
* Fixed ForbiddenError instantiation issue
* Removed unused ROLE_HIERARCHY references

### CI/CD

* Fixed Inno Setup installer path
* Improved release version synchronization

### Testing

* Fixed SQLAlchemy model registration during tests

## Changed

* VERSION file is now the single source of truth
* Application version automatically reads from VERSION
* All version references synchronized to 1.1.0

## Production Certification

* Tests: 26/26 PASS
* Build Certification: 117/117 PASS
* Migration Certification: 328/328 PASS
* FTS Integrity: PASS
* Backup Integrity: PASS
* Recovery Integrity: PASS
* Attachment Integrity: PASS
* Version Governance: PASS
* CI/CD Validation: PASS

---

# [1.0.0] - 2026-05-27

الحالة: Initial Production Baseline

## Added

### Desktop Application

* PySide6 Desktop Application
* SQLite Local Database
* Full Offline Operation

### Web Platform

* FastAPI Backend
* PostgreSQL Support
* Vue 3 Progressive Web Application (PWA)

### Core Features

* Role-Based Access Control (RBAC)
* REST API
* Swagger / ReDoc Documentation
* Structured Logging
* Centralized Error Handling
* Audit Logging
* Dynamic Receipt Numbering
* PDF Generation
* QR Code Support
* Barcode Support
* Attachment Management
* Migration Framework
* Backup Framework
* Iraqi Health Organization Seed Data
* Docker Deployment Support
* GitHub Actions CI/CD
* Arabic RTL Support

### Security

* bcrypt Password Hashing
* JWT Authentication
* CORS Protection
* Input Validation
* SQL Injection Protection
* Migration Locking
* Immutable Audit Logs

## Notes

* Default Credentials: admin / Admin@123
* Desktop Application Works Fully Offline
* Web Platform Requires PostgreSQL
* This version represents the initial production baseline

---

# Version Policy

Production Branch:
main

Production Release:
v1.1.0

Development Branch:
feature/v1.2.0-dev

Rules:

* No direct development on main
* No direct commits to production releases
* All new features start from feature branches
* All merges require review and validation
* Production releases must be tagged before deployment

---

Last Production Release:

v1.1.0

Repository:

[git@github.com](mailto:git@github.com):samertts/Receipt-and-delivery.git
