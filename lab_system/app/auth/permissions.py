from lab_system.app.utils.errors import AuthorizationError

ROLE_PERMISSIONS = {
    'Admin': {'manage_users', 'view_dashboard', 'view_settings'},
    'Supervisor': {'view_dashboard'},
    'User': {'view_dashboard'},
    'Auditor': {'view_dashboard'},
}


def require_permission(role: str, permission: str) -> None:
    allowed = ROLE_PERMISSIONS.get(role, set())
    if permission not in allowed:
        raise AuthorizationError('غير مصرح لك بهذا الإجراء')
