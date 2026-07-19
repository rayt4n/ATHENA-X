"""Wire all Stage 6 components together."""
from __future__ import annotations
from athena_x_runtime_event_envelope import EventEnvelope, create_event, EventPriority
from athena_x_runtime_event_priority import PriorityQueue
from athena_x_runtime_event_correlation import CorrelationTracer
from athena_x_runtime_snapshot_coordinator import SnapshotCoordinator, SnapshotConfig
from athena_x_runtime_event_backpressure import BackpressureManager
from athena_x_runtime_event_log import EventLog
from athena_x_runtime_event_monitoring import EventMonitor
from athena_x_runtime_websocket_bridge import WebSocketBridge


def create_stage6_container():
    """Create a fully wired Stage 6 event bus system."""
    return {
        "priority_queue": PriorityQueue(),
        "correlation_tracer": CorrelationTracer(),
        "snapshot_coordinator": SnapshotCoordinator(),
        "backpressure_manager": BackpressureManager(),
        "event_log": EventLog(),
        "event_monitor": EventMonitor(),
        "websocket_bridge": WebSocketBridge(),
    }
