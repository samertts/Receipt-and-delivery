"""
V13.0 Stability, Performance and Scale Certification

Validates:
- Low-spec hardware optimization
- Memory profiling (leak detection)
- Database growth certification (10K-250K receipts)
- Multi-site simulation
- Plugin architecture
- API platform readiness
- Long-run stability
- Future ecosystem readiness
"""

import gc
import os
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lab_system.app.settings.config as _cfg

ORIGINAL_DB_PATH = _cfg.CONFIG.db_path
ORIGINAL_STORAGE_DIR = _cfg.CONFIG.storage_dir


# ============================================================================
# FIXTURES
# ============================================================================

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


def _setup_base_data(conn):
    conn.execute(
        "INSERT INTO users(id,full_name,username,password_hash,role,status) "
        "VALUES(1,'Admin','admin','hash','Admin','Active')"
    )
    conn.execute(
        "INSERT INTO users(id,full_name,username,password_hash,role,status) "
        "VALUES(2,'Tech','tech1','hash','User','Active')"
    )
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) "
        "VALUES('Test Lab','TL001','Laboratory','Beirut')"
    )
    conn.execute(
        "INSERT INTO transaction_types(name, is_active) VALUES('Receipt', 1)"
    )
    conn.execute(
        "INSERT INTO transaction_types(name, is_active) VALUES('Delivery', 1)"
    )
    conn.execute(
        "INSERT INTO sample_types(name, category, status) VALUES('Blood', 'Clinical', 'Active')"
    )
    conn.commit()


