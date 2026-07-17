"""Tests for DB monitoring (Stage 5 req 10)."""
import pytest
import time
from athena_x_runtime_db_monitoring import DBMonitor


def test_track_records_latency():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        time.sleep(0.001)
    metrics = monitor.get_metrics()
    assert metrics.total_writes == 1
    assert metrics.avg_write_latency_ms > 0


def test_track_records_errors():
    monitor = DBMonitor()
    try:
        with monitor.track("write_quote"):
            raise RuntimeError("test error")
    except RuntimeError:
        pass
    metrics = monitor.get_metrics()
    assert metrics.total_errors == 1


def test_metrics_track_writes_and_reads():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        pass
    with monitor.track("write_bar"):
        pass
    with monitor.track("read_quote"):
        pass
    metrics = monitor.get_metrics()
    assert metrics.total_writes == 2
    assert metrics.total_reads == 1


def test_by_operation_breakdown():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        pass
    with monitor.track("write_quote"):
        pass
    with monitor.track("read_quote"):
        pass
    metrics = monitor.get_metrics()
    assert "write_quote" in metrics.by_operation
    assert metrics.by_operation["write_quote"]["count"] == 2
    assert "read_quote" in metrics.by_operation
    assert metrics.by_operation["read_quote"]["count"] == 1


def test_p50_p95_p99_computed():
    monitor = DBMonitor()
    for i in range(100):
        with monitor.track("write_quote"):
            time.sleep(0.0001 * (i + 1))  # increasing latency
    metrics = monitor.get_metrics()
    stats = metrics.by_operation["write_quote"]
    assert stats["p50"] > 0
    assert stats["p95"] >= stats["p50"]
    assert stats["p99"] >= stats["p95"]


def test_write_throughput():
    monitor = DBMonitor()
    for _ in range(10):
        with monitor.track("write_quote"):
            pass
    metrics = monitor.get_metrics()
    assert metrics.write_throughput_per_sec > 0
