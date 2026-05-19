from lab_system.app.database.db import get_conn

def seed_organizations(total=35):
    with get_conn() as conn:
        c = conn.execute('SELECT COUNT(*) c FROM organizations').fetchone()['c']
        if c >= total:
            return
        for i in range(1,total+1):
            conn.execute('INSERT OR IGNORE INTO organizations(name,code,address,phone,email) VALUES(?,?,?,?,?)',
                         (f'مؤسسة صحية {i:02d}', f'IQH-{i:03d}', 'Baghdad', '+964', f'org{i}@gov.iq'))
