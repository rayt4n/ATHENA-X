"""Institutional Workspace — top-level orchestrator.

Provides:
  - discover() — auto-discover all runtime agents and register as adapters
  - execute_request(symbol, timeframe, repo) — full Layer 1→5 pipeline with tracing

  - execute_agent(agent_id, symbol, timeframe, repo) — single agent standalone

  - get_evidence_report(request_id) — evidence for a past request

  - list_components() — full inventory for the dashboard
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from athena_x_runtime_logger import get_logger
from athena_x_ta_base import Timeframe

from .adapters import AdapterRegistry, AgentAdapter
from .tracer import RequestTracer, TraceRecord
from .evidence import EvidenceReport, build_evidence_report

log = get_logger("institutional-workspace.workspace")


class InstitutionalWorkspace:
    """Top-level orchestrator for the Stage 16.3 Institutional Workspace.

    Lifecycle:
        workspace = InstitutionalWorkspace()
        workspace.discover()                              # auto-discover all agents
        components = workspace.list_components()          # for dashboard
        result = await workspace.execute_request(...)     # full pipeline
        result = await workspace.execute_agent("ta.ema", ...)  # standalone
    """

    def __init__(self, event_bus=None):
        self._registry = AdapterRegistry()
        self._tracer = RequestTracer()
        self._event_bus = event_bus
        self._history: list[TraceRecord] = []
        self._discovered = False

    # ─── Discovery ───────────────────────────────────────────────────────

    def discover(self) -> int:
        """Auto-discover all runtime agents and register them as adapters."""
        count = self._registry.discover_and_register()
        self._discovered = True
        log.info("workspace_discovered", adapter_count=count)
        return count

    def list_components(self) -> list[dict]:
        """Return full inventory of every runtime component for the dashboard."""
        if not self._discovered:
            self.discover()
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "category": a.category,
                "layer": a.layer,
                "description": a.description,
                "inputs": list(a.inputs),
                "outputs": list(a.outputs),
                "dependencies": list(a.dependencies),
                "module_path": a.module_path,
                "manifest": a.manifest.to_dict(),
                "health": a.health(),
            }
            for a in self._registry.list_all()
        ]

    def get_component(self, agent_id: str) -> dict | None:
        """Get one component's full metadata."""
        a = self._registry.get(agent_id)
        if a is None:
            return None
        return {
            "agent_id": a.agent_id,
            "name": a.name,
            "category": a.category,
            "layer": a.layer,
            "description": a.description,
            "inputs": list(a.inputs),
            "outputs": list(a.outputs),
            "dependencies": list(a.dependencies),
            "module_path": a.module_path,
            "manifest": a.manifest.to_dict(),
            "health": a.health(),
        }

    def get_summary(self) -> dict:
        return self._registry.get_summary()

    # ─── Standalone Execution ───────────────────────────────────────────

    async def execute_agent(
        self,
        agent_id: str,
        symbol: str,
        timeframe: Timeframe,
        repo: Any,
    ) -> dict:
        """Execute a single agent standalone. Returns a result dict with trace."""
        if not self._discovered:
            self.discover()
        adapter = self._registry.get(agent_id)
        if adapter is None:
            raise ValueError(f"Agent not found: {agent_id}")

        # Start a trace
        record = self._tracer.start_request(
            symbol=symbol,
            timeframe=str(timeframe.value if hasattr(timeframe, "value") else timeframe),
            data_provider=type(repo).__name__,
        )

        try:
            async with self._tracer.trace_agent(
                adapter.agent_id, adapter.layer, adapter.category
            ):
                output = await adapter.execute(symbol, timeframe, repo, self._event_bus)
                self._tracer.record_output(output)

            # Build conclusion from output
            conclusion = ""
            if hasattr(output, "indicator") and hasattr(output, "value"):
                conclusion = f"{output.indicator}={output.value}"

            self._tracer.finish_request(record, final_conclusion=conclusion)
            self._history.append(record)

            return {
                "agent_id": agent_id,
                "output": _serialize_output(output),
                "trace": record.to_dict(),
                "evidence": build_evidence_report(record).to_dict(),
            }
        except Exception as e:
            self._tracer.finish_request(
                record, success=False, error=f"{type(e).__name__}: {e}"
            )
            self._history.append(record)
            raise

    # ─── Full Pipeline Execution ────────────────────────────────────────

    async def execute_request(
        self,
        symbol: str,
        timeframe: Timeframe,
        repo: Any,
        data_provider: str = "unknown",
    ) -> dict:
        """Execute the full Layer 1→5 pipeline with tracing.

        Returns a dict containing:
          - final_conclusion
          - trace (full event list)
          - evidence (per-conclusion contributor breakdown)
          - all_outputs (per-agent raw outputs)
        """
        if not self._discovered:
            self.discover()

        record = self._tracer.start_request(
            symbol=symbol,
            timeframe=str(timeframe.value if hasattr(timeframe, "value") else timeframe),
            data_provider=data_provider,
        )

        all_outputs: dict[str, Any] = {}

        try:
            # Execute Layer 1 (market structure) — 6 agents
            for adapter in self._registry.list_by_layer(1):
                async with self._tracer.trace_agent(
                    adapter.agent_id, adapter.layer, adapter.category
                ):
                    out = await adapter.execute(symbol, timeframe, repo, self._event_bus)
                    self._tracer.record_output(out)
                    all_outputs[adapter.agent_id] = _serialize_output(out)

            # Execute Layer 2 (indicators) — 8 agents
            for adapter in self._registry.list_by_layer(2):
                async with self._tracer.trace_agent(
                    adapter.agent_id, adapter.layer, adapter.category
                ):
                    out = await adapter.execute(symbol, timeframe, repo, self._event_bus)
                    self._tracer.record_output(out)
                    all_outputs[adapter.agent_id] = _serialize_output(out)

            # Execute Layer 3 (institutional) — 8 agents
            for adapter in self._registry.list_by_layer(3):
                async with self._tracer.trace_agent(
                    adapter.agent_id, adapter.layer, adapter.category
                ):
                    out = await adapter.execute(symbol, timeframe, repo, self._event_bus)
                    self._tracer.record_output(out)
                    all_outputs[adapter.agent_id] = _serialize_output(out)

            # Execute Layer 4 (consensus) — 1 agent
            for adapter in self._registry.list_by_layer(4):
                async with self._tracer.trace_agent(
                    adapter.agent_id, adapter.layer, adapter.category
                ):
                    out = await adapter.execute(symbol, timeframe, repo, self._event_bus)
                    self._tracer.record_output(out)
                    all_outputs[adapter.agent_id] = _serialize_output(out)

            # Build final conclusion from consensus output
            consensus_out = all_outputs.get("ta.consensus")
            if consensus_out and isinstance(consensus_out, dict):
                final_conclusion = f"alignment={consensus_out.get('alignment', 'unknown')}"
            else:
                final_conclusion = "(pipeline completed; no consensus)"

            self._tracer.finish_request(record, final_conclusion=final_conclusion)
            self._history.append(record)

            evidence = build_evidence_report(record)

            return {
                "request_id": record.request_id,
                "symbol": record.symbol,
                "timeframe": record.timeframe,
                "final_conclusion": final_conclusion,
                "trace": record.to_dict(),
                "evidence": evidence.to_dict(),
                "all_outputs": all_outputs,
            }
        except Exception as e:
            self._tracer.finish_request(
                record, success=False, error=f"{type(e).__name__}: {e}"
            )
            self._history.append(record)
            raise

    # ─── History & Evidence ─────────────────────────────────────────────

    def get_history(self, limit: int = 50) -> list[dict]:
        """Return recent trace records (most recent first)."""
        recent = self._history[-limit:][::-1]
        return [r.to_dict() for r in recent]

    def get_evidence_report(self, request_id: str) -> dict | None:
        """Get the evidence report for a past request."""
        for record in self._history:
            if record.request_id == request_id:
                return build_evidence_report(record).to_dict()
        return None


def _serialize_output(output: Any) -> Any:
    """Convert a TAOutput or other object into a JSON-serializable dict."""
    if output is None:
        return None
    if hasattr(output, "to_event_payload"):
        return output.to_event_payload()
    if hasattr(output, "__dict__"):
        try:
            return {
                k: _safe_serialize(v)
                for k, v in output.__dict__.items()
                if not k.startswith("_")
            }
        except Exception:
            return str(output)
    if isinstance(output, dict):
        return {k: _safe_serialize(v) for k, v in output.items()}
    return _safe_serialize(output)


def _safe_serialize(v: Any) -> Any:
    """Make a value JSON-safe."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return [_safe_serialize(x) for x in v][:50]  # cap at 50 items
    if isinstance(v, dict):
        return {str(k): _safe_serialize(val) for k, val in list(v.items())[:50]}
    return str(v)[:200]
