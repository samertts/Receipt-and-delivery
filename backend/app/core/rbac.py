from __future__ import annotations

PERMISSION_ROLES: dict[str, tuple[str, ...]] = {
    "view_dashboard": ("admin", "supervisor", "user", "auditor"),
    "view_transactions": ("admin", "supervisor", "user", "auditor"),
    "create_transaction": ("admin", "supervisor", "user"),
    "edit_transaction": ("admin", "supervisor"),
    "delete_transaction": ("admin",),
    "manage_users": ("admin",),
    "view_users": ("admin", "supervisor"),
    "view_audit_logs": ("admin", "auditor"),
    "manage_organizations": ("admin", "supervisor"),
    "view_organizations": ("admin", "supervisor", "user", "auditor"),
    "view_reports": ("admin", "supervisor"),
    "manage_settings": ("admin",),
    "manage_backups": ("admin",),
    "sync_data": ("admin",),
}

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    role: tuple(sorted(permission for permission, roles in PERMISSION_ROLES.items() if role in roles))
    for role in ("admin", "supervisor", "user", "auditor")
}

ROLES = tuple(ROLE_PERMISSIONS)


def permissions_for_role(role: str) -> list[str]:
    return list(ROLE_PERMISSIONS.get(role, ()))


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, ())
