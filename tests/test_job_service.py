from __future__ import annotations

import threading
import time

from lab_system.app.services.job_service import JobManager, JobStatus


def _wait_for(manager: JobManager, job_id: str, statuses: set[str]):
    deadline = time.time() + 3
    while time.time() < deadline:
        job = manager.get(job_id)
        if job and job.status in statuses:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {statuses}: {manager.get(job_id)}")


def test_job_success_reports_progress():
    manager = JobManager(max_workers=1)
    try:
        def work(progress, cancelled):
            progress(40)
            assert not cancelled.is_set()

        job_id = manager.submit("report", work)
        job = _wait_for(manager, job_id, {JobStatus.SUCCEEDED})
        assert job.progress == 100
        assert job.error == ""
    finally:
        manager.shutdown()


def test_job_retries_then_succeeds():
    manager = JobManager(max_workers=1)
    attempts = 0
    try:
        def work(progress, cancelled):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("temporary")
            progress(100)

        job_id = manager.submit("sync", work, max_retries=1)
        job = _wait_for(manager, job_id, {JobStatus.SUCCEEDED})
        assert attempts == 2
        assert job.retry_count == 1
    finally:
        manager.shutdown()


def test_job_watchdog_requests_cooperative_cancellation():
    manager = JobManager(max_workers=1)
    stopped = threading.Event()
    try:
        def work(progress, cancelled):
            while not cancelled.is_set():
                time.sleep(0.01)
            stopped.set()

        job_id = manager.submit("import", work, timeout_seconds=0.05)
        job = _wait_for(manager, job_id, {JobStatus.TIMED_OUT})
        assert "watchdog" in job.error
        assert stopped.wait(1)
    finally:
        manager.shutdown()


def test_cancel_queued_job():
    manager = JobManager(max_workers=1)
    gate = threading.Event()
    try:
        first = manager.submit("first", lambda progress, cancelled: gate.wait(2))
        second = manager.submit("second", lambda progress, cancelled: None)
        assert manager.cancel(second) is True
        assert _wait_for(manager, second, {JobStatus.CANCELLED}).status == JobStatus.CANCELLED
        gate.set()
        _wait_for(manager, first, {JobStatus.SUCCEEDED, JobStatus.CANCELLED})
    finally:
        manager.shutdown()
