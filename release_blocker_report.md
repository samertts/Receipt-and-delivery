# Release Blocker Report

**Project:** Receipt-and-delivery
**Date:** 2026-06-18
**Scope:** Hidden bugs, regressions, security weaknesses, architecture flaws
**Classification:** ULTIMATE CERTIFICATION — PHASE 10

---

## Executive Summary

Found **3 Critical**, **8 High**, **9 Medium**, and **5 Low** findings.

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 8 |
| Medium | 9 |
| Low | 5 |
| **Total** | **25** |

**Status: NOT READY FOR RELEASE**

---

## CRITICAL — Blocks Release

### 1. SQL Injection via `ilike` f-string in Transaction Search
- **Location:** `backend/app/repositories/__init__.py:38`
- **Evidence:** `query = query.filter(Transaction.transaction_no.ilike(f"%{search}%"))`
- **Impact:** Wildcard-based data extraction possible
- **Fix:** Use `escape_like(search)` or explicit bind parameters

### 2. Organization Deletion Does Not Check Referential Integrity
- **Location:** `backend/app/services/organization_service.py:111-120`
- **Impact:** 500 error when deleting organization with transactions
- **Fix:** Check for referencing transactions before delete

### 3. Unhandled Database Session in Transaction Create
- **Location:** `backend/app/services/transaction_service.py:60-73`
- **Impact:** Partially created transaction with 0 items
- **Fix:** Wrap entire create in single transaction

---

## HIGH — Must Fix Before Release

### 4. Unbounded Memory Growth in `MemoryRateLimiter`
- **Location:** `backend/app/core/security.py:32-45`
- **Impact:** Memory exhaustion over time
- **Fix:** Add periodic cleanup of stale keys

### 5. Rate Limiter Disabled in Debug Mode
- **Location:** `backend/app/core/security.py:109`
- **Impact:** Brute-force attacks possible
- **Fix:** Only disable for `TESTING` env var

### 6. Sync Push Endpoint Has No Input Validation
- **Location:** `backend/app/api/v1/sync.py:15-33`
- **Impact:** Denial of service via large payloads
- **Fix:** Create Pydantic schema for sync push requests

### 7. Frontend Token Storage in `localStorage`
- **Location:** `frontend/src/stores/auth.js:7-8, 18-19, 51-53`
- **Impact:** XSS can steal tokens
- **Fix:** Store in httpOnly cookies

### 8. No CORS Origin Validation Fallback to Wildcard
- **Location:** `backend/app/core/config.py:83`
- **Impact:** Security bypass when misconfigured
- **Fix:** Remove `or ["*"]` fallback

### 9. No Database Migration Framework for Backend
- **Location:** `backend/app/db/session.py:26-27`
- **Impact:** Schema changes require manual intervention
- **Fix:** Initialize Alembic

### 10. Health Endpoint Exposes Server Version Information
- **Location:** `backend/app/api/v1/health.py:75-92`
- **Impact:** Information disclosure
- **Fix:** Remove framework version details

### 11. No Nginx Security Headers in Production
- **Location:** `frontend/nginx.conf`
- **Impact:** Vulnerable to clickjacking, XSS
- **Fix:** Add all standard security headers

---

## MEDIUM — Should Fix Before Release

### 12. Transaction Number Generation Collision Risk
- **Location:** `backend/app/services/transaction_service.py:177-178`
- **Impact:** Duplicate transaction numbers possible
- **Fix:** Add random suffix or database sequence

### 13. Transaction Creation Not Atomic
- **Location:** `backend/app/services/transaction_service.py:42-73`
- **Impact:** Orphaned transaction records
- **Fix:** Use single `db.add()` + `db.commit()`

### 14. Dev Docker Compose Exposes PostgreSQL Without TLS
- **Location:** `docker-compose.yml:13`
- **Impact:** Database accessible from network
- **Fix:** Bind to `127.0.0.1:5432:5432`

### 15. `response_envelope_middleware` Consumes Response Stream
- **Location:** `backend/app/main.py:81-94`
- **Impact:** Large responses cause OOM
- **Fix:** Only apply to small JSON responses

### 16. `datetime.utcnow()` Deprecated
- **Location:** `backend/app/api/v1/health.py:26`
- **Impact:** Will break in future Python versions
- **Fix:** Replace with `datetime.now(timezone.utc)`

### 17. Frontend Token Refresh Parses JWT Without Verification
- **Location:** `frontend/src/stores/auth.js:21`
- **Impact:** Client trusts tampered tokens
- **Fix:** Fetch user profile from server

### 18. Desktop SQLite FTS DELETE Triggers Are No-Ops
- **Location:** `lab_system/app/database/db.py:160-162, 171-173`
- **Impact:** Deleted records appear in search
- **Fix:** Implement proper FTS cleanup

### 19. Container DI Partially Implemented
- **Location:** `backend/app/api/container_deps.py:18-22`
- **Impact:** Dead code, confusion about DI pattern
- **Fix:** Either fully use container or remove it

### 20. Backend Dockerfile Runs as Root
- **Location:** `backend/Dockerfile`
- **Impact:** Root access if compromised
- **Fix:** Add non-root user

---

## LOW — Can Fix After Release

### 21. Duplicate `_compute_hash` Function
### 22. `_active_only` Query Parameter Unused
### 23. Import Inside Middleware Function
### 24. Backend Startup Token Purge Swallows All Exceptions
### 25. No `httpOnly` Cookie Support for Refresh Token

---

## Release Readiness Assessment

**Status: NOT READY FOR RELEASE**

The 3 Critical issues and 8 High issues must be resolved before v1.2.0 can ship.

**Estimated remediation time:** 2-3 days for Critical+High items.

---

**END OF RELEASE BLOCKER REPORT**
