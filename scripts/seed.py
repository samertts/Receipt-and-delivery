"""
Seed script for the Lab Receipt & Delivery Management System.
Populates the database with default admin user and Iraqi health organizations.

Usage:
    python scripts/seed.py                     # Default: seeds DB via SQLAlchemy
    python scripts/seed.py --desktop           # Seeds the desktop app SQLite DB
"""

import os
import sys

from app.core.logging import setup_logging
from app.db.session import SessionLocal, init_db
from app.models.organization import Organization
from app.models.user import User
from app.services.security import hash_password

setup_logging()

ORG_NAMES = [
    "مختبر بغداد المركزي",
    "مختبر الكرخ",
    "مختبر الرصافة",
    "مختبر الموصل",
    "مختبر البصرة",
    "مختبر أربيل",
    "مختبر كركوك",
    "مختبر النجف",
    "مختبر كربلاء",
    "مختبر السليمانية",
    "مختبر دهوك",
    "مختبر الحلة",
    "مختبر العمارة",
    "مختبر الديوانية",
    "مختبر الكوت",
    "مختبر تكريت",
    "مختبر الرمادي",
    "مختبر السماوة",
    "مختبر الناصرية",
    "مختبر بابل",
    "مختبر واسط",
    "مختبر ذي قار",
    "مختبر المثنى",
    "مختبر القادسية",
    "مختبر ميسان",
    "مختبر صلاح الدين",
    "مختبر الأنبار",
    "مختبر نينوى",
    "مختبر تأميم",
    "مختبر حلبجة",
    "مختبر كركوك الصحي",
    "مختبر البصرة المركزي",
    "مختبر الموصل المركزي",
    "مختبر الفرات الأوسط",
    "مختبر بغداد الدولي",
]

GOVERNORATES = [
    "بغداد",
    "بغداد",
    "بغداد",
    "نينوى",
    "البصرة",
    "أربيل",
    "كركوك",
    "النجف",
    "كربلاء",
    "السليمانية",
    "دهوك",
    "بابل",
    "ميسان",
    "القادسية",
    "واسط",
    "صلاح الدين",
    "الأنبار",
    "المثنى",
    "ذي قار",
    "بابل",
    "واسط",
    "ذي قار",
    "المثنى",
    "القادسية",
    "ميسان",
    "صلاح الدين",
    "الأنبار",
    "نينوى",
    "كركوك",
    "حلبجة",
    "كركوك",
    "البصرة",
    "نينوى",
    "النجف",
    "بغداد",
]


def seed_organizations(db):
    count = 0
    for i, name in enumerate(ORG_NAMES):
        code = f"IQH-{i + 1:03d}"
        existing = db.query(Organization).filter(Organization.code == code).first()
        if not existing:
            org = Organization(
                name=name,
                code=code,
                org_type="Public Health Laboratory",
                governorate=GOVERNORATES[i] if i < len(GOVERNORATES) else "",
                address=GOVERNORATES[i] if i < len(GOVERNORATES) else "",
                phone="+964",
                email=f"lab{i + 1:02d}@moh.gov.iq",
                status="active",
            )
            db.add(org)
            count += 1
    db.commit()
    return count


def seed_admin(db):
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        user = User(
            username="admin",
            full_name="مدير النظام",
            password_hash=hash_password(
                os.environ.get("LAB_ADMIN_PASSWORD", os.urandom(16).hex())
            ),
            role="admin",
            status="active",
        )
        db.add(user)
        db.commit()
        return 1
    return 0


def seed_desktop():
    """Seed the desktop app SQLite database."""
    from lab_system.app.services.catalog_service import seed_defaults
    from lab_system.app.services.seed_service import seed_organizations as seed_orgs
    from lab_system.app.services.user_service import seed_default_users

    seed_default_users()
    seed_orgs()
    seed_defaults()
    print("Desktop database seeded successfully.")


def main():
    if "--desktop" in sys.argv:
        seed_desktop()
        return

    print(f"Seeding {len(ORG_NAMES)} Iraqi health organizations...")
    init_db()
    db = SessionLocal()
    try:
        org_count = seed_organizations(db)
        user_count = seed_admin(db)
        print(f"Seeded: {org_count} organizations, {user_count} admin user(s)")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
