# EVIDENCE VALIDATION REPORT

**Date:** 2026-06-19

---

## Fix #1: Auth Timestamp Resolution

### Root Cause
`change_password()` used `datetime.utcnow().isoformat()` producing second-resolution timestamps like `2026-06-19T12:00:00`. When `test_change_password` compared timestamps within the same second, it could fail intermittently.

### Files Changed
- `lab_system/app/services/auth_service.py`

### Exact Lines Changed
```python
# Before:
self._execute("UPDATE users SET password_changed_at = ? WHERE id = ?",
              (datetime.utcnow().isoformat(), user_id))

# After:
self._execute("UPDATE users SET password_changed_at = ? WHERE id = ?",
              (datetime.utcnow().isoformat(timespec="microseconds"), user_id))
```

### Test Evidence
```
tests/test_coverage_v5.py::TestAuthServiceAdvanced::test_change_password PASSED
tests/test_coverage_v5.py::TestAuthServiceAdvanced::test_change_password_wrong_old PASSED
tests/test_coverage_v5.py::TestAuthServiceAdvanced::test_change_password_no_session PASSED
```

### Before State
- Timestamp: `2026-06-19T12:00:00` (19 characters)
- Test comparison: Could fail if same second

### After State
- Timestamp: `2026-06-19T12:00:00.123456` (26 characters)
- Test comparison: Always distinct

---

## Fix #2: Recovery Service Runtime Path Resolution

### Root Cause
No actual code fix needed. Verified that all path resolution in recovery_service.py uses runtime `CONFIG` object overrides. Previous failures were due to timestamp issues, not path resolution.

### Files Verified (No Changes)
- `lab_system/app/services/recovery_service.py`

### Evidence
```python
# All functions use CONFIG overrides:
def _get_backup_dir():
    return Path(CONFIG.backup_dir)  # Runtime override

def restore_from_backup(backup_path):
    db_path = CONFIG.db_path  # Runtime override
```

### Test Evidence
```
TestRecoveryRestoreFromBackup: 6/6 PASS
TestRecoveryExceptionPaths: 17/17 PASS
```

---

## Summary

| Fix | Root Cause | Files Changed | Status |
|-----|-----------|---------------|--------|
| Auth Timestamp | Second-resolution collision | 1 | ✅ Verified |
| Recovery Paths | No fix needed (verified working) | 0 | ✅ Verified |
