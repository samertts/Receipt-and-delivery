# Adversarial Security Report

**Project:** Receipt-and-delivery
**Date:** 2026-06-18
**Scope:** Full security assessment
**Classification:** ULTIMATE CERTIFICATION — PHASE 2

---

## Executive Summary

Comprehensive adversarial security assessment of the Receipt-and-Delivery system. Found **1 Critical**, **1 High**, **6 Medium**, and **3 Low** findings.

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 1 |
| Medium | 6 |
| Low | 3 |
| **Total** | **11** |

**Overall Security Posture: B+ (Good with notable gaps)**

---

## 1. JWT Implementation

| Finding | Severity | Status |
|---------|----------|--------|
| HS256 algorithm (symmetric) | **Medium** | Weakness |
| Access token expiry 120 min | Low | Acceptable |
| Refresh token expiry 7 days | Low | Acceptable |
| Refresh token rotation implemented | ✅ | Good |
| Token blacklisting on logout/refresh | ✅ | Good |
| Secret key auto-generated (256-bit) | ✅ | Good |

**MEDIUM: HS256 vs RS256** — Uses symmetric algorithm. If secret key is compromised, all tokens are forgeable.

**MEDIUM: Secret Key in plaintext file** — `.generated_secret_key.json` contains signing key. If exposed, full system compromise.

---

## 2. Authentication

| Finding | Severity | Status |
|---------|----------|--------|
| bcrypt hashing (both systems) | ✅ | Good |
| Password strength validation | ✅ | Good |
| Rate limiting on login (5/min) | ✅ | Good |
| **Rate limiting bypassed in DEBUG/TESTING** | **High** | Vulnerability |
| Rate limiting IP-only (no user correlation) | **Medium** | Weakness |
| No account lockout on backend API | **Medium** | Weakness |
| Refresh tokens in localStorage | **Medium** | Weakness |

**HIGH: Rate Limiter Completely Bypassed in Debug Mode**
```python
if os.environ.get("TESTING") or settings.debug:
    return await call_next(request)
```
If `DEBUG=true` is set in production, all rate limiting is disabled.

---

## 3. RBAC

| Finding | Severity | Status |
|---------|----------|--------|
| All backend routes use `require_permission` | ✅ | Good |
| Desktop uses `@with_permission` decorator | ✅ | Good |
| Fail-closed if user is None | ✅ | Good |
| Role hierarchy properly enforced | ✅ | Good |
| Self-escalation prevention | ✅ | Good |

**All routes are properly protected. Fail-closed behavior verified.**

---

## 4. SQL Injection

| Finding | Severity | Status |
|---------|----------|--------|
| Backend uses SQLAlchemy ORM | ✅ | Good |
| Backend repos use parameterized queries | ✅ | Good |
| Desktop uses parameterized raw SQL | ✅ | Good |
| No f-string SQL with user input | ✅ | Good |
| FTS query parameterized | ✅ | Good |

**No SQL injection vulnerabilities found.**

---

## 5. Path Traversal

| Finding | Severity | Status |
|---------|----------|--------|
| Filename sanitization via `Path.name` | ✅ | Good |
| Regex-based filename cleaning | ✅ | Good |
| Resolved path validation | ✅ | Good |
| Magic byte verification | ✅ | Good |
| Recovery: path validation via `_validate_path_in_dir` | ✅ | Good |
| File size limit (50MB) | ✅ | Good |

**Defense-in-depth on file uploads verified.**

---

## 6. XSS

| Finding | Severity | Status |
|---------|----------|--------|
| 58 `v-html` usages for SVG icons | **Low** | Acceptable |
| No `v-html` with user input | ✅ | Good |
| Vue template interpolation `{{ }}` auto-escapes | ✅ | Good |

All `v-html` instances render static SVG icons. User data rendered via auto-escaping `{{ }}`.

---

## 7. CORS Configuration

| Finding | Severity | Status |
|---------|----------|--------|
| CORS origins configurable | ✅ | Good |
| Default restricted to localhost | ✅ | Good |
| **Fallback to `*` if origin list empty** | **Medium** | Weakness |

**MEDIUM:** If `ALLOWED_ORIGINS` is empty, CORS falls back to `["*"]`, allowing any origin with credentials.

---

## 8. Information Leakage

| Finding | Severity | Status |
|---------|----------|--------|
| Generic 500 error message | ✅ | Good |
| Custom error codes without details | ✅ | Good |
| Login failure doesn't reveal which field is wrong | ✅ | Good |
| **Username logged in failed login attempts** | **Low** | Weakness |

---

## 9. Insecure Deserialization

**No vulnerabilities found.** All data parsing uses safe methods (JSON, Pydantic schemas).

---

## 10. Audit Log Tampering

| Finding | Severity | Status |
|---------|----------|--------|
| Hash chain implemented (both systems) | ✅ | Good |
| SHA-256 for chain hashing | ✅ | Good |
| Chain verification function available | ✅ | Good |
| **Chain uses non-unique hash input** | **Low** | Weakness |
| **No external append-only guarantee** | **Low** | Weakness |

---

## Summary of Vulnerabilities

| # | Vulnerability | Severity | Component |
|---|--------------|----------|-----------|
| 1 | CORS fallback to wildcard origin | **Medium** | Backend API |
| 2 | HS256 instead of RS256 | **Medium** | JWT |
| 3 | Secret key in plaintext file | **Medium** | Backend Config |
| 4 | No account lockout on API | **Medium** | Backend Auth |
| 5 | Refresh tokens in localStorage | **Medium** | Frontend |
| 6 | Rate limiting IP-only | **Medium** | Backend API |
| 7 | Rate limiting bypassed in DEBUG mode | **High** | Backend API |
| 8 | Audit chain non-unique hash input | **Low** | Audit |
| 9 | No append-only audit store | **Low** | Audit |
| 10 | Username in failed login logs | **Low** | Backend Auth |

---

## Remediation Priority

1. **HIGH:** Remove `settings.debug` check from rate limiter bypass
2. **HIGH:** Prevent CORS wildcard fallback
3. **HIGH:** Move `.generated_secret_key.json` to secure storage
4. **MEDIUM:** Implement account lockout on backend API
5. **MEDIUM:** Consider RS256 for JWT signing
6. **MEDIUM:** Store refresh tokens in httpOnly cookies
7. **LOW:** Add timestamp/nonce to audit chain hash input
8. **LOW:** Consider append-only audit log storage

---

## What's Done Well

- Defense-in-depth on file uploads
- Parameterized queries consistently
- RBAC enforced on all API routes
- Refresh token rotation with blacklisting
- Audit logging with hash chain
- Generic error messages
- Input validation via Pydantic schemas
- Session timeout and account lockout in desktop

---

**END OF ADVERSARIAL SECURITY REPORT**
