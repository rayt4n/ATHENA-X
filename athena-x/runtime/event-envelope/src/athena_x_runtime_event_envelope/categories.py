"""5 event categories with their event types (Stage 6 req 1)."""
from __future__ import annotations


EVENT_CATEGORIES = {
    "market": [
        "market:raw",        # Raw provider output
        "market:validated",  # Passed validation
        "market:canonical",  # Standardized
        "market:updated",    # Latest quote updated
        "market:closed",     # Bar closed
        "market:snapshot",   # Synchronized snapshot (from SnapshotCoordinator)
    ],
    "options": [
        "options:chain",
        "options:flow",
        "options:oi",
        "options:greeks",
        "options:iv",
        "options:gex",
    ],
    "news": [
        "news:breaking",
        "news:macro",
        "news:earnings",
        "news:mag7",
    ],
    "ai": [
        "ai:technical",
        "ai:forecast",
        "ai:probability",
        "ai:validation",
        "ai:consensus",
    ],
    "reports": [
        "report:started",
        "report:partial",
        "report:completed",
    ],
    "system": [
        "system:heartbeat",
        "system:error",
        "system:warning",
        "system:provider",
        "system:health",
    ],
}


def list_event_types(category: str | None = None) -> list[str]:
    """List all event types, optionally filtered by category."""
    if category:
        return EVENT_CATEGORIES.get(category, [])
    all_types = []
    for types in EVENT_CATEGORIES.values():
        all_types.extend(types)
    return all_types
