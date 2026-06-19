# RBAC Regression Report

**Date:** 2026-06-19

---

## Root Cause

The `@with_permission` decorator in `lab_system/app/auth/permissions.py` was changed from fail-open to fail-closed:

**Before (fail-open):**
```python
def wrapper(*args, **kwargs):
    user = kwargs.get('user')
    if user is None:
        return func(*args, **kwargs)  # pass through
    check_permission(user, permission)
    return func(*args, **kwargs)
```

**After (fail-closed):**
```python
def wrapper(*args, **kwargs):
    user = kwargs.get('user')
    if user is None:
        raise AuthorizationError('غير مصرح لك بهذا الإجراء')
    check_permission(user, permission)
    return func(*args, **kwargs)
```

This is the **correct security behavior** - fail-closed prevents unauthorized access.

---

## Affected Functions

| Module | Function | Permission |
|--------|----------|------------|
| receipt_service | create_receipt | receipts.create |
| receipt_service | update_receipt | receipts.update |
| receipt_service | soft_delete_receipt | receipts.delete |
| receipt_service | hard_delete_receipt | receipts.delete |
| receipt_service | restore_receipt | receipts.restore |
| receipt_service | change_receipt_status | receipts.update |
| receipt_service | set_receipt_status | receipts.update |
| user_service | create_user | users.create |
| user_service | disable_user | users.update |
| user_service | enable_user | users.update |
| user_service | reset_password | users.reset_password |
| org_service | upsert_organization | organizations.update |
| backup_service | create_backup | backup.create |
| recovery_service | restore_from_backup | backup.restore |
| recovery_service | delete_backup | backup.delete |
| recovery_service | validate_recovery | backup.verify |

---

## Fix Applied

### 1. Source Code Fixes

Added `user=None` parameter to helper functions that forward to `@with_permission` decorated functions:

```python
# Before
def approve_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Approved', user_id)

# After
def approve_receipt(receipt_id, user_id=None, user=None):
    return change_receipt_status(receipt_id, 'Approved', user_id, user=user)
```

Functions updated:
- `approve_receipt`
- `reject_receipt`
- `archive_receipt`
- `unarchive_receipt`
- `cancel_receipt`
- `batch_update_status`
- `batch_soft_delete`

### 2. Automated Operations

`auto_backup` and `enforce_retention` now use a system user:

```python
_system_user = {"id": 0, "username": "system", "role": "Admin", "status": "Active"}
```

### 3. Test Fixes

All test files updated with `ADMIN_USER` fixture:

```python
ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}
```

All calls updated to pass `user=ADMIN_USER`.

---

## Verification

| Test File | Tests | Before | After |
|-----------|-------|--------|-------|
| test_workflow.py | 28 | 16 failed | 0 failed |
| test_desktop_services.py | 13 | 9 failed | 0 failed |
| test_security.py | 17 | 2 failed | 0 failed |
| test_auth_advanced.py | 19 | 1 failed | 0 failed |
| test_desktop_models.py | 3 | 1 failed | 0 failed |
| test_database.py | 14 | 1 failed | 0 failed |
| **Total** | **94** | **30 failed** | **0 failed** |
