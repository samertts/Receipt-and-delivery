"""Tests for dashboard_service.py — Dashboard statistics."""

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestDashboardService:
    def test_get_stats_empty_db(self, fresh_db):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        stats = svc.get_stats()
        assert stats["total"] == 0
        assert stats["today_count"] == 0
        assert stats["week_count"] == 0
        assert stats["month_count"] == 0
        assert stats["pending"] == 0
        assert stats["completed"] == 0
        assert stats["org_count"] == 0
        assert stats["user_count"] == 0

    def test_get_stats_with_seed(self, fresh_db, seed_data):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        stats = svc.get_stats()
        assert stats["user_count"] >= 2
        assert stats["org_count"] >= 1

    def test_get_recent_activity_empty(self, fresh_db):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        activity = svc.get_recent_activity()
        assert isinstance(activity, list)
        assert len(activity) == 0

    def test_get_recent_activity_with_limit(self, fresh_db):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        activity = svc.get_recent_activity(limit=5)
        assert isinstance(activity, list)

    def test_get_recent_backups_empty(self, fresh_db):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        backups = svc.get_recent_backups()
        assert isinstance(backups, list)
        assert len(backups) == 0

    def test_get_recent_backups_with_limit(self, fresh_db):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        backups = svc.get_recent_backups(limit=3)
        assert isinstance(backups, list)