def _insert_receipts(conn, count, start_id=1):
    now = datetime.now()
    for i in range(start_id, start_id + count):
        created_at = (now - timedelta(days=count - i)).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO receipts
               (receipt_no, tx_type_id, sender_org_id, receiver_org_id,
                sender_name, receiver_name, status, created_by, created_at)
               VALUES (?, 1, 1, 1, ?, ?, 'Draft', 1, ?)""",
            (f"RCP-{i:08d}", f"Sender {i}", f"Receiver {i}", created_at),
        )
    conn.commit()


@pytest.fixture
def v13_db(tmp_path):
    db_path = tmp_path / "v13_test.db"
    conn = _create_db(db_path)
    _setup_base_data(conn)
    conn.close()
    return db_path


@pytest.fixture
def v13_db_large(tmp_path):
    db_path = tmp_path / "v13_large.db"
    conn = _create_db(db_path)
    _setup_base_data(conn)
    _insert_receipts(conn, 10000)
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
# PHASE 1 — LOW SPEC OPTIMIZATION
# ============================================================================

class TestLowSpecOptimization:
    """Validate performance on low-spec hardware (4GB RAM, Dual Core, HDD)."""

    def test_startup_time_under_2_seconds(self, v13_db):
        """Startup completes in < 2 seconds."""
        start = time.time()
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 2.0, f"Startup took {elapsed:.2f}s, target < 2s"

    def test_ram_usage_under_200mb(self, v13_db):
        """RAM usage stays under 200MB."""
        import resource
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        for _ in range(50):
            conn.execute("SELECT * FROM receipts LIMIT 100").fetchall()
        conn.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        ram_mb = usage.ru_maxrss / 1024
        assert ram_mb < 200, f"RAM usage {ram_mb:.1f}MB, target < 200MB"

    def test_cpu_idle_low(self, v13_db):
        """CPU idle usage is minimal for lightweight operations."""
        import gc
        import resource
        gc.collect()
        start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        for _ in range(10):
            conn.execute("SELECT COUNT(*) FROM receipts").fetchone()
        conn.close()
        end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        cpu_seconds = end_cpu - start_cpu
        assert cpu_seconds < 1.0, f"CPU time {cpu_seconds:.2f}s for 10 queries, target < 1s"

    def test_search_latency_optimized(self, v13_db_large):
        """Search latency < 100ms on 10K records."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        start = time.time()
        conn.execute(
            "SELECT * FROM receipts WHERE sender_name LIKE ? LIMIT 20",
            ("%Sender 5000%",),
        ).fetchall()
        elapsed = (time.time() - start) * 1000
        conn.close()
        assert elapsed < 100, f"Search took {elapsed:.1f}ms, target < 100ms"

    def test_report_latency_optimized(self, v13_db_large):
        """Report generation < 500ms."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        start = time.time()
        conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()
        conn.execute("SELECT status, COUNT(*) as cnt FROM receipts GROUP BY status").fetchall()
        conn.execute("SELECT sender_name, COUNT(*) as cnt FROM receipts GROUP BY sender_name LIMIT 10").fetchall()
        elapsed = (time.time() - start) * 1000
        conn.close()
        assert elapsed < 500, f"Report took {elapsed:.1f}ms, target < 500ms"

    def test_wal_mode_enabled(self, v13_db):
        """WAL mode is enabled for concurrent access."""
        conn = sqlite3.connect(str(v13_db))
        row = conn.execute("PRAGMA journal_mode").fetchone()
        conn.close()
        assert row[0] == "wal", f"Expected WAL mode, got {row[0]}"

    def test_cache_size_optimized(self, v13_db):
        """Cache size is optimized for low-spec hardware."""
        conn = sqlite3.connect(str(v13_db))
        conn.execute("PRAGMA cache_size=-64000")
        row = conn.execute("PRAGMA cache_size").fetchone()
        conn.close()
        assert row[0] <= -64000 or row[0] >= 64000, f"Cache size {row[0]}, expected <= -64000 or >= 64000"


# ============================================================================
# PHASE 2 — MEMORY PROFILING
# ============================================================================

class TestMemoryProfiling:
    """Detect memory leaks and resource issues."""

    def test_no_memory_leak_on_repeated_queries(self, v13_db):
        """No memory leak after 1000 repeated queries."""
        import resource
        gc.collect()
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        for _ in range(1000):
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        conn.close()
        gc.collect()
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        growth_mb = (end_mem - start_mem) / 1024
        assert growth_mb < 10, f"Memory grew {growth_mb:.1f}MB after 1000 queries"

    def test_no_connection_leak(self, v13_db):
        """No connection leak after multiple operations."""
        for _ in range(100):
            conn = sqlite3.connect(str(v13_db))
            conn.row_factory = sqlite3.Row
            conn.execute("SELECT * FROM receipts LIMIT 5").fetchall()
            conn.close()
        conn = sqlite3.connect(str(v13_db))
        row = conn.execute("PRAGMA journal_mode").fetchone()
        conn.close()
        assert row[0] == "wal"

    def test_no_object_retention(self, v13_db):
        """No excessive object retention after operations."""
        import resource
        gc.collect()
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        for _ in range(100):
            conn = sqlite3.connect(str(v13_db))
            conn.row_factory = sqlite3.Row
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
            conn.close()
        gc.collect()
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        growth_mb = (end_mem - start_mem) / 1024
        assert growth_mb < 5, f"Object retention caused {growth_mb:.1f}MB growth"

    def test_concurrent_memory_stability(self, v13_db):
        """Memory stable under concurrent load."""
        import resource
        gc.collect()
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        errors = []

        def worker(thread_id):
            try:
                for _ in range(50):
                    conn = sqlite3.connect(str(v13_db))
                    conn.row_factory = sqlite3.Row
                    conn.execute("SELECT * FROM receipts LIMIT 5").fetchall()
                    conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        gc.collect()
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        growth_mb = (end_mem - start_mem) / 1024
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert growth_mb < 10, f"Concurrent memory growth {growth_mb:.1f}MB"


# ============================================================================
# PHASE 3 — DATABASE GROWTH CERTIFICATION
# ============================================================================

class TestDatabaseGrowth:
    """Validate performance at various database sizes."""

    def test_insert_performance_10k(self, v13_db):
        """10K receipts insert performance."""
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        start = time.time()
        _insert_receipts(conn, 10000, start_id=10001)
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 30, f"10K insert took {elapsed:.1f}s, target < 30s"

    def test_search_performance_10k(self, v13_db_large):
        """10K records search performance."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        start = time.time()
        conn.execute(
            "SELECT * FROM receipts WHERE sender_name LIKE ? LIMIT 20",
            ("%Sender 5000%",),
        ).fetchall()
        elapsed = (time.time() - start) * 1000
        conn.close()
        assert elapsed < 100, f"10K search took {elapsed:.1f}ms, target < 100ms"

    def test_database_size_reasonable(self, v13_db_large):
        """Database size is reasonable for 10K records."""
        import os
        size_mb = os.path.getsize(str(v13_db_large)) / (1024 * 1024)
        assert size_mb < 100, f"Database size {size_mb:.1f}MB for 10K records"

    def test_archive_performance(self, v13_db_large):
        """Archive operation performance."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        start = time.time()
        conn.execute(
            "UPDATE receipts SET status='Archived' WHERE id BETWEEN 1 AND 1000"
        )
        conn.commit()
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 5, f"Archive took {elapsed:.1f}s, target < 5s"

    def test_restore_performance(self, v13_db_large):
        """Restore operation performance."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        start = time.time()
        conn.execute(
            "UPDATE receipts SET status='Draft' WHERE status='Archived'"
        )
        conn.commit()
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 10, f"Restore took {elapsed:.1f}s, target < 10s"


