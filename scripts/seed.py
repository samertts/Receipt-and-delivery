from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.services.security import hash_password

orgs = [
    {"name": f"مؤسسة صحية {i}", "code": f"ORG{i:03}", "address": "بغداد", "phone": "07700000000", "email": f"org{i}@lab.iq", "logo_path": ""}
    for i in range(1, 36)
]

db = SessionLocal()
for org in orgs:
    db.add(Organization(**org))
db.add(User(username="admin", full_name="System Admin", password_hash=hash_password("Admin@123"), role="admin"))
db.commit()
print("Seed complete")
