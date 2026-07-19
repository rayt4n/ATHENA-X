"""Evidence Report — for each conclusion in a final analysis, list which agents contributed.

Given a TraceRecord, produces an EvidenceReport that maps each conclusion
to its contributing agents, with their confidence scores, outputs, and
timing. Used by the dashboard to show "why did the system conclude X?"
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .tracer import TraceRecord, TraceEvent


@dataclass
class EvidenceContribution:
    """One agent's contribution to one conclusion."""
    agent_id: str
    layer: int | str
    category: str
    output_summary: str
    confidence: float | None
    duration_ms: float
    role: str = ""           # "primary" | "supporting" | "contextual"

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "layer": self.layer,
            "category": self.category,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
            "duration_ms": round(self.duration_ms, 3),
            "role": self.role,
        }


@dataclass
class EvidenceReport:
    """Evidence report mapping conclusions to contributing agents."""
    request_id: str
    symbol: str
    timeframe: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    final_conclusion: str = ""
    total_agents_executed: int = 0
    total_duration_ms: float = 0.0
    primary_contributors: list[EvidenceContribution] = field(default_factory=list)
    supporting_contributors: list[EvidenceContribution] = field(default_factory=list)
    contextual_contributors: list[EvidenceContribution] = field(default_factory=list)
    layer_breakdown: dict[str, int] = field(default_factory=dict)
    failed_agents: list[EvidenceContribution] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "generated_at": self.generated_at.isoformat(),
            "final_conclusion": self.final_conclusion,
            "total_agents_executed": self.total_agents_executed,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "primary_contributors": [c.to_dict() for c in self.primary_contributors],
            "supporting_contributors": [c.to_dict() for c in self.supporting_contributors],
            "contextual_contributors": [c.to_dict() for c in self.contextual_contributors],
            "layer_breakdown": self.layer_breakdown,
            "failed_agents": [c.to_dict() for c in self.failed_agents],
        }


def _classify_role(agent_id: str, layer: int | str, final_conclusion: str) -> str:
    """Classify an agent's role in reaching the final conclusion.

    Layer 5 (supervisor) and Layer 4 (consensus) are always 'primary'.
    Layer 3 (institutional) agents are 'primary' if their output matches the conclusion keyword.
    Layer 2 (indicators) are 'supporting'.
    Layer 1 (market structure) are 'contextual'.
    Hubs are 'primary' for their domain.
    """
    if isinstance(layer, str):
        if layer == "hub":
            return "primary"
        return "contextual"
    if layer == 5:
        return "primary"
    if layer == 4:
        return "primary"
    if layer == 3:
        return "primary"
    if layer == 2:
        return "supporting"
    if layer == 1:
        return "contextual"
    return "contextual"


def build_evidence_report(trace: TraceRecord) -> EvidenceReport:
    """Build an EvidenceReport from a TraceRecord."""
    report = EvidenceReport(
        request_id=trace.request_id,
        symbol=trace.symbol,
        timeframe=trace.timeframe,
        final_conclusion=trace.final_conclusion,
        total_agents_executed=len(trace.events),
        total_duration_ms=trace.total_duration_ms,
    )

    layer_counts: dict[str, int] = {}
    for event in trace.events:
        layer_key = str(event.layer)
        layer_counts[layer_key] = layer_counts.get(layer_key, 0) + 1

        contribution = EvidenceContribution(
            agent_id=event.agent_id,
            layer=event.layer,
            category=event.category,
            output_summary=event.output_summary,
            confidence=event.confidence,
            duration_ms=event.duration_ms,
        )

        if not event.success:
            report.failed_agents.append(contribution)
            continue

        contribution.role = _classify_role(event.agent_id, event.layer, trace.final_conclusion)
        if contribution.role == "primary":
            report.primary_contributors.append(contribution)
        elif contribution.role == "supporting":
            report.supporting_contributors.append(contribution)
        else:
            report.contextual_contributors.append(contribution)

    report.layer_breakdown = layer_counts
    return report


def evidence_summary_text(report: EvidenceReport) -> str:
    """Human-readable summary of the evidence report."""
    lines = [
        f"Evidence Report for {report.symbol} ({report.timeframe})",
        f"Final conclusion: {report.final_conclusion or '(none)'}",
        f"Total agents executed: {report.total_agents_executed} in {report.total_duration_ms:.1f} ms",
        "",
        f"Primary contributors ({len(report.primary_contributors)}):",
    ]
    for c in report.primary_contributors:
        conf = f" conf={c.confidence:.2f}" if c.confidence is not None else ""
        lines.append(f"  - {c.agent_id} (L{c.layer}){conf}: {c.output_summary}")
    lines.append("")
    lines.append(f"Supporting contributors ({len(report.supporting_contributors)}):")
    for c in report.supporting_contributors:
        conf = f" conf={c.confidence:.2f}" if c.confidence is not None else ""
        lines.append(f"  - {c.agent_id} (L{c.layer}){conf}: {c.output_summary}")
    lines.append("")
    lines.append(f"Contextual contributors ({len(report.contextual_contributors)}):")
    for c in report.contextual_contributors:
        lines.append(f"  - {c.agent_id} (L{c.layer}): {c.output_summary}")
    if report.failed_agents:
        lines.append("")
        lines.append(f"Failed agents ({len(report.failed_agents)}):")
        for c in report.failed_agents:
            lines.append(f"  - {c.agent_id} (L{c.layer}): FAILED")
    return "\n".join(lines)
