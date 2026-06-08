# DEFECT_REPORT.md — Verified Defects
## Release v1.1.0 — Receipt-and-delivery

---

## Defect Summary

| Total | Critical | High | Medium | Low | Fixed |
|-------|----------|------|--------|-----|-------|
| 5 | 2 | 0 | 2 | 1 | 5 |

---

## DEF-001: Missing PageHeader Import in users_page.py

| Field | Value |
|-------|-------|
| **ID** | DEF-001 / PILOT-001 |
| **Severity** | ⚫ **Critical** |
| **Status** | ✅ **Fixed** |
| **Fixed in** | `c69cd4e` |

### Description
`users_page.py` uses `PageHeader` class on line 51 but never imports it. This causes a `NameError: name 'PageHeader' is not defined` at runtime when the Users page is instantiated.

### Root Cause
During the PageHeader standardization refactoring, the `from lab_system.app.ui.page_header import PageHeader` import was not added to `users_page.py`.

### Reproduction
1. Launch application
2. Navigate to "المستخدمون" (Users) page
3. Observe `NameError: name 'PageHeader' is not defined`

### Fix
Added import statement: `from lab_system.app.ui.page_header import PageHeader`

### Affected Code
```python
# lab_system/app/ui/users_page.py:51
header = PageHeader("إدارة المستخدمين والصلاحيات", "إضافة وتعديل وإدارة المستخدمين")
```

### Verification
- ✅ `python3 -c "from lab_system.app.ui.users_page import UsersPage"` — no error
- ✅ `ruff check lab_system/` — all checks pass
- ✅ All 156 unit tests pass

---

## DEF-002: Undefined Variable `s` in Chevron Icon Functions

| Field | Value |
|-------|-------|
| **ID** | DEF-002 / PILOT-002 |
| **Severity** | ⚫ **Critical** |
| **Status** | ✅ **Fixed** |
| **Fixed in** | `c69cd4e` |

### Description
Both `icon_chevron_left()` and `icon_chevron_right()` in `icons.py` reference the variable `s` in the `size=s` argument to `_paint_icon()`. However, `s` is only defined as a parameter of the inner `draw(p, s)` closure, not in the outer function scope. This causes a `NameError` at runtime when these icon functions are called.

### Root Cause
The `size=s` keyword argument tries to capture `s` from the enclosing scope, but `s` only exists inside the `draw` closure.

### Reproduction
```python
from lab_system.app.ui.icons import icon_chevron_left
icon_chevron_left()  # NameError: name 's' is not defined
```

### Fix
Removed `size=s` from both `_paint_icon()` calls. The default size parameter (24) is used automatically.

```python
# Before
return _paint_icon(draw, size=s, color=color)

# After  
return _paint_icon(draw, color=color)
```

### Verification
- ✅ `python3 -c "from lab_system.app.ui.icons import icon_chevron_left, icon_chevron_right"` — no error
- ✅ `ruff check lab_system/` — all checks pass
- ✅ All 156 unit tests pass

---

## DEF-003: Unused Imports Across 7 Files (19 occurrences)

| Field | Value |
|-------|-------|
| **ID** | DEF-003 |
| **Severity** | 🟡 **Medium** |
| **Status** | ✅ **Fixed** |
| **Fixed in** | `c69cd4e` (auto-fixed via `ruff --fix`) |

### Files Affected

| File | Unused Import |
|------|---------------|
| `backup_page.py` | `QLabel` |
| `notifications.py` | `QPoint`, `QWidget`, `THEME` |
| `receipt_dialog.py` | `QLabel` |
| `receipts_page.py` | `toast` |
| `settings_page.py` | `QLabel`, `QMessageBox`, `QPushButton` |
| `sidebar.py` | `QRect`, `QTimer`, `QIcon`, `QHBoxLayout`, `QLabel`, `QPushButton`, `icon_chevron_left`, `icon_chevron_right` |
| `users_page.py` | `QLabel` |

Plus: `sidebar.py` — f-string without placeholders (line 311)

### Impact
No runtime impact but increases module load time and clutters code.

### Fix
All 19 issues auto-fixed by `ruff check --fix`. One additional manual fix for the f-string.

### Verification
- ✅ `ruff check lab_system/ --select E,F,W` — 0 errors

---

## DEF-004: Unused Variable `total` in reports_page.py

| Field | Value |
|-------|-------|
| **ID** | DEF-004 |
| **Severity** | 🟡 **Medium** |
| **Status** | ✅ **Fixed** |
| **Fixed in** | `c69cd4e` |

### Description
In `reports_page.py:136`, variable `total` is assigned but never used.

### Fix
Removed the assignment: `total = sum(summary["by_status"].values())`

### Verification
- ✅ `ruff check lab_system/` — 0 errors

---

## DEF-005: Unused Variable `refresh_btn` in audit_page.py

| Field | Value |
|-------|-------|
| **ID** | DEF-005 |
| **Severity** | 🟢 **Low** |
| **Status** | ✅ **Fixed** |
| **Fixed in** | `c69cd4e` |

### Description
In `audit_page.py:24`, variable `refresh_btn` is assigned the return value of `add_action()` but never used.

### Fix
Removed the assignment — changed to bare `header.add_action(...)`.

### Verification
- ✅ `ruff check lab_system/` — 0 errors

---

## Regression Verification

After all fixes applied:

| Check | Result |
|-------|--------|
| `ruff check lab_system/ --select E,F,W` | ✅ 0 errors |
| `pytest tests/ -q` | ✅ 156/156 passed |
| `python3 -c "from lab_system.app.ui import *"` | ✅ No import errors |
| `frontend npm run build` | ✅ 14 PWA entries |

---

## Non-Defects (Intentional)

The following items were investigated and determined to be **not defects**:

| Item | Rationale |
|------|-----------|
| QMessageBox.warning used instead of toast for confirmations | Intentional — confirmations require user decision (Yes/No) |
| Bandit medium-severity SQL warnings | False positives — all queries use parameterized statements |
| Hard-coded colors in UI code | Intentional — THEME dict used where dynamic; static colors for specific UI states |

---

**Report Date:** June 8, 2026  
**Total Defects Found:** 5  
**Total Defects Fixed:** 5  
**Remaining:** 0
