from __future__ import annotations

from typing import Any

from lab_system.app.database.db import get_conn
from lab_system.app.utils.errors import ValidationError

VALID_ORG_STATUS = {'Active', 'Inactive', 'Archived'}


def _validate(payload: dict[str, Any]) -> None:
    if not payload.get('name', '').strip():
        raise ValidationError('اسم المؤسسة مطلوب')
    if not payload.get('code', '').strip():
        raise ValidationError('رمز المؤسسة مطلوب')
    if payload.get('status', 'Active') not in VALID_ORG_STATUS:
        raise ValidationError('حالة المؤسسة غير صالحة')


def list_organizations(active_only: bool = False):
    with get_conn() as conn:
        if active_only:
            return conn.execute("SELECT * FROM organizations WHERE status='Active' ORDER BY name").fetchall()
        return conn.execute('SELECT * FROM organizations WHERE status <> "Archived" ORDER BY name').fetchall()


def search_organizations(q: str = '', status: str = ''):
    q = q.strip()
    where = ['status <> "Archived"']
    params = []
    if q:
        where.append('(name LIKE ? OR code LIKE ? OR governorate LIKE ?)')
        like = f'%{q}%'
        params.extend([like, like, like])
    if status:
        where.append('status = ?')
        params.append(status)
    sql = f'SELECT * FROM organizations WHERE {" AND ".join(where)} ORDER BY name'
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def upsert_organization(payload: dict[str, Any]):
    _validate(payload)
    with get_conn() as conn:
        if payload.get('id'):
            conn.execute(
                '''UPDATE organizations
                   SET name=?,code=?,org_type=?,governorate=?,address=?,phone=?,email=?,logo_path=?,notes=?,status=?
                   WHERE id=?''',
                (
                    payload['name'].strip(), payload['code'].strip(), payload.get('org_type', 'Other'), payload.get('governorate', ''),
                    payload.get('address', ''), payload.get('phone', ''), payload.get('email', ''), payload.get('logo_path', ''),
                    payload.get('notes', ''), payload.get('status', 'Active'), payload['id'],
                ),
            )
            return payload['id']
        cur = conn.execute(
            '''INSERT INTO organizations(name,code,org_type,governorate,address,phone,email,logo_path,notes,status)
               VALUES(?,?,?,?,?,?,?,?,?,?)''',
            (
                payload['name'].strip(), payload['code'].strip(), payload.get('org_type', 'Other'), payload.get('governorate', ''),
                payload.get('address', ''), payload.get('phone', ''), payload.get('email', ''), payload.get('logo_path', ''),
                payload.get('notes', ''), payload.get('status', 'Active'),
            ),
        )
        return cur.lastrowid


def set_organization_status(org_id: int, status: str):
    if status not in VALID_ORG_STATUS:
        raise ValidationError('حالة المؤسسة غير صالحة')
    with get_conn() as conn:
        conn.execute('UPDATE organizations SET status=? WHERE id=?', (status, org_id))
