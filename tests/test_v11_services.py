"""V11.0 Tests — Self Healing, Chain of Custody, Predictive Intelligence,
Command Center, Performance, Mobile Readiness, National Network."""

import os
import sqlite3
import sys
import time
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lab_system.app.settings.config as _cfg
ORIGINAL_DB_PATH = _cfg.CONFIG.db_path
ORIGINAL_STORAGE_DIR = _cfg.CONFIG.storage_dir

ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _create_db(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "lab_system", "app", "database", "db.py"
    )
    with open(schema_path, "r") as f:
        schema_content = f.read()
    globals_ = {}
    exec(schema_content, globals_)
    for table_sql in globals_["SCHEMA"].split(";"):
        if table_sql.strip():
            try:
                conn.execute(table_sql)
            except sqlite3.OperationalError:
                pass
    conn.commit()
    return conn


def _setup_receipt_data(conn):
    conn.execute(
        "INSERT INTO users(full_name,username,password_hash,role,status) "
        "VALUES('Admin','admin','hash','Admin','Active')"
    )
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) "
        "VALUES('Org1', 'ORG1', 'clinic', 'Baghdad')"
    )
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) "
        "VALUES('Org2', 'ORG2', 'laboratory', 'Basra')"
    )
    conn.execute("INSERT INTO transaction_types(name) VALUES('receipt')")
    conn.execute("INSERT INTO sample_types(name) VALUES('blood')")
    conn.commit()
    conn.execute(
        """INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,
            sender_name,receiver_name,status,created_at,created_by)
            VALUES('R001',1,1,2,'Sender','Receiver','Draft','2024-01-01',1)"""
    )
    conn.commit()