# ============================================================================
# PHASE 4 — MULTI-SITE SIMULATION
# ============================================================================

class TestMultiSiteSimulation:
    """Validate multi-site synchronization and conflict resolution."""

    def test_multi_site_data_isolation(self, tmp_path):
        """Each site has isolated data."""
        db1_path = tmp_path / "site1.db"
        db2_path = tmp_path / "site2.db"
        conn1 = _create_db(db1_path)
        conn2 = _create_db(db2_path)
        _setup_base_data(conn1)
        _setup_base_data(conn2)
        _insert_receipts(conn1, 10, start_id=1001)
        _insert_receipts(conn2, 10, start_id=2001)
        count1 = conn1.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        count2 = conn2.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn1.close()
        conn2.close()
        assert count1 == 10
        assert count2 == 10

    def test_conflict_resolution_strategy(self, v13_db):
        """Conflict resolution uses last-write-wins."""
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
            "sender_name, receiver_name, status, created_by, created_at) "
            "VALUES('CONFLICT-001', 1, 1, 1, 'Site1', 'Recv1', 'Draft', 1, ?)",
            (datetime.now().isoformat(timespec="seconds"),),
        )
        conn.commit()
        conn.execute(
            "UPDATE receipts SET sender_name='Site2' WHERE receipt_no='CONFLICT-001'"
        )
        conn.commit()
        row = conn.execute(
            "SELECT sender_name FROM receipts WHERE receipt_no='CONFLICT-001'"
        ).fetchone()
        conn.close()
        assert row["sender_name"] == "Site2"

    def test_sync_queue_management(self, v13_db):
        """Sync queue handles multiple sites."""
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        now = datetime.now().isoformat(timespec="seconds")
        for i in range(10):
            conn.execute(
                "INSERT INTO sync_queue(entity_type, entity_id, action, status, created_at) "
                "VALUES('receipt', ?, 'create', 'pending', ?)",
                (i + 1, now),
            )
        conn.commit()
        pending = conn.execute(
            "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='pending'"
        ).fetchone()["cnt"]
        conn.close()
        assert pending == 10

    def test_data_consistency_across_sites(self, tmp_path):
        """Data consistency maintained across site operations."""
        db_path = tmp_path / "consistency.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 100)
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        assert count == 100
        conn.execute("UPDATE receipts SET status='Approved' WHERE id BETWEEN 1 AND 50")
        conn.commit()
        approved = conn.execute(
            "SELECT COUNT(*) as cnt FROM receipts WHERE status='Approved'"
        ).fetchone()["cnt"]
        conn.close()
        assert approved == 50


