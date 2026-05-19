from lab_system.app.database.db import get_conn
from lab_system.app.auth.security import hash_password, verify_password

def seed_default_users():
    with get_conn() as conn:
        c = conn.execute("SELECT COUNT(*) c FROM users").fetchone()['c']
        if c == 0:
            conn.execute('INSERT INTO users(username,full_name,password_hash,role) VALUES(?,?,?,?)',
                         ('admin','System Admin',hash_password('Admin@123'),'Admin'))

def authenticate(username, password):
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM users WHERE username=? AND active=1',(username,)).fetchone()
    if not row:
        return None
    return row if verify_password(password, row['password_hash']) else None
