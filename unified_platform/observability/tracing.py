"""
Platform Observability — Distributed Tracing

Phase 6: Observability Platform
Constitution: Principle 19 (Observability First)
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Span:
    """A single trace span."""
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    operation: str = ""
    service: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {},
        })


@dataclass
class Trace:
    """A complete trace with multiple spans."""
    trace_id: str
    spans: list[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    status: str = "ok"

    def finish(self) -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        if any(s.status == "error" for s in self.spans):
            self.status = "error"


class Tracer:
    """Distributed tracing implementation."""

    def __init__(self, service: str = "platform") -> None:
        self._service = service
        self._traces: dict[str, Trace] = {}
        self._active_spans: dict[str, Span] = {}
        self._lock = threading.Lock()

    def start_trace(self, operation: str, attributes: dict[str, Any] | None = None) -> str:
        trace_id = str(uuid.uuid4())
        trace = Trace(trace_id=trace_id)
        self._traces[trace_id] = trace

        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            operation=operation,
            service=self._service,
            attributes=attributes or {},
        )
        trace.spans.append(span)
        self._active_spans[trace_id] = span
        return trace_id

    def start_span(self, trace_id: str, operation: str, parent_span_id: str | None = None) -> str:
        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=operation,
            service=self._service,
        )
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id].spans.append(span)
        return span_id

    def finish_span(self, trace_id: str, span_id: str, status: str = "ok") -> None:
        with self._lock:
            if trace_id in self._traces:
                for span in self._traces[trace_id].spans:
                    if span.span_id == span_id:
                        span.finish(status)
                        break

    def finish_trace(self, trace_id: str) -> Trace | None:
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace:
                trace.finish()
                self._active_spans.pop(trace_id, None)
            return trace

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    def get_traces(self, limit: int = 50) -> list[Trace]:
        return list(self._traces.values())[-limit:]

    def get_slow_traces(self, threshold_ms: float = 1000) -> list[Trace]:
        return [t for t in self._traces.values() if t.duration_ms > threshold_ms]

    def get_error_traces(self) -> list[Trace]:
        return [t for t in self._traces.values() if t.status == "error"]

    def export(self) -> dict[str, Any]:
        return {
            "total_traces": len(self._traces),
            "active_traces": len(self._active_spans),
            "slow_traces": len(self.get_slow_traces()),
            "error_traces": len(self.get_error_traces()),
        }