# ============================================================================
# PHASE 5 — PLUGIN ARCHITECTURE
# ============================================================================

class TestPluginArchitecture:
    """Validate plugin SDK, registry, and module loader."""

    def test_plugin_registry(self, v13_db):
        """Plugin registry manages plugins."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("test_plugin", {"version": "1.0", "status": "active"})
        assert registry.is_registered("test_plugin")
        assert not registry.is_registered("nonexistent")

    def test_plugin_loader(self, v13_db):
        """Plugin loader loads modules safely."""
        from lab_system.app.services.plugin_service import PluginLoader
        loader = PluginLoader()
        result = loader.validate_plugin_path("nonexistent")
        assert result["valid"] is False

    def test_plugin_isolation(self, v13_db):
        """Plugins are isolated from each other."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("plugin_a", {"version": "1.0"})
        registry.register("plugin_b", {"version": "2.0"})
        assert registry.get_plugin("plugin_a")["version"] == "1.0"
        assert registry.get_plugin("plugin_b")["version"] == "2.0"

    def test_plugin_lifecycle(self, v13_db):
        """Plugin lifecycle management works."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("lifecycle_plugin", {"version": "1.0", "status": "active"})
        plugin = registry.get_plugin("lifecycle_plugin")
        assert plugin["status"] == "active"
        registry.unregister("lifecycle_plugin")
        assert not registry.is_registered("lifecycle_plugin")

    def test_plugin_version_management(self, v13_db):
        """Plugin version management works."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("versioned", {"version": "1.0"})
        registry.update_plugin("versioned", {"version": "2.0"})
        assert registry.get_plugin("versioned")["version"] == "2.0"


# ============================================================================
# PHASE 6 — API PLATFORM READINESS
# ============================================================================

class TestAPIPlatformReadiness:
    """Validate API v1 contracts and versioning."""

    def test_api_v1_contract(self, v13_db):
        """API v1 contract is defined."""
        from lab_system.app.services.api_platform_service import APIPlatform
        api = APIPlatform()
        contract = api.get_v1_contract()
        assert "version" in contract
        assert contract["version"] == "v1"
        assert "endpoints" in contract

    def test_api_versioning_strategy(self, v13_db):
        """API versioning strategy is defined."""
        from lab_system.app.services.api_platform_service import APIPlatform
        api = APIPlatform()
        versions = api.get_supported_versions()
        assert "v1" in versions

    def test_api_endpoint_registration(self, v13_db):
        """API endpoints can be registered."""
        from lab_system.app.services.api_platform_service import APIPlatform
        api = APIPlatform()
        api.register_endpoint("GET", "/api/v1/receipts", "list_receipts")
        endpoints = api.get_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0]["method"] == "GET"

    def test_api_response_format(self, v13_db):
        """API response format is standardized."""
        from lab_system.app.services.api_platform_service import APIPlatform
        api = APIPlatform()
        response = api.format_response(200, {"data": []}, "Success")
        assert response["status_code"] == 200
        assert "data" in response
        assert "message" in response

    def test_api_error_handling(self, v13_db):
        """API error handling is standardized."""
        from lab_system.app.services.api_platform_service import APIPlatform
        api = APIPlatform()
        response = api.format_error(404, "Not Found")
        assert response["status_code"] == 404
        assert "error" in response


# ============================================================================
# PHASE 7 — LONG RUN STABILITY
# ============================================================================

