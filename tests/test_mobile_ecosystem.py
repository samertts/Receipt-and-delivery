"""Tests for unified_platform/mobile/__init__.py — Mobile Ecosystem Readiness."""

import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unified_platform.mobile import (
    MobilePlatform,
    SyncMode,
    OfflineCapability,
    AndroidContract,
    TabletContract,
    OfflineContract,
    SyncContract,
    AttachmentContract,
    MobileAuthContract,
    MobileNotificationContract,
    MobileReadinessManager,
)


# ============================================================================
# TestMobileContracts
# ============================================================================


class TestMobileContracts:
    """Tests for all 7 mobile contract types."""

    def test_android_contract_defaults(self):
        c = AndroidContract()
        assert c.min_version == "1.0.0"
        assert c.max_version == ""
        assert c.api_base == "/api/v1"
        assert c.auth_method == "jwt"
        assert c.sync_mode == SyncMode.INCREMENTAL
        assert c.offline_capability == OfflineCapability.FULL
        assert "receipts" in c.supported_features
        assert "organizations" in c.supported_features
        assert "scan_qr" in c.supported_features
        assert c.push_notifications is True
        assert c.camera_integration is True
        assert c.barcode_scanning is True
        assert c.gps_location is False

    def test_android_contract_custom_values(self):
        c = AndroidContract(
            min_version="2.0.0",
            max_version="3.0.0",
            api_base="/api/v2",
            sync_mode=SyncMode.REALTIME,
            offline_capability=OfflineCapability.PARTIAL,
            gps_location=True,
        )
        assert c.min_version == "2.0.0"
        assert c.max_version == "3.0.0"
        assert c.sync_mode == SyncMode.REALTIME
        assert c.offline_capability == OfflineCapability.PARTIAL
        assert c.gps_location is True

    def test_tablet_contract_defaults(self):
        c = TabletContract()
        assert c.min_version == "1.0.0"
        assert c.api_base == "/api/v1"
        assert c.auth_method == "jwt"
        assert c.sync_mode == SyncMode.REALTIME
        assert c.offline_capability == OfflineCapability.FULL
        assert "dashboard" in c.supported_features
        assert "reports" in c.supported_features
        assert c.push_notifications is True
        assert c.camera_integration is True
        assert c.printer_support is True
        assert c.large_screen_optimized is True

    def test_tablet_contract_custom_values(self):
        c = TabletContract(
            min_version="1.5.0",
            sync_mode=SyncMode.INCREMENTAL,
            printer_support=False,
            large_screen_optimized=False,
        )
        assert c.min_version == "1.5.0"
        assert c.sync_mode == SyncMode.INCREMENTAL
        assert c.printer_support is False
        assert c.large_screen_optimized is False

    def test_offline_contract_defaults(self):
        c = OfflineContract()
        assert c.max_offline_hours == 72
        assert c.max_cached_records == 10000
        assert c.auto_sync_on_reconnect is True
        assert c.conflict_resolution == "last-writer-wins"
        assert c.offline_queue_limit == 500
        assert "create_receipt" in c.supported_operations
        assert "delete_receipt" in c.blocked_operations
        assert "receipts" in c.sync_priority

    def test_offline_contract_custom_values(self):
        c = OfflineContract(
            max_offline_hours=24,
            max_cached_records=5000,
            auto_sync_on_reconnect=False,
            conflict_resolution="manual",
        )
        assert c.max_offline_hours == 24
        assert c.max_cached_records == 5000
        assert c.auto_sync_on_reconnect is False
        assert c.conflict_resolution == "manual"

    def test_sync_contract_defaults(self):
        c = SyncContract()
        assert c.protocol == "rest"
        assert c.transport == "https"
        assert c.compression == "gzip"
        assert c.batch_size == 100
        assert c.max_payload_mb == 10
        assert c.retry_strategy == "exponential_backoff"
        assert c.max_retries == 5
        assert c.conflict_resolution == "last-writer-wins"
        assert c.incremental_sync is True
        assert c.delta_compression is True

    def test_sync_contract_custom_values(self):
        c = SyncContract(
            protocol="graphql",
            batch_size=200,
            max_retries=10,
            incremental_sync=False,
        )
        assert c.protocol == "graphql"
        assert c.batch_size == 200
        assert c.max_retries == 10
        assert c.incremental_sync is False

    def test_attachment_contract_defaults(self):
        c = AttachmentContract()
        assert c.max_file_size_mb == 50
        assert ".pdf" in c.supported_formats
        assert ".jpg" in c.supported_formats
        assert ".png" in c.supported_formats
        assert c.thumbnail_generation is True
        assert c.thumbnail_max_size == (200, 200)
        assert c.image_compression is True
        assert c.image_quality == 80
        assert c.max_image_resolution == (4000, 4000)
        assert c.offline_upload_queue is True
        assert c.auto_upload_on_wifi is True

    def test_attachment_contract_custom_values(self):
        c = AttachmentContract(
            max_file_size_mb=100,
            supported_formats=(".pdf",),
            image_quality=60,
        )
        assert c.max_file_size_mb == 100
        assert c.supported_formats == (".pdf",)
        assert c.image_quality == 60

    def test_auth_contract_defaults(self):
        c = MobileAuthContract()
        assert "jwt" in c.auth_methods
        assert "biometric" in c.auth_methods
        assert "pin" in c.auth_methods
        assert c.jwt_expiry_hours == 24
        assert c.refresh_token_expiry_days == 30
        assert c.biometric_enabled is True
        assert c.pin_code_enabled is True
        assert c.pin_length == 6
        assert c.max_failed_attempts == 5
        assert c.lockout_duration_minutes == 30
        assert c.remember_device is True
        assert c.device_limit == 3

    def test_auth_contract_custom_values(self):
        c = MobileAuthContract(
            auth_methods=("jwt",),
            jwt_expiry_hours=12,
            biometric_enabled=False,
            device_limit=1,
        )
        assert c.auth_methods == ("jwt",)
        assert c.jwt_expiry_hours == 12
        assert c.biometric_enabled is False
        assert c.device_limit == 1

    def test_notification_contract_defaults(self):
        c = MobileNotificationContract()
        assert c.push_enabled is True
        assert c.push_provider == "fcm"
        assert "receipt_created" in c.notification_types
        assert "receipt_updated" in c.notification_types
        assert "sync_complete" in c.notification_types
        assert "security_alert" in c.notification_types
        assert c.quiet_hours_enabled is True
        assert c.quiet_hours_start == 22
        assert c.quiet_hours_end == 6
        assert c.batch_notifications is True
        assert c.offline_notification_queue is True

    def test_notification_contract_custom_values(self):
        c = MobileNotificationContract(
            push_enabled=False,
            push_provider="apns",
            quiet_hours_start=23,
            quiet_hours_end=7,
        )
        assert c.push_enabled is False
        assert c.push_provider == "apns"
        assert c.quiet_hours_start == 23
        assert c.quiet_hours_end == 7

    def test_mobile_platform_enum(self):
        assert MobilePlatform.ANDROID.value == "android"
        assert MobilePlatform.IOS.value == "ios"
        assert MobilePlatform.TABLET.value == "tablet"
        assert MobilePlatform.WEB.value == "web"

    def test_sync_mode_enum(self):
        assert SyncMode.FULL.value == "full"
        assert SyncMode.INCREMENTAL.value == "incremental"
        assert SyncMode.MANUAL.value == "manual"
        assert SyncMode.REALTIME.value == "realtime"

    def test_offline_capability_enum(self):
        assert OfflineCapability.FULL.value == "full"
        assert OfflineCapability.PARTIAL.value == "partial"
        assert OfflineCapability.VIEW_ONLY.value == "view_only"
        assert OfflineCapability.NONE.value == "none"


