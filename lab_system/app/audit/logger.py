from datetime import datetime
import platform
from lab_system.app.database.db import get_conn

def log_action(user_id, action, details=''):
    with get_conn() as conn:
        conn.execute('INSERT INTO audit_logs(user_id,action,machine_name,timestamp,details) VALUES(?,?,?,?,?)',
                     (user_id, action, platform.node(), datetime.now().isoformat(timespec='seconds'), details))
