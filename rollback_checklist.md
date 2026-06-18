# Rollback Checklist

**Project:** Receipt-and-delivery
**Release:** v1.2.0
**Date:** 2026-06-18
**Classification:** ROLLBACK PROCEDURE

---

## Rollback Decision Matrix

| Severity | Condition | Action |
|----------|-----------|--------|
| CRITICAL | Data loss detected | IMMEDIATE ROLLBACK |
| CRITICAL | Database corruption | IMMEDIATE ROLLBACK |
| CRITICAL | Authentication broken | IMMEDIATE ROLLBACK |
| HIGH | >5% error rate | ROLLBACK within 15 min |
| HIGH | Performance degraded >50% | ROLLBACK within 15 min |
| MEDIUM | Feature regression | Evaluate, may rollback |
| LOW | Minor UI issue | Hotfix, no rollback |

---

## Pre-Rollback Verification

| Step | Action | Status |
|------|--------|--------|
| 1 | Confirm rollback is necessary | ☐ |
| 2 | Identify rollback scope (full/partial) | ☐ |
| 3 | Notify stakeholders | ☐ |
| 4 | Document reason for rollback | ☐ |
| 5 | Verify backup exists and is valid | ☐ |

---

## Rollback Execution Steps

### Phase 1: Stop Services

| Step | Action | Status |
|------|--------|--------|
| 1.1 | Stop application services | ☐ |
| 1.2 | Verify no active connections | ☐ |
| 1.3 | Confirm services stopped | ☐ |

### Phase 2: Database Rollback

| Step | Action | Status |
|------|--------|--------|
| 2.1 | Locate pre-deployment backup | ☐ |
| 2.2 | Verify backup integrity | ☐ |
| 2.3 | Create current state backup (for forensics) | ☐ |
| 2.4 | Restore database from backup | ☐ |
| 2.5 | Verify restored database integrity | ☐ |
| 2.6 | Verify schema version | ☐ |
| 2.7 | Verify data integrity | ☐ |

### Phase 3: Application Rollback

| Step | Action | Status |
|------|--------|--------|
| 3.1 | Deploy previous version (v1.1.0) | ☐ |
| 3.2 | Restore previous configuration | ☐ |
| 3.3 | Verify configuration | ☐ |
| 3.4 | Start application services | ☐ |

### Phase 4: Post-Rollback Verification

| Step | Action | Status |
|------|--------|--------|
| 4.1 | Health check endpoint | ☐ |
| 4.2 | Authentication test | ☐ |
| 4.3 | Receipt CRUD test | ☐ |
| 4.4 | User management test | ☐ |
| 4.5 | Verify no data loss | ☐ |
| 4.6 | Verify audit trail intact | ☐ |

---

## Rollback Verification Checklist

| Check | Status |
|-------|--------|
| Application running on previous version | ☐ |
| Database restored to pre-deployment state | ☐ |
| All users can authenticate | ☐ |
| Receipts are accessible | ☐ |
| No data loss detected | ☐ |
| Audit trail intact | ☐ |
| Sync service operational | ☐ |
| Error rate returned to baseline | ☐ |

---

## Post-Rollback Actions

| Step | Action | Status |
|------|--------|--------|
| 1 | Notify stakeholders of rollback | ☐ |
| 2 | Document root cause | ☐ |
| 3 | Create incident report | ☐ |
| 4 | Schedule post-mortem | ☐ |
| 5 | Plan remediation | ☐ |
| 6 | Update release notes | ☐ |

---

## Rollback Log

| Field | Value |
|-------|-------|
| Rollback initiated by | _________________ |
| Date/Time | _________________ |
| Reason | _________________ |
| Scope | ☐ Full / ☐ Partial |
| Backup used | _________________ |
| Duration | _________________ |
| Data loss | ☐ None / ☐ Partial / ☐ Full |
| Services affected | _________________ |

---

## Recovery Path

If rollback fails:

1. **Immediate:** Contact DBA for manual database recovery
2. **Short-term:** Restore from off-site backup
3. **Long-term:** Engage disaster recovery team

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Incident Commander | _________________ | __________ | ☐ APPROVED |
| DBA | _________________ | __________ | ☐ APPROVED |
| Operations Lead | _________________ | __________ | ☐ APPROVED |

---

**END OF ROLLBACK CHECKLIST**