# ============================================================================
# TestMobileReadinessManager
# ============================================================================


class TestMobileReadinessManager:
    """Tests for MobileReadinessManager class."""

    def setup_method(self):
        self.manager = MobileReadinessManager()

    def test_readiness_report_has_all_sections(self):
        report = self.manager.get_readiness_report()
        assert "android" in report
        assert "tablet" in report
        assert "offline" in report
        assert "sync" in report
        assert "attachment" in report
        assert "auth" in report
        assert "notification" in report
        assert "mobile_ready" in report

    def test_mobile_ready_flag(self):
        report = self.manager.get_readiness_report()
        assert report["mobile_ready"] is True

    def test_android_section(self):
        report = self.manager.get_readiness_report()
        android = report["android"]
        assert android["min_version"] == "1.0.0"
        assert android["offline_capability"] == "full"
        assert android["sync_mode"] == "incremental"
        assert isinstance(android["features"], list)
        assert "receipts" in android["features"]

    def test_tablet_section(self):
        report = self.manager.get_readiness_report()
        tablet = report["tablet"]
        assert tablet["min_version"] == "1.0.0"
        assert tablet["offline_capability"] == "full"
        assert isinstance(tablet["features"], list)
        assert "dashboard" in tablet["features"]

    def test_offline_section(self):
        report = self.manager.get_readiness_report()
        offline = report["offline"]
        assert offline["max_offline_hours"] == 72
        assert offline["max_cached_records"] == 10000
        assert offline["auto_sync"] is True

    def test_sync_section(self):
        report = self.manager.get_readiness_report()
        sync = report["sync"]
        assert sync["protocol"] == "rest"
        assert sync["batch_size"] == 100
        assert sync["conflict_resolution"] == "last-writer-wins"

    def test_attachment_section(self):
        report = self.manager.get_readiness_report()
        attachment = report["attachment"]
        assert attachment["max_file_size_mb"] == 50
        assert isinstance(attachment["formats"], list)
        assert ".pdf" in attachment["formats"]

    def test_auth_section(self):
        report = self.manager.get_readiness_report()
        auth = report["auth"]
        assert isinstance(auth["methods"], list)
        assert "jwt" in auth["methods"]
        assert auth["jwt_expiry_hours"] == 24
        assert auth["biometric"] is True

    def test_notification_section(self):
        report = self.manager.get_readiness_report()
        notification = report["notification"]
        assert notification["push_enabled"] is True
        assert notification["provider"] == "fcm"
        assert isinstance(notification["types"], list)
        assert "receipt_created" in notification["types"]

    def test_contracts_accessible_via_manager(self):
        assert self.manager.android.min_version == "1.0.0"
        assert self.manager.tablet.min_version == "1.0.0"
        assert self.manager.offline.max_offline_hours == 72
        assert self.manager.sync.batch_size == 100
        assert self.manager.attachment.max_file_size_mb == 50
        assert self.manager.auth.jwt_expiry_hours == 24
        assert self.manager.notification.push_enabled is True
