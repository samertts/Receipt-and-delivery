from lab_system.app.database import db as _db


def seed_defaults():
    tx = ["Sample Receipt", "Sample Delivery", "Referral Transfer", "Material Transfer"]
    sm = ["Serum", "EDTA", "Urine", "Swab", "Tissue", "Blood", "Plasma", "CSF"]
    with _db.get_conn() as conn:
        for t in tx:
            conn.execute(
                "INSERT OR IGNORE INTO transaction_types(name,is_active) VALUES(?,1)",
                (t,),
            )
        for s in sm:
            conn.execute(
                "INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?, 'General', 'Active')",
                (s,),
            )


def list_transaction_types():
    with _db.get_conn() as conn:
        return conn.execute(
            "SELECT * FROM transaction_types WHERE is_active=1 ORDER BY name"
        ).fetchall()


def list_sample_types():
    with _db.get_conn() as conn:
        return conn.execute(
            "SELECT * FROM sample_types WHERE status='Active' ORDER BY name"
        ).fetchall()
