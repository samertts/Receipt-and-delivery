"""
Platform Core — Reporting Service

Unified reporting with shared generation logic.
Extracted from: lab_system/app/services/report_service.py
"""

from __future__ import annotations

from typing import Any

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus


class ReportingService(PlatformService):
    """Unified reporting service."""

    @property
    def service_name(self) -> str:
        return "platform.reporting"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def receipt_summary(self, date_from: str = "", date_to: str = "", conn=None) -> dict[str, Any]:
        """Generate receipt summary report."""
        ...

    def daily_report(self, date: str = "", conn=None) -> dict[str, Any]:
        """Generate daily report."""
        ...

    def monthly_report(self, year: int = 0, month: int = 0, conn=None) -> dict[str, Any]:
        """Generate monthly report."""
        ...

    def institution_stats(self, conn=None) -> list[dict[str, Any]]:
        """Generate institution statistics."""
        ...

    def rejection_stats(self, date_from: str = "", date_to: str = "", conn=None) -> dict[str, Any]:
        """Generate rejection statistics."""
        ...

    def damage_stats(self, date_from: str = "", date_to: str = "", conn=None) -> dict[str, Any]:
        """Generate damage statistics."""
        ...

    def sample_summary(self, conn=None) -> list[dict[str, Any]]:
        """Generate sample type summary."""
        ...

    def export_csv(self, data: list[dict[str, Any]], filename: str) -> str:
        """Export data to CSV file."""
        ...

    def export_xlsx(self, data: list[dict[str, Any]], filename: str) -> str:
        """Export data to XLSX file."""
        ...

    def export_pdf(self, data: dict[str, Any], filename: str) -> str:
        """Export report to PDF file."""
        ...

    def governorate_report(self, governorate: str, conn=None) -> dict[str, Any]:
        """Generate governorate-level report."""
        ...

    def national_aggregate(self, conn=None) -> dict[str, Any]:
        """Generate national-level aggregate report."""
        ...
