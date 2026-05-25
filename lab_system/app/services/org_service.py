from lab_system.app.database.db import get_conn


def list_organizations(active_only=False):
    with get_conn() as conn:
        if active_only:
            return conn.execute("SELECT * FROM organizations WHERE status='Active' ORDER BY name").fetchall()
        return conn.execute('SELECT * FROM organizations ORDER BY name').fetchall()


def upsert_organization(payload):
    with get_conn() as conn:
        if payload.get('id'):
            conn.execute('''UPDATE organizations SET name=?,code=?,org_type=?,governorate=?,address=?,phone=?,email=?,logo_path=?,notes=?,status=? WHERE id=?''',
                         (payload['name'], payload['code'], payload['org_type'], payload['governorate'], payload['address'], payload['phone'], payload['email'], payload['logo_path'], payload['notes'], payload['status'], payload['id']))
        else:
            conn.execute('''INSERT INTO organizations(name,code,org_type,governorate,address,phone,email,logo_path,notes,status) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                         (payload['name'], payload['code'], payload['org_type'], payload['governorate'], payload['address'], payload['phone'], payload['email'], payload['logo_path'], payload['notes'], payload['status']))
