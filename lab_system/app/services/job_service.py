"""Bounded background job execution with cooperative cancellation and watchdogs."""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: str
    kind: str
    status: str = JobStatus.QUEUED
    progress: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    error: str = ""
    retry_count: int = 0
    max_retries: int = 0
    timeout_seconds: float | None = None
    _cancel_event: threading.Event = field(
        default_factory=threading.Event, repr=False, compare=False
    )
    _future: Future | None = field(default=None, repr=False, compare=False)


ProgressCallback = Callable[[int], None]
JobFunction = Callable[[ProgressCallback, threading.Event], None]


class JobManager:
    """Run bounded jobs without sharing UI or database objects across threads."""

    def __init__(self, max_workers: int = 2):
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="lab-job"
        )
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()

    def submit(
        self,
        kind: str,
        function: JobFunction,
        *,
        max_retries: int = 0,
        timeout_seconds: float | None = None,
    ) -> str:
        if not kind.strip():
            raise ValueError("job kind is required")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        job = Job(
            id=uuid.uuid4().hex,
            kind=kind.strip(),
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )
        with self._lock:
            self._jobs[job.id] = job
            job._future = self._executor.submit(self._run, job, function)
        if timeout_seconds is not None:
            threading.Thread(
                target=self._watchdog,
                args=(job,),
                name=f"job-watchdog-{job.id[:8]}",
                daemon=True,
            ).start()
        return job.id

    def _set_progress(self, job: Job, progress: int) -> None:
        with self._lock:
            if job.status not in {JobStatus.QUEUED, JobStatus.RUNNING}:
                return
            job.progress = max(0, min(100, int(progress)))

    def _run(self, job: Job, function: JobFunction) -> None:
        with self._lock:
            if job._cancel_event.is_set():
                job.status = JobStatus.CANCELLED
                job.completed_at = _now()
                return
            job.status = JobStatus.RUNNING
            job.started_at = _now()
        while True:
            try:
                function(
                    lambda progress: self._set_progress(job, progress),
                    job._cancel_event,
                )
                with self._lock:
                    if job._cancel_event.is_set():
                        if job.status not in {JobStatus.TIMED_OUT, JobStatus.CANCELLED}:
                            job.status = JobStatus.CANCELLED
                    else:
                        job.progress = 100
                        job.status = JobStatus.SUCCEEDED
                    job.completed_at = _now()
                return
            except Exception as exc:
                with self._lock:
                    job.error = str(exc)[:500]
                    if job._cancel_event.is_set():
                        if job.status not in {JobStatus.TIMED_OUT, JobStatus.CANCELLED}:
                            job.status = JobStatus.CANCELLED
                        job.completed_at = _now()
                        return
                    if job.retry_count >= job.max_retries:
                        job.status = JobStatus.FAILED
                        job.completed_at = _now()
                        return
                    job.retry_count += 1

    def _watchdog(self, job: Job) -> None:
        future = job._future
        if future is None or job.timeout_seconds is None:
            return
        try:
            future.result(timeout=job.timeout_seconds)
        except TimeoutError:
            with self._lock:
                if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                    job.status = JobStatus.TIMED_OUT
                    job.error = "job exceeded watchdog timeout"
                    job.completed_at = _now()
                    job._cancel_event.set()
        except Exception:
            # The worker owns failure state; the watchdog must not overwrite it.
            return

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return Job(
                id=job.id,
                kind=job.kind,
                status=job.status,
                progress=job.progress,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error=job.error,
                retry_count=job.retry_count,
                max_retries=job.max_retries,
                timeout_seconds=job.timeout_seconds,
            )

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status in {
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.TIMED_OUT,
            }:
                return False
            job._cancel_event.set()
            job.status = JobStatus.CANCELLED
            job.completed_at = _now()
            if job._future:
                job._future.cancel()
            return True

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)
