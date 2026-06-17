# Release Notes v1.2.0

**Date:** 2026-06-17
**Version:** 1.2.0-rc1
**Classification:** Release Candidate

## Overview

v1.2.0 introduces significant architectural improvements focused on production readiness, security hardening, and operational maturity. This release candidate has passed all quality gates and is approved for stakeholder review.

## Key Changes

### Architecture Hardening

- **Dependency Injection Container:** Centralized service container with lazy singleton resolution
- **Service Layer:** All API routes now delegate to dedicated service classes
- **Repository Standardization:** Consistent BaseRepository pattern across backend and desktop

### Security Improvements

- **Fail-Closed Permissions:** Permission decorator now raises errors when user context is missing
- **Last-Admin Protection:** System prevents deletion of the last administrator
- **Self-Role-Change Protection:** Administrators cannot modify their own role

### Operational Enhancements

- **Health Endpoints:** 5 comprehensive health check endpoints
- **Startup Diagnostics:** Automatic system verification on launch
- **Structured Logging:** JSON-formatted logs with audit trail

### Sync Production Readiness

- **Durable Queue:** SQLite-backed sync queue survives restarts
- **Retry Logic:** Automatic retry with exponential backoff
- **Conflict Resolution:** Last-writer-wins strategy with server fallback

## Upgrade Notes

- Database schema is backward-compatible with v1.1.0
- No breaking API changes
- Desktop application requires restart after upgrade

## Known Issues

- Frontend package.json version not yet updated to 1.2.0
- Coverage at 80% (core business logic >90%)

## Testing

- 46/46 automated tests pass
- Ruff linting clean
- Bandit security scan: 0 high, 1 medium (acceptable), 2 low (false positives)

## Classification

**RELEASE CANDIDATE APPROVED** — Awaiting stakeholder review.