@pytest.fixture
def fresh_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = _create_db(db_path)
    conn.execute(
        "INSERT INTO users(id,full_name,username,password_hash,role,status) "
        "VALUES(1,'Admin','admin','hash','Admin','Active')"
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def fresh_db_with_data(tmp_path):
    db_path = tmp_path / "test.db"
    conn = _create_db(db_path)
    _setup_receipt_data(conn)
    conn.close()
    return db_path


def _patch_db(db_path, storage_dir=None):
    import lab_system.app.settings.config as cfg_mod
    import lab_system.app.database.db as db_mod

    originals = {}
    originals["db_get_conn"] = db_mod.get_conn

    @contextmanager
    def _test_get_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    db_mod.get_conn = _test_get_conn
    originals["cfg_db_path"] = cfg_mod.CONFIG.db_path
    object.__setattr__(cfg_mod.CONFIG, "db_path", str(db_path))

    if storage_dir is not None:
        originals["cfg_storage_dir"] = cfg_mod.CONFIG.storage_dir
        object.__setattr__(cfg_mod.CONFIG, "storage_dir", storage_dir)

    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            db_mod.get_conn = originals["db_get_conn"]
            object.__setattr__(cfg_mod.CONFIG, "db_path", originals["cfg_db_path"])
            if "cfg_storage_dir" in originals:
                object.__setattr__(cfg_mod.CONFIG, "storage_dir", originals["cfg_storage_dir"])

    return _Ctx()


@pytest.fixture(autouse=True)
def _restore_config():
    import lab_system.app.settings.config as cfg_mod
    yield
    object.__setattr__(cfg_mod.CONFIG, "db_path", ORIGINAL_DB_PATH)
    object.__setattr__(cfg_mod.CONFIG, "storage_dir", ORIGINAL_STORAGE_DIR)


# ============================================================================
# SELF HEALING SERVICE
# ============================================================================

class TestSelfHealingService:
    def test_detect_database_lock_healthy(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_database_lock()
            assert result["status"] == "healthy"

    def test_detect_backup_health_no_dir(self, fresh_db, tmp_path):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db, storage_dir=tmp_path / "empty"):
            (tmp_path / "empty").mkdir(exist_ok=True)
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_backup_health()
            assert result["status"] in ("degraded", "healthy")

    def test_detect_backup_health_with_backups(self, fresh_db, tmp_path):
        from lab_system.app.services.self_healing_service import SelfHealingService
        bk_dir = tmp_path / "backups"
        bk_dir.mkdir()
        (bk_dir / "test_backup.db").write_bytes(b"fake backup")
        with _patch_db(fresh_db, storage_dir=tmp_path):
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_backup_health()
            assert "backups" in result["details"]

    def test_detect_recovery_health(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_recovery_health()
            assert result["status"] == "healthy"

    def test_detect_sync_health(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_sync_health()
            assert result["status"] == "healthy"

    def test_detect_storage_health(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.detect_storage_health()
            assert result["status"] in ("healthy", "degraded")

    def test_get_overall_health(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.get_overall_health()
            assert "overall_status" in result
            assert "health_score" in result
            assert "checks" in result
            assert len(result["checks"]) == 5

    def test_attempt_auto_healing(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.attempt_auto_healing()
            assert "healed" in result
            assert "failed" in result
            assert "actions" in result

    def test_healing_log(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            svc.attempt_auto_healing()
            log = svc.get_healing_log()
            assert isinstance(log, list)

    def test_recover_database_lock(self, fresh_db):
        from lab_system.app.services.self_healing_service import SelfHealingService
        with _patch_db(fresh_db):
            svc = SelfHealingService(str(fresh_db))
            result = svc.recover_database_lock()
            assert result["success"] is True

    def test_recover_backup_failure(self, fresh_db, tmp_path):
        from lab_system.app.services.self_healing_service import SelfHealingService
        bk_dir = tmp_path / "backups"
        bk_dir.mkdir()
        snap_dir = tmp_path / "snapshots"
        snap_dir.mkdir()
        with _patch_db(fresh_db, storage_dir=tmp_path):
            svc = SelfHealingService(str(fresh_db))
            result = svc.recover_backup_failure()
            assert result["success"] is True


# ============================================================================
# CHAIN OF CUSTODY SERVICE
# ============================================================================

class TestChainOfCustodyService:
    def test_initialize_schema(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            conn = sqlite3.connect(str(fresh_db))
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sample_lifecycle'"
            ).fetchone()
            assert row is not None
            conn.close()

    def test_register_sample(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            result = svc.register_sample(
                sample_id=1, receipt_id=1, user_id=1, location="Lab A"
            )
            assert result["success"] is True
            assert result["entry_id"] is not None

    def test_transition_stage(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import (
            ChainOfCustodyService, SampleStage,
        )
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            result = svc.transition_stage(
                sample_id=1, receipt_id=1,
                new_stage=SampleStage.REGISTERED, user_id=1,
            )
            assert result["success"] is True

    def test_invalid_transition_rejected(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import (
            ChainOfCustodyService, SampleStage,
        )
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            result = svc.transition_stage(
                sample_id=1, receipt_id=1,
                new_stage=SampleStage.DELIVERED, user_id=1,
            )
            assert result["success"] is False
            assert "Invalid transition" in result["error"]

    def test_invalid_stage_rejected(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            result = svc.transition_stage(
                sample_id=1, receipt_id=1,
                new_stage="invalid_stage", user_id=1,
            )
            assert result["success"] is False

    def test_get_current_stage(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import (
            ChainOfCustodyService, SampleStage,
        )
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            stage = svc.get_current_stage(1)
            assert stage == SampleStage.RECEIVED

    def test_get_lifecycle_history(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import (
            ChainOfCustodyService, SampleStage,
        )
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            svc.transition_stage(
                sample_id=1, receipt_id=1,
                new_stage=SampleStage.REGISTERED, user_id=1,
            )
            history = svc.get_lifecycle_history(1)
            assert len(history) == 2

    def test_get_lifecycle_summary(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            summary = svc.get_lifecycle_summary(1)
            assert summary["sample_id"] == 1
            assert summary["current_stage"] == "received"

    def test_get_stage_statistics(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            stats = svc.get_stage_statistics()
            assert stats["received"] == 1

    def test_full_traceability_report(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import ChainOfCustodyService
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            report = svc.get_full_traceability_report()
            assert report["traceability_score"] == 100.0
            assert report["total_samples_tracked"] == 1

    def test_full_lifecycle_flow(self, fresh_db):
        from lab_system.app.services.chain_of_custody_service import (
            ChainOfCustodyService, SampleStage,
        )
        with _patch_db(fresh_db):
            svc = ChainOfCustodyService(str(fresh_db))
            svc.initialize_schema()
            svc.register_sample(sample_id=1, receipt_id=1, user_id=1)
            for stage in [
                SampleStage.REGISTERED,
                SampleStage.TRANSPORTED,
                SampleStage.TESTING,
                SampleStage.APPROVED,
                SampleStage.DELIVERED,
                SampleStage.ARCHIVED,
            ]:
                result = svc.transition_stage(
                    sample_id=1, receipt_id=1,
                    new_stage=stage, user_id=1,
                )
                assert result["success"] is True, f"Failed at {stage}: {result['error']}"
            assert svc.get_current_stage(1) == SampleStage.ARCHIVED
            history = svc.get_lifecycle_history(1)
            assert len(history) == 7


# ============================================================================
# PREDICTIVE INTELLIGENCE SERVICE
# ============================================================================

class TestPredictiveIntelligenceService:
    def test_predict_backup_failure(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_backup_failure()
            assert "risk_level" in result
            assert "confidence" in result
            assert "evidence" in result

    def test_predict_sync_failure(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_sync_failure()
            assert "risk_level" in result

    def test_predict_storage_exhaustion(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_storage_exhaustion()
            assert "risk_level" in result
            assert "evidence" in result

    def test_predict_database_growth(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_database_growth()
            assert "risk_level" in result

    def test_predict_performance_degradation(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_performance_degradation()
            assert "risk_level" in result

    def test_predict_recovery_failure(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_recovery_failure()
            assert "risk_level" in result

    def test_get_all_predictions(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.get_all_predictions()
            assert "overall_risk" in result
            assert "predictions" in result
            assert len(result["predictions"]) == 6

    def test_prediction_has_recommendation(self, fresh_db):
        from lab_system.app.services.prediction_service import PredictiveIntelligenceService
        with _patch_db(fresh_db):
            svc = PredictiveIntelligenceService(str(fresh_db))
            result = svc.predict_backup_failure()
            assert "recommendation" in result
            assert len(result["recommendation"]) > 0


# ============================================================================
# COMMAND CENTER SERVICE
# ============================================================================

class TestCommandCenterService:
    def test_get_database_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_database_health()
            assert "score" in result
            assert result["score"] >= 50

    def test_get_backup_health(self, fresh_db, tmp_path):
        from lab_system.app.services.command_center_service import CommandCenterService
        bk_dir = tmp_path / "backups"
        bk_dir.mkdir()
        with _patch_db(fresh_db, storage_dir=tmp_path):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_backup_health()
            assert "score" in result

    def test_get_recovery_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_recovery_health()
            assert "score" in result

    def test_get_sync_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_sync_health()
            assert "score" in result

    def test_get_security_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_security_health()
            assert "score" in result

    def test_get_performance_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_performance_health()
            assert "score" in result

    def test_get_user_activity_health(self, fresh_db):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db):
            svc = CommandCenterService(str(fresh_db))
            result = svc.get_user_activity_health()
            assert "score" in result

    def test_get_operational_alerts(self, fresh_db, tmp_path):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db, storage_dir=tmp_path):
            (tmp_path / "backups").mkdir(exist_ok=True)
            (tmp_path / "snapshots").mkdir(exist_ok=True)
            svc = CommandCenterService(str(fresh_db))
            alerts = svc.get_operational_alerts()
            assert isinstance(alerts, list)

    def test_get_command_center_report(self, fresh_db, tmp_path):
        from lab_system.app.services.command_center_service import CommandCenterService
        with _patch_db(fresh_db, storage_dir=tmp_path):
            (tmp_path / "backups").mkdir(exist_ok=True)
            (tmp_path / "snapshots").mkdir(exist_ok=True)
            svc = CommandCenterService(str(fresh_db))
            report = svc.get_command_center_report()
            assert "overall_health_score" in report
            assert "scores" in report
            assert "alerts" in report
            assert len(report["scores"]) == 7


# ============================================================================
# PERFORMANCE SERVICE
# ============================================================================

class TestPerformanceService:
    def test_startup_timer(self):
        from lab_system.app.services.performance_service import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.start_startup_timer()
        time.sleep(0.01)
        monitor.end_startup_timer()
        assert monitor.startup_time_ms > 0
        assert monitor.startup_time_sec > 0

    def test_startup_report(self):
        from lab_system.app.services.performance_service import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.start_startup_timer()
        time.sleep(0.01)
        monitor.end_startup_timer()
        report = monitor.get_startup_report()
        assert "startup_time_ms" in report
        assert "memory_usage_mb" in report

    def test_query_time_tracking(self):
        from lab_system.app.services.performance_service import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.record_query_time(10.0)
        monitor.record_query_time(20.0)
        assert monitor.avg_query_time_ms == 15.0

    def test_background_worker_pool(self):
        from lab_system.app.services.performance_service import BackgroundWorkerPool
        pool = BackgroundWorkerPool(max_workers=2)
        pool.start()
        result = pool.submit(lambda: 42)
        assert result.result() == 42
        stats = pool.get_stats()
        assert stats["tasks_completed"] >= 1
        pool.stop()

    def test_query_optimizer(self):
        from lab_system.app.services.performance_service import QueryOptimizer
        optimizer = QueryOptimizer()
        optimizer.optimize_db(str(_cfg.CONFIG.db_path))
        stats = optimizer.get_db_stats(str(_cfg.CONFIG.db_path))
        assert "pages" in stats
        assert "size_mb" in stats

    def test_memory_optimizer(self):
        from lab_system.app.services.performance_service import MemoryOptimizer
        mem = MemoryOptimizer.get_process_memory_mb()
        assert mem > 0
        report = MemoryOptimizer.get_memory_report()
        assert "current_mb" in report
        assert "target_met" in report

    def test_lazy_loader(self):
        from lab_system.app.services.performance_service import LazyLoader
        loader = LazyLoader()
        call_count = [0]
        def factory():
            call_count[0] += 1
            return "instance"
        loader.register("test", factory)
        assert not loader.is_loaded("test")
        result = loader.get("test")
        assert result == "instance"
        assert loader.is_loaded("test")
        assert call_count[0] == 1
        loader.get("test")
        assert call_count[0] == 1

    def test_get_performance_report(self):
        from lab_system.app.services.performance_service import get_performance_report
        report = get_performance_report()
        assert "startup" in report
        assert "workers" in report
        assert "memory" in report


# ============================================================================
# MOBILE READINESS SERVICE
# ============================================================================

class TestMobileReadinessService:
    def test_mobile_receipt_contract(self):
        from lab_system.app.services.mobile_service import MobileReceiptContract
        receipt = {"receipt_no": "R001", "sender_name": "Test"}
        items = [{"sample_type_id": 1, "total_count": 10}]
        contract = MobileReceiptContract.create_receipt_data(receipt, items)
        assert contract["contract_version"] == "1.0"
        assert contract["operation"] == "create_receipt"
        assert contract["data"]["receipt"]["receipt_no"] == "R001"

    def test_mobile_receipt_response(self):
        from lab_system.app.services.mobile_service import MobileReceiptContract
        response = MobileReceiptContract.receipt_response(
            {"id": 1}, success=True
        )
        assert response["success"] is True
        assert response["error"] == ""

    def test_offline_data_store(self, fresh_db):
        from lab_system.app.services.mobile_service import OfflineDataStore
        with _patch_db(fresh_db):
            store = OfflineDataStore(str(fresh_db))
            store.initialize_offline_schema()
            result = store.queue_offline_operation(
                operation="create",
                entity_type="receipts",
                entity_id=1,
                payload={"test": True},
                device_id="device1",
            )
            assert result["success"] is True
            pending = store.get_pending_operations()
            assert len(pending) == 1
            store.mark_synced(result["offline_id"])
            pending = store.get_pending_operations()
            assert len(pending) == 0

    def test_offline_mark_failed(self, fresh_db):
        from lab_system.app.services.mobile_service import OfflineDataStore
        with _patch_db(fresh_db):
            store = OfflineDataStore(str(fresh_db))
            store.initialize_offline_schema()
            result = store.queue_offline_operation(
                operation="create", entity_type="receipts",
                entity_id=1, payload={}, device_id="d1",
            )
            store.mark_failed(result["offline_id"], "network error")
            stats = store.get_sync_stats()
            assert stats["failed"] == 1

    def test_sync_protocol_contract(self):
        from lab_system.app.services.mobile_service import SyncProtocolContract
        request = SyncProtocolContract.create_sync_request(
            entity_type="receipts", entity_id=1,
            action="create", payload={"test": True},
            client_timestamp="2024-01-01T00:00:00",
        )
        assert request["contract_version"] == "1.0"
        response = SyncProtocolContract.create_sync_response(
            success=True, entity_type="receipts",
            entity_id=1, server_timestamp="2024-01-01T00:00:01",
        )
        assert response["success"] is True

    def test_notification_contract(self):
        from lab_system.app.services.mobile_service import NotificationContract
        notif = NotificationContract.create_notification(
            title="Test", body="Body", notification_type="info",
        )
        assert notif["contract_version"] == "1.0"
        batch = NotificationContract.create_notification_batch([notif, notif])
        assert batch["count"] == 2

    def test_attachment_contract(self):
        from lab_system.app.services.mobile_service import AttachmentContract
        req = AttachmentContract.create_attachment_request(
            receipt_id=1, file_name="test.pdf",
            file_type="pdf", file_size=1024, file_hash="abc",
        )
        assert req["contract_version"] == "1.0"
        resp = AttachmentContract.create_attachment_response(
            success=True, attachment_id=1,
        )
        assert resp["success"] is True

    def test_get_mobile_readiness_report(self):
        from lab_system.app.services.mobile_service import get_mobile_readiness_report
        report = get_mobile_readiness_report()
        assert report["contracts_ready"] is True
        assert report["offline_store_ready"] is True


# ============================================================================
# NATIONAL NETWORK SERVICE
# ============================================================================

class TestNationalNetworkService:
    def test_initialize_schema(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            conn = sqlite3.connect(str(fresh_db))
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "laboratories" in table_names
            assert "laboratory_nodes" in table_names
            assert "referrals" in table_names
            conn.close()

    def test_register_laboratory(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            result = svc.register_laboratory(
                name="Test Lab", code="TL001",
                lab_type="hospital", governorate="Baghdad",
            )
            assert result["success"] is True
            assert result["lab_id"] is not None

    def test_register_duplicate_lab_rejected(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            svc.register_laboratory(name="Lab1", code="L1", lab_type="hospital")
            result = svc.register_laboratory(name="Lab2", code="L1", lab_type="hospital")
            assert result["success"] is False
            assert "already exists" in result["error"]

    def test_register_invalid_lab_type(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            result = svc.register_laboratory(
                name="Bad Lab", code="BL001", lab_type="invalid",
            )
            assert result["success"] is False

    def test_get_laboratory(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            reg = svc.register_laboratory(
                name="Test Lab", code="TL001", lab_type="reference",
            )
            lab = svc.get_laboratory(reg["lab_id"])
            assert lab is not None
            assert lab["name"] == "Test Lab"

    def test_list_laboratories(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            svc.register_laboratory(name="Lab1", code="L1", lab_type="hospital")
            svc.register_laboratory(name="Lab2", code="L2", lab_type="reference")
            labs = svc.list_laboratories()
            assert len(labs) == 2

    def test_discover_laboratories(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            svc.register_laboratory(
                name="Baghdad Lab", code="BL1",
                lab_type="hospital", governorate="Baghdad",
            )
            svc.register_laboratory(
                name="Basra Lab", code="BS1",
                lab_type="reference", governorate="Basra",
            )
            labs = svc.discover_laboratories(governorate="Baghdad")
            assert len(labs) == 1

    def test_register_node(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            reg = svc.register_laboratory(
                name="Test Lab", code="TL001", lab_type="hospital",
            )
            result = svc.register_node(
                lab_id=reg["lab_id"], node_name="Node1",
                ip_address="192.168.1.1", version="1.0",
            )
            assert result["success"] is True
            assert result["node_id"] is not None

    def test_update_node_heartbeat(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            reg = svc.register_laboratory(
                name="Test Lab", code="TL001", lab_type="hospital",
            )
            node = svc.register_node(
                lab_id=reg["lab_id"], node_name="Node1",
            )
            result = svc.update_node_heartbeat(node["node_id"], "online")
            assert result is True

    def test_get_node_health(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            reg = svc.register_laboratory(
                name="Test Lab", code="TL001", lab_type="hospital",
            )
            svc.register_node(lab_id=reg["lab_id"], node_name="Node1")
            health = svc.get_node_health()
            assert len(health) == 1

    def test_generate_nsid(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            nsid = svc.generate_nsid("TL001", 1)
            assert nsid.startswith("NSID-TL001-")

    def test_generate_referral_no(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            ref_no = svc.generate_referral_no("TL001")
            assert ref_no.startswith("REF-TL001-")

    def test_create_referral(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            lab1 = svc.register_laboratory(
                name="Lab1", code="L1", lab_type="hospital",
            )
            lab2 = svc.register_laboratory(
                name="Lab2", code="L2", lab_type="reference",
            )
            result = svc.create_referral(
                sample_id=1, from_lab_id=lab1["lab_id"],
                to_lab_id=lab2["lab_id"], user_id=1,
            )
            assert result["success"] is True
            assert result["referral_no"] is not None

    def test_update_referral_status(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            lab1 = svc.register_laboratory(
                name="Lab1", code="L1", lab_type="hospital",
            )
            lab2 = svc.register_laboratory(
                name="Lab2", code="L2", lab_type="reference",
            )
            ref = svc.create_referral(
                sample_id=1, from_lab_id=lab1["lab_id"],
                to_lab_id=lab2["lab_id"], user_id=1,
            )
            result = svc.update_referral_status(
                ref["referral_no"], "accepted",
            )
            assert result["success"] is True

    def test_invalid_referral_status(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            lab1 = svc.register_laboratory(
                name="Lab1", code="L1", lab_type="hospital",
            )
            lab2 = svc.register_laboratory(
                name="Lab2", code="L2", lab_type="reference",
            )
            ref = svc.create_referral(
                sample_id=1, from_lab_id=lab1["lab_id"],
                to_lab_id=lab2["lab_id"], user_id=1,
            )
            result = svc.update_referral_status(
                ref["referral_no"], "invalid_status",
            )
            assert result["success"] is False

    def test_list_referrals(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            lab1 = svc.register_laboratory(
                name="Lab1", code="L1", lab_type="hospital",
            )
            lab2 = svc.register_laboratory(
                name="Lab2", code="L2", lab_type="reference",
            )
            svc.create_referral(
                sample_id=1, from_lab_id=lab1["lab_id"],
                to_lab_id=lab2["lab_id"], user_id=1,
            )
            refs = svc.list_referrals()
            assert len(refs) == 1

    def test_get_network_statistics(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            svc.register_laboratory(name="Lab1", code="L1", lab_type="hospital")
            svc.register_laboratory(name="Lab2", code="L2", lab_type="reference")
            stats = svc.get_network_statistics()
            assert stats["total_laboratories"] == 2
            assert stats["active_laboratories"] == 2

    def test_get_national_readiness_report(self, fresh_db):
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(fresh_db):
            svc = NationalNetworkService(str(fresh_db))
            svc.initialize_schema()
            svc.register_laboratory(name="Lab1", code="L1", lab_type="hospital")
            report = svc.get_national_readiness_report()
            assert "readiness_score" in report
            assert "statistics" in report
            assert report["federation_ready"] is True