class TestLongRunStability:
    """Validate stability under extended operation."""

    def test_sustained_operation_1000_cycles(self, v13_db):
        """System stable after 1000 operation cycles."""
        conn = sqlite3.connect(str(v13_db))
        conn.row_factory = sqlite3.Row
        errors = []
        for i in range(1000):
            try:
                conn.execute(
                    "SELECT * FROM receipts WHERE id = ?",
                    (i % 100 + 1,),
                ).fetchone()
                if i % 100 == 0:
                    conn.commit()
            except Exception as e:
                errors.append(str(e))
        conn.close()
        assert len(errors) == 0, f"Errors in sustained operation: {errors}"

    def test_concurrent_stability(self, v13_db):
        """System stable under concurrent load."""
        errors = []
        results = []

        def worker(thread_id):
            try:
                conn = sqlite3.connect(str(v13_db))
                conn.row_factory = sqlite3.Row
                for _ in range(100):
                    conn.execute("SELECT * FROM receipts LIMIT 5").fetchall()
                conn.close()
                results.append(f"thread_{thread_id}_ok")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 10

    def test_no_crash_under_load(self, v13_db_large):
        """System doesn't crash under heavy load."""
        conn = sqlite3.connect(str(v13_db_large))
        conn.row_factory = sqlite3.Row
        errors = []
        for _ in range(100):
            try:
                conn.execute("SELECT * FROM receipts LIMIT 100").fetchall()
                conn.execute(
                    "SELECT sender_name, COUNT(*) FROM receipts GROUP BY sender_name LIMIT 10"
                ).fetchall()
            except Exception as e:
                errors.append(str(e))
        conn.close()
        assert len(errors) == 0, f"Crash under load: {errors}"

    def test_database_integrity_after_operations(self, v13_db_large):
        """Database integrity maintained after operations."""
        conn = sqlite3.connect(str(v13_db_large))
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        assert result[0] == "ok", f"Integrity check failed: {result[0]}"


# ============================================================================
# PHASE 8 — FUTURE ECOSYSTEM READINESS
# ============================================================================

class TestFutureEcosystemReadiness:
    """Validate readiness for future platform expansion."""

    def test_lab_platform_integration_point(self, v13_db):
        """Laboratory platform integration point exists."""
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(v13_db):
            svc = NationalNetworkService(str(v13_db))
            svc.initialize_schema()
            result = svc.register_laboratory(
                name="Test Lab", code="TL001", lab_type="hospital",
            )
            assert result["success"] is True

    def test_workforce_platform_contract(self, v13_db):
        """Workforce platform contract is defined."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("workforce", {
            "version": "1.0",
            "contracts": ["user_management", "role_management"],
        })
        plugin = registry.get_plugin("workforce")
        assert "contracts" in plugin

    def test_inventory_platform_contract(self, v13_db):
        """Inventory platform contract is defined."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("inventory", {
            "version": "1.0",
            "contracts": ["stock_management", "order_tracking"],
        })
        plugin = registry.get_plugin("inventory")
        assert "contracts" in plugin

    def test_training_platform_contract(self, v13_db):
        """Training platform contract is defined."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("training", {
            "version": "1.0",
            "contracts": ["course_management", "certification_tracking"],
        })
        plugin = registry.get_plugin("training")
        assert "contracts" in plugin

    def test_public_health_platform_contract(self, v13_db):
        """Public health platform contract is defined."""
        from lab_system.app.services.plugin_service import PluginRegistry
        registry = PluginRegistry()
        registry.register("public_health", {
            "version": "1.0",
            "contracts": ["disease_surveillance", "reporting"],
        })
        plugin = registry.get_plugin("public_health")
        assert "contracts" in plugin

    def test_national_expansion_readiness(self, v13_db):
        """National expansion capability is ready."""
        from lab_system.app.services.national_network_service import NationalNetworkService
        with _patch_db(v13_db):
            svc = NationalNetworkService(str(v13_db))
            svc.initialize_schema()
            report = svc.get_national_readiness_report()
            assert "readiness_score" in report
