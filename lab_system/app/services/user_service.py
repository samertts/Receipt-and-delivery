from datetime import datetime, timedelta
from lab_system.app.database import db as _db
from lab_system.app.auth.security import hash_password, verify_password
from lab_system.app.utils.errors import AuthenticationError


def seed_default_users():
    created = False
    with _db.get_conn() as conn:
        if conn.execute('SELECT COUNT(*) c FROM users').fetchone()['c'] == 0:
            now = datetime.now().isoformat(timespec='seconds')
            conn.execute('INSERT INTO users(full_name,username,password_hash,role,status,password_changed_at) VALUES(?,?,?,?,?,?)',
                         ('System Admin', 'admin', hash_password('Admin@123'), 'Admin', 'Active', now))
            created = True
    if created:
        from lab_system.app.audit.logger import log_action
        log_action(None, 'admin_seeded', 'Default admin account created on first startup')
    return created


def record_login_attempt(username, success):
    with _db.get_conn() as conn:
        conn.execute('INSERT INTO login_attempts(username,success,attempted_at) VALUES(?,?,?)',
                     (username, 1 if success else 0, datetime.now().isoformat(timespec='seconds')))


def get_recent_failures(username, minutes=5):
    since = (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec='seconds')
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) c FROM login_attempts WHERE username=? AND success=0 AND attempted_at>=?",
            (username, since),
        ).fetchone()
    return row['c'] if row else 0


def authenticate(username, password):
    with _db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=? AND status='Active'", (username,)).fetchone()
    if row and verify_password(password, row['password_hash']):
        record_login_attempt(username, True)
        return row
    record_login_attempt(username, False)
    return None


def needs_password_change(user):
    changed_at = user.get('password_changed_at') or ''
    return len(changed_at) == 0


def change_password(user_id, old_password, new_password):
    with _db.get_conn() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
        if not row or not verify_password(old_password, row['password_hash']):
            raise AuthenticationError('كلمة المرور الحالية غير صحيحة')
        conn.execute('UPDATE users SET password_hash=?, password_changed_at=? WHERE id=?',
                     (hash_password(new_password), datetime.now().isoformat(timespec='seconds'), user_id))


def list_users():
    with _db.get_conn() as conn:
        return conn.execute('SELECT u.*, o.name institution_name FROM users u LEFT JOIN organizations o ON o.id=u.institution_id ORDER BY u.id DESC').fetchall()


def create_user(full_name, username, password, role, institution_id=None, phone='', notes=''):
    with _db.get_conn() as conn:
        conn.execute('INSERT INTO users(full_name,username,password_hash,role,institution_id,phone,notes,status,password_changed_at) VALUES(?,?,?,?,?,?,?,?,?)',
                     (full_name, username, hash_password(password), role, institution_id, phone, notes, 'Active', datetime.now().isoformat(timespec='seconds')))


def disable_user(user_id):
    with _db.get_conn() as conn:
        conn.execute("UPDATE users SET status='Inactive' WHERE id=?", (user_id,))


def reset_password(user_id, new_password):
    with _db.get_conn() as conn:
        conn.execute('UPDATE users SET password_hash=?, password_changed_at=? WHERE id=?',
                     (hash_password(new_password), datetime.now().isoformat(timespec='seconds'), user_id))
