from functools import wraps

from lab_system.app.utils.errors import AuthorizationError

ROLE_PERMISSIONS = {
    'Admin': {
        'dashboard.view',
        'receipts.create', 'receipts.read', 'receipts.update', 'receipts.delete',
        'receipts.approve', 'receipts.reject', 'receipts.archive', 'receipts.cancel',
        'organizations.create', 'organizations.read', 'organizations.update', 'organizations.delete',
        'users.create', 'users.read', 'users.update', 'users.delete',
        'users.reset_password',
        'settings.read', 'settings.update',
        'reports.read', 'reports.export',
        'audit.read',
        'backup.create', 'backup.restore', 'backup.delete', 'backup.verify',
    },
    'Supervisor': {
        'dashboard.view',
        'receipts.create', 'receipts.read', 'receipts.update',
        'receipts.approve', 'receipts.reject', 'receipts.archive', 'receipts.cancel',
        'organizations.read', 'organizations.update',
        'users.read',
        'settings.read',
        'reports.read', 'reports.export',
        'audit.read',
        'backup.create', 'backup.verify',
    },
    'User': {
        'dashboard.view',
        'receipts.create', 'receipts.read',
        'organizations.read',
        'reports.read',
    },
    'Auditor': {
        'dashboard.view',
        'receipts.read',
        'organizations.read',
        'users.read',
        'reports.read',
        'audit.read',
    },
}


def require_permission(role: str, permission: str) -> None:
    allowed = ROLE_PERMISSIONS.get(role, set())
    if permission not in allowed:
        raise AuthorizationError('غير مصرح لك بهذا الإجراء')


def check_permission(user: dict, permission: str) -> None:
    require_permission(user.get('role', ''), permission)


def with_permission(permission: str):
    """Decorator: enforces permission if `user` kwarg is provided (defense-in-depth).

    Usage:
        @with_permission('users.create')
        def create_user(full_name, username, password, role, user=None):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('user')
            if user is not None:
                check_permission(user, permission)
            return func(*args, **kwargs)
        return wrapper
    return decorator
