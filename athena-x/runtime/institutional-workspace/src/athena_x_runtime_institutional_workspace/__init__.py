"""ATHENA-X Stage 16.3 — Institutional Workspace Integration.

Exposes the verified agent runtime (Layer 1–5 + Intelligence Hubs) as a
unified plugin-style registry, with auto-discovery, request tracing, and
evidence generation. Does NOT duplicate any verified agent logic.

Public API:
    from athena_x_runtime_institutional_workspace import (
        InstitutionalWorkspace, AgentAdapter, TraceRecord, EvidenceReport,
    )
"""
from .discovery import RuntimeDiscovery, DiscoveredAgent
from .adapters.base import AgentAdapter, adapt_agent
from .adapters.registry import AdapterRegistry
from .tracer import RequestTracer, TraceRecord, TraceEvent
from .evidence import EvidenceReport, EvidenceContribution, build_evidence_report, evidence_summary_text
from .workspace import InstitutionalWorkspace

__all__ = [
    "InstitutionalWorkspace",
    "AgentAdapter",
    "adapt_agent",
    "AdapterRegistry",
    "RuntimeDiscovery",
    "DiscoveredAgent",
    "RequestTracer",
    "TraceRecord",
    "TraceEvent",
    "EvidenceReport",
    "EvidenceContribution",
    "build_evidence_report",
    "evidence_summary_text",
]
__version__ = "0.1.0"
