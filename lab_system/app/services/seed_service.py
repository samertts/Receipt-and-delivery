from lab_system.app.database.db import get_conn


def seed_organizations(total=35):
    with get_conn() as conn:
        for i in range(1, total + 1):
            conn.execute('''INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,address,phone,email,status)
                VALUES(?,?,?,?,?,?,?,?)''', (f'مؤسسة صحية {i:02d}', f'IQH-{i:03d}', 'Public Health Laboratory', 'Baghdad', 'Baghdad', '+964', f'org{i}@gov.iq', 'Active'))
