# Deployment Checklist

**Project:** Receipt-and-delivery
**Release:** v1.2.0
**Date:** 2026-06-18
**Classification:** PRODUCTION DEPLOYMENT CHECKLIST

---

## Pre-Deployment Verification

### 1. Release Verification

| Check | Status | Value |
|-------|--------|-------|
| RC tag verified | ☐ | `v1.2.0-rc1` exists on remote |
| Branch merged to main | ☐ | `feature/v1.2.0-ui-modernization-phase2` merged |
| Release tag created | ☐ | `v1.2.0` tag exists |
| VERSION updated | ☐ | `1.2.0` in VERSION file |
| All tests passing | ☐ | 46/46 backend + 72/72 UAT |

### 2. Code Quality

| Check | Status | Value |
|-------|--------|-------|
| Ruff lint clean | ☐ | 0 errors |
| No critical findings | ☐ | 0 critical |
| No high findings | ☐ | 0 high |
| Security scan clean | ☐ | Bandit PASS |

### 3. Documentation

| Check | Status |
|-------|--------|
| CHANGELOG.md updated | ☐ |
| RELEASE_NOTES_v1.2.0.md complete | ☐ |
| DEPLOYMENT_GUIDE.md reviewed | ☐ |
| ADMIN_GUIDE.md reviewed | ☐ |
| USER_GUIDE.md reviewed | ☐ |
| BACKUP_AND_RECOVERY_GUIDE.md reviewed | ☐ |

---

## Deployment Steps

### Phase 1: Backup (Pre-Deployment)

| Step | Action | Status |
|------|--------|--------|
| 1.1 | Create full database backup | ☐ |
| 1.2 | Verify backup integrity | ☐ |
| 1.3 | Copy backup to safe location | ☐ |
| 1.4 | Document backup filename/path | ☐ |
| 1.5 | Verify rollback package ready | ☐ |

### Phase 2: Server Preparation

| Step | Action | Status |
|------|--------|--------|
| 2.1 | Notify users of maintenance window | ☐ |
| 2.2 | Stop application services | ☐ |
| 2.3 | Verify no active connections | ☐ |
| 2.4 | Download release artifacts | ☐ |
| 2.5 | Verify artifact checksums | ☐ |

### Phase 3: Database Migration

| Step | Action | Status |
|------|--------|--------|
| 3.1 | Run database migrations | ☐ |
| 3.2 | Verify migration version | ☐ |
| 3.3 | Run integrity check | ☐ |
| 3.4 | Verify indexes | ☐ |
| 3.5 | Verify foreign keys | ☐ |

### Phase 4: Application Deployment

| Step | Action | Status |
|------|--------|--------|
| 4.1 | Deploy backend API | ☐ |
| 4.2 | Deploy frontend/static assets | ☐ |
| 4.3 | Update configuration | ☐ |
| 4.4 | Verify configuration | ☐ |
| 4.5 | Start application services | ☐ |

### Phase 5: Post-Deployment Verification

| Step | Action | Status |
|------|--------|--------|
| 5.1 | Health check endpoint | ☐ |
| 5.2 | Authentication test | ☐ |
| 5.3 | Receipt CRUD test | ☐ |
| 5.4 | User management test | ☐ |
| 5.5 | RBAC verification | ☐ |
| 5.6 | Audit logging test | ☐ |
| 5.7 | Sync service test | ☐ |
| 5.8 | Backup verification | ☐ |

### Phase 6: Smoke Tests

| Step | Action | Status |
|------|--------|--------|
| 6.1 | Login as admin | ☐ |
| 6.2 | Create receipt | ☐ |
| 6.3 | Update receipt | ☐ |
| 6.4 | Search receipts | ☐ |
| 6.5 | Approve receipt | ☐ |
| 6.6 | Archive receipt | ☐ |
| 6.7 | Create user | ☐ |
| 6.8 | Test RBAC (user vs admin) | ☐ |
| 6.9 | View audit logs | ☐ |
| 6.10 | Health endpoints | ☐ |

---

## Post-Deployment Monitoring

### 72-Hour Monitoring Plan

| Hour | Check | Status |
|------|-------|--------|
| H+1 | Application health | ☐ |
| H+1 | Error logs review | ☐ |
| H+1 | Performance metrics | ☐ |
| H+4 | Application health | ☐ |
| H+4 | Error logs review | ☐ |
| H+4 | User feedback | ☐ |
| H+8 | Application health | ☐ |
| H+8 | Database performance | ☐ |
| H+8 | Sync status | ☐ |
| H+24 | Full health review | ☐ |
| H+24 | Error trend analysis | ☐ |
| H+24 | Performance baseline | ☐ |
| H+48 | Application health | ☐ |
| H+48 | User complaints review | ☐ |
| H+72 | Final sign-off | ☐ |

---

## Rollback Triggers

Initiate rollback if any of the following occur:

| Trigger | Action |
|---------|--------|
| Critical error in logs | ROLLBACK |
| Database corruption | ROLLBACK |
| Authentication failure | ROLLBACK |
| Data loss detected | ROLLBACK |
| >5% error rate | ROLLBACK |
| Performance degradation >50% | ROLLBACK |
| User-reported data loss | ROLLBACK |

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Deployment Lead | _________________ | __________ | ☐ APPROVED |
| DBA | _________________ | __________ | ☐ APPROVED |
| QA Lead | _________________ | __________ | ☐ APPROVED |
| Operations | _________________ | __________ | ☐ APPROVED |

---

**END OF DEPLOYMENT CHECKLIST**
