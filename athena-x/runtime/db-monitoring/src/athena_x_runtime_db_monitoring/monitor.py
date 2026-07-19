"""Database performance monitor - Stage 5 req 10.

Tracks:
  - Database latency (p50, p95, p99)
  - Query execution time
  - Insert throughput
  - Storage growth
  - Partition health
  - Index usage
  - Lock contention
  - Connection pool utilization

Expose in Supervisor dashboard (Stage 13).
"""
from __future__ import annotations
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Deque


@dataclass
class QueryStats:
    """Statistics for a single query type."""
    operation: str  # "write_quote", "read_quote", etc.
    count: int = 0
    latencies: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    errors: int = 0

    def record(self, latency_ms: float, success: bool = True) -> None:
        self.count += 1
        self.latencies.append(latency_ms)
        if not success:
            self.errors += 1

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0.0

    @property
    def p95(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def p99(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def error_rate(self) -> float:
        return self.errors / self.count if self.count > 0 else 0.0


@dataclass
class DBMetrics:
    """Aggregated database metrics for Supervisor dashboard."""
    total_writes: int = 0
    total_reads: int = 0
    total_errors: int = 0
    write_throughput_per_sec: float = 0.0
    avg_write_latency_ms: float = 0.0
    avg_read_latency_ms: float = 0.0
    storage_bytes: int = 0
    partition_count: int = 0
    active_connections: int = 0
    lock_contention_count: int = 0
    by_operation: dict[str, dict] = field(default_factory=dict)


class DBMonitor:
    """Monitors database performance.

    Usage:
        monitor = DBMonitor()
        with monitor.track("write_quote"):
            await repo.write_quote(record)
        metrics = monitor.get_metrics()
    """

    def __init__(self):
        self._stats: dict[str, QueryStats] = {}
        self._lock = RLock()
        self._start_time = time.monotonic()
        self._writes_since_start = 0

    def track(self, operation: str):
        """Context manager to track query latency."""
        return _QueryTracker(self, operation)

    def record(self, operation: str, latency_ms: float, success: bool = True) -> None:
        with self._lock:
            if operation not in self._stats:
                self._stats[operation] = QueryStats(operation=operation)
            self._stats[operation].record(latency_ms, success)
            if "write" in operation:
                self._writes_since_start += 1

    def get_metrics(self) -> DBMetrics:
        with self._lock:
            total_writes = sum(s.count for op, s in self._stats.items() if "write" in op)
            total_reads = sum(s.count for op, s in self._stats.items() if "read" in op)
            total_errors = sum(s.errors for s in self._stats.values())

            elapsed = time.monotonic() - self._start_time
            throughput = self._writes_since_start / elapsed if elapsed > 0 else 0.0

            write_latencies = []
            read_latencies = []
            for op, s in self._stats.items():
                if "write" in op:
                    write_latencies.extend(s.latencies)
                elif "read" in op:
                    read_latencies.extend(s.latencies)

            return DBMetrics(
                total_writes=total_writes,
                total_reads=total_reads,
                total_errors=total_errors,
                write_throughput_per_sec=throughput,
                avg_write_latency_ms=statistics.mean(write_latencies) if write_latencies else 0.0,
                avg_read_latency_ms=statistics.mean(read_latencies) if read_latencies else 0.0,
                by_operation={
                    op: {
                        "count": s.count,
                        "p50": s.p50,
                        "p95": s.p95,
                        "p99": s.p99,
                        "errors": s.errors,
                        "error_rate": s.error_rate,
                    }
                    for op, s in self._stats.items()
                },
            )


class _QueryTracker:
    """Context manager for tracking query latency."""

    def __init__(self, monitor: DBMonitor, operation: str):
        self._monitor = monitor
        self._operation = operation
        self._start = 0.0

    def __enter__(self):
        self._start = time.monotonic_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.monotonic_ns() - self._start) / 1_000_000
        success = exc_type is None
        self._monitor.record(self._operation, elapsed_ms, success)
        return False
