"""Tests for org_service.py — Organization management."""

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestOrgService:
    def test_list_organizations_empty(self, fresh_db):
        from lab_system.app.services.org_service import list_organizations

        result = list_organizations()
        assert len(result) == 0

    def test_list_organizations_with_data(self, fresh_db, seed_data):
        from lab_system.app.services.org_service import list_organizations

        result = list_organizations()
        assert len(result) >= 1

    def test_list_organizations_active_only(self, fresh_db, seed_data):
        from lab_system.app.services.org_service import list_organizations

        result = list_organizations(active_only=True)
        assert all(r["status"] == "Active" for r in result)

    def test_upsert_organization_create(self, fresh_db, seed_data):
        from lab_system.app.services.org_service import upsert_organization

        payload = {
            "name": "New Lab",
            "code": "NL001",
            "org_type": "Laboratory",
            "governorate": "Basra",
            "address": "Test Address",
            "phone": "0770000001",
            "email": "new@lab.com",
            "logo_path": "",
            "notes": "",
            "status": "Active",
        }
        upsert_organization(payload, user=ADMIN_USER)
        from lab_system.app.services.org_service import list_organizations
        result = list_organizations()
        names = [r["name"] for r in result]
        assert "New Lab" in names

    def test_upsert_organization_update(self, fresh_db, seed_data):
        from lab_system.app.services.org_service import list_organizations, upsert_organization

        existing = list_organizations()
        assert len(existing) >= 1
        org = dict(existing[0])

        org["name"] = "Updated Lab"
        upsert_organization(org, user=ADMIN_USER)

        updated = list_organizations()
        names = [r["name"] for r in updated]
        assert "Updated Lab" in names
