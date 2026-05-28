from lab_system.app.database import db as _db
from lab_system.app.auth.security import hash_password, verify_password


def seed_default_users():
    created = False
    with _db.get_conn() as conn:
        if conn.execute('SELECT COUNT(*) c FROM users').fetchone()['c'] == 0:
            conn.execute('INSERT INTO users(full_name,username,password_hash,role,status) VALUES(?,?,?,?,?)',
                         ('System Admin', 'admin', hash_password('Admin@123'), 'Admin', 'Active'))
            created = True
    if created:
        from lab_system.app.audit.logger import log_action
        log_action(None, 'admin_seeded', 'Default admin account created on first startup')


def authenticate(username, password):
    with _db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=? AND status='Active'", (username,)).fetchone()
    return row if row and verify_password(password, row['password_hash']) else None


def list_users():
    with _db.get_conn() as conn:
        return conn.execute('SELECT u.*, o.name institution_name FROM users u LEFT JOIN organizations o ON o.id=u.institution_id ORDER BY u.id DESC').fetchall()


def create_user(full_name, username, password, role, institution_id=None, phone='', notes=''):
    with _db.get_conn() as conn:
        conn.execute('INSERT INTO users(full_name,username,password_hash,role,institution_id,phone,notes,status) VALUES(?,?,?,?,?,?,?,?)',
                     (full_name, username, hash_password(password), role, institution_id, phone, notes, 'Active'))


def disable_user(user_id):
    with _db.get_conn() as conn:
        conn.execute("UPDATE users SET status='Inactive' WHERE id=?", (user_id,))


def reset_password(user_id, new_password):
    with _db.get_conn() as conn:
        conn.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(new_password), user_id))
