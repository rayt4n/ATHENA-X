"""Plugin Validation Workspace — top-level orchestrator.

Reuses InstitutionalWorkspace (Stage 16.3) for agent execution.
Adds:
  - ValidationDiscovery (Phase 1)
  - LogicScenarioRunner (Phase 5)
  - CrossValidator (Phase 6)
  - Per-plugin evidence reports (Phase 8)
  - Final certification table (Phase 9)
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field, asdict
from typing import Any

from athena_x_runtime_logger import get_logger
from athena_x_runtime_institutional_workspace import InstitutionalWorkspace
from athena_x_ta_base import Timeframe

from .discovery import ValidationDiscovery, ValidationInventory
from .logic.scenarios import LogicScenarioRunner, LOGIC_SCENARIOS, ScenarioRepo
from .crossval.reference import CrossValidator, ReferenceResult
from .evidence import PluginEvidence, build_evidence_report

log = get_logger("plugin-validation.workspace")


class PluginValidationWorkspace:
    """Top-level orchestrator for Stage 16.5 Plugin Validation.

    Lifecycle:
        workspace = PluginValidationWorkspace()
        workspace.discover()                            # Phase 1
        inventory = workspace.get_inventory()           # Phase 1 result
        result = await workspace.validate_agent("ta.ema")  # Phase 3+5+6+8
        result = await workspace.validate_all()         # all agents
        cert_table = workspace.get_certification_table()  # Phase 9
    """

    def __init__(self, event_bus=None):
        self._institutional_ws = InstitutionalWorkspace(event_bus=event_bus)
        self._discovery = ValidationDiscovery()
        self._scenario_runner = LogicScenarioRunner()
        self._cross_validator = CrossValidator(tolerance=0.05)
        self._inventory: ValidationInventory | None = None
        self._evidence: dict[str, PluginEvidence] = {}
        self._discovered = False

    # ─── Phase 1: Discovery ────────────────────────────────────────────

    def discover(self) -> ValidationInventory:
        """Discover every component in the repository."""
        self._inventory = self._discovery.discover_all()
        # Also discover the institutional workspace agents
        self._institutional_ws.discover()
        self._discovered = True
        return self._inventory

    def get_inventory(self) -> ValidationInventory:
        if not self._discovered:
            self.discover()
        return self._inventory

    def get_inventory_dict(self) -> dict:
        return self.get_inventory().to_dict()

    # ─── Phase 3+5+6+8: Validate one agent ────────────────────────────

    async def validate_agent(self, agent_id: str) -> PluginEvidence:
        """Validate one agent: run scenarios + cross-validate + build evidence."""
        if not self._discovered:
            self.discover()

        adapter = self._institutional_ws._registry.get(agent_id)
        if adapter is None:
            raise ValueError(f"Agent not found: {agent_id}")

        # Find agent metadata
        agent_meta = next(
            (a for a in self._inventory.runtime_agents if a.agent_id == agent_id),
            None
        )
        if agent_meta is None:
            raise ValueError(f"Agent metadata not found: {agent_id}")

        # Run logic scenarios
        scenarios = self._scenario_runner.scenarios_for(agent_id)
        scenario_results: list[dict] = []
        execution_results: list[dict] = []
        crossval_results: list[dict] = []

        for scenario in scenarios:
            bars, params = scenario.setup()
            repo = ScenarioRepo(bars)
            t0 = time.perf_counter()
            try:
                output = await adapter.execute("SPY", Timeframe.FIFTEEN_MIN, repo)
                latency_ms = (time.perf_counter() - t0) * 1000.0
                passed, message = scenario.check(output)

                # Extract confidence
                conf = None
                if hasattr(output, "confidence") and hasattr(output.confidence, "score"):
                    conf = output.confidence.score
                elif isinstance(output, dict):
                    conf = output.get("confidence")

                scenario_results.append({
                    "scenario_id": scenario.scenario_id,
                    "category": scenario.category,
                    "description": scenario.description,
                    "passed": passed,
                    "message": message,
                })
                execution_results.append({
                    "success": True,
                    "latency_ms": latency_ms,
                    "confidence": conf,
                })

                # Cross-validate (only for agents with reference implementations)
                cv = self._cross_validator.validate(agent_id, output, bars)
                if cv.reference != "N/A":
                    crossval_results.append(cv.to_dict())

            except Exception as e:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                scenario_results.append({
                    "scenario_id": scenario.scenario_id,
                    "category": scenario.category,
                    "description": scenario.description,
                    "passed": False,
                    "message": f"EXCEPTION: {type(e).__name__}: {e}",
                })
                execution_results.append({
                    "success": False,
                    "latency_ms": latency_ms,
                    "error": str(e)[:200],
                })

        # Build evidence report
        evidence = build_evidence_report(
            agent_id=agent_id,
            name=adapter.name,
            layer=adapter.layer,
            category=adapter.category,
            crossval_results=crossval_results,
            scenario_results=scenario_results,
            execution_results=execution_results,
            dependencies=list(agent_meta.dependencies),
        )
        self._evidence[agent_id] = evidence
        return evidence

    # ─── Validate all agents ──────────────────────────────────────────

    async def validate_all(self) -> dict[str, PluginEvidence]:
        """Validate every runtime agent."""
        if not self._discovered:
            self.discover()
        for agent_meta in self._inventory.runtime_agents:
            try:
                await self.validate_agent(agent_meta.agent_id)
            except Exception as e:
                log.warning("validate_agent_failed", agent_id=agent_meta.agent_id, error=str(e))
        return self._evidence

    # ─── Phase 9: Certification table ─────────────────────────────────

    def get_certification_table(self) -> list[dict]:
        """Phase 9 — final certification table."""
        table = []
        for agent_id, ev in self._evidence.items():
            table.append({
                "agent_id": agent_id,
                "name": ev.name,
                "layer": ev.layer,
                "category": ev.category,
                "math_score": round(ev.math_score, 1),
                "logic_score": round(ev.logic_score, 1),
                "runtime_score": round(ev.runtime_score, 1),
                "performance_score": round(ev.performance_score, 1),
                "avg_latency_ms": round(ev.avg_latency_ms, 3),
                "avg_confidence": round(ev.avg_confidence, 3),
                "error_count": ev.error_count,
                "certification": ev.certification,
                "failure_cases_count": len(ev.failure_cases),
            })
        # Sort by certification priority then by overall score
        cert_priority = {"CERTIFIED": 0, "PROVISIONAL": 1, "NEEDS IMPROVEMENT": 2}
        table.sort(key=lambda x: (
            cert_priority.get(x["certification"], 3),
            -(x["math_score"] + x["logic_score"] + x["runtime_score"] + x["performance_score"]) / 4
        ))
        return table

    def get_summary(self) -> dict:
        """Get validation summary."""
        table = self.get_certification_table()
        cert_counts = {"CERTIFIED": 0, "PROVISIONAL": 0, "NEEDS IMPROVEMENT": 0}
        for row in table:
            cert_counts[row["certification"]] = cert_counts.get(row["certification"], 0) + 1
        avg_math = sum(r["math_score"] for r in table) / max(len(table), 1)
        avg_logic = sum(r["logic_score"] for r in table) / max(len(table), 1)
        avg_runtime = sum(r["runtime_score"] for r in table) / max(len(table), 1)
        avg_perf = sum(r["performance_score"] for r in table) / max(len(table), 1)
        return {
            "total_agents_validated": len(table),
            "certification_counts": cert_counts,
            "avg_math_score": round(avg_math, 1),
            "avg_logic_score": round(avg_logic, 1),
            "avg_runtime_score": round(avg_runtime, 1),
            "avg_performance_score": round(avg_perf, 1),
            "total_failure_cases": sum(r["failure_cases_count"] for r in table),
            "total_errors": sum(r["error_count"] for r in table),
            "pandas_ta_available": self._cross_validator.available(),
        }

    # ─── Phase 3: Execute one agent standalone (raw pipeline view) ────

    async def execute_agent_raw(self, agent_id: str, bars: list[dict] | None = None) -> dict:
        """Execute one agent with raw input/output visible for dashboard.

        Returns:
            {
                "agent_id": ...,
                "raw_input": {bars, params},
                "raw_output": TAOutput serialized,
                "normalized_output": {agent, value, confidence, indicator},
                "validation_result": {passed, message},
                "evidence": PluginEvidence summary,
            }
        """
        if not self._discovered:
            self.discover()
        adapter = self._institutional_ws._registry.get(agent_id)
        if adapter is None:
            raise ValueError(f"Agent not found: {agent_id}")

        # Generate default bars if not provided
        if bars is None:
            from .logic.scenarios import _bullish_trend_bars
            bars = _bullish_trend_bars(60)

        repo = ScenarioRepo(bars)
        t0 = time.perf_counter()
        try:
            output = await adapter.execute("SPY", Timeframe.FIFTEEN_MIN, repo)
            latency_ms = (time.perf_counter() - t0) * 1000.0

            # Serialize output
            raw_output = _serialize_output(output)

            # Normalize
            normalized = {
                "agent": getattr(output, "agent", None) or raw_output.get("agent"),
                "indicator": getattr(output, "indicator", None) or raw_output.get("indicator"),
                "value": getattr(output, "value", None) if hasattr(output, "value") else raw_output.get("value"),
                "confidence": (
                    output.confidence.score if hasattr(output, "confidence") and hasattr(output.confidence, "score")
                    else raw_output.get("confidence")
                ),
                "timeframe": getattr(output, "timeframe", None) or raw_output.get("timeframe"),
            }

            # Cross-validate
            cv = self._cross_validator.validate(agent_id, output, bars)

            return {
                "agent_id": agent_id,
                "raw_input": {
                    "symbol": "SPY",
                    "timeframe": "15m",
                    "bar_count": len(bars),
                    "first_bar": bars[0] if bars else None,
                    "last_bar": bars[-1] if bars else None,
                },
                "raw_output": raw_output,
                "normalized_output": normalized,
                "cross_validation": cv.to_dict(),
                "execution_time_ms": latency_ms,
                "success": True,
            }
        except Exception as e:
            return {
                "agent_id": agent_id,
                "raw_input": {"bar_count": len(bars) if bars else 0},
                "raw_output": None,
                "normalized_output": None,
                "cross_validation": None,
                "execution_time_ms": (time.perf_counter() - t0) * 1000.0,
                "success": False,
                "error": str(e)[:300],
            }

    # ─── Phase 4: Complete pipeline execution ─────────────────────────

    async def execute_complete_pipeline(self, bars: list[dict] | None = None) -> dict:
        """Execute the complete pipeline: Market Data → Provider → Layer 1-5 → Workspace → Dashboard.

        Reuses InstitutionalWorkspace.execute_request() and adds pipeline-step visibility.
        """
        if not self._discovered:
            self.discover()

        # Generate default bars
        if bars is None:
            from .logic.scenarios import _bullish_trend_bars
            bars = _bullish_trend_bars(60)

        pipeline_steps = []

        # Step 1: Market Data (simulated)
        pipeline_steps.append({
            "step": 1,
            "name": "Market Data",
            "component": "FakeMarketRepository",
            "status": "ok",
            "details": {"bar_count": len(bars), "symbol": "SPY", "timeframe": "15m"},
        })

        # Step 2: Provider (simulated — Yahoo adapter would be used in production)
        pipeline_steps.append({
            "step": 2,
            "name": "Provider",
            "component": "SimulatedProvider (would be YahooAdapter in production)",
            "status": "ok",
            "details": {"bars_fetched": len(bars)},
        })

        # Steps 3-7: Layer 1-5 via InstitutionalWorkspace.execute_request
        repo = ScenarioRepo(bars)
        ws_result = await self._institutional_ws.execute_request(
            "SPY", Timeframe.FIFTEEN_MIN, repo, data_provider="simulated"
        )

        # Extract per-layer results
        layer_events = {}
        for event in ws_result["trace"]["events"]:
            layer = str(event["layer"])
            if layer not in layer_events:
                layer_events[layer] = []
            layer_events[layer].append(event)

        layer_names = {
            "1": "Layer 1: Market Structure",
            "2": "Layer 2: Indicators",
            "3": "Layer 3: Institutional",
            "4": "Layer 4: Consensus",
            "5": "Layer 5: Supervisor",
        }
        for layer_num in ["1", "2", "3", "4", "5"]:
            events = layer_events.get(layer_num, [])
            pipeline_steps.append({
                "step": int(layer_num) + 2,
                "name": layer_names.get(layer_num, f"Layer {layer_num}"),
                "component": f"{len(events)} agents",
                "status": "ok" if all(e["success"] for e in events) else "error",
                "details": {
                    "agents_executed": len(events),
                    "total_duration_ms": sum(e["duration_ms"] for e in events),
                    "agents": [e["agent_id"] for e in events],
                },
            })

        # Step 8: Workspace (Institutional Workspace aggregation)
        pipeline_steps.append({
            "step": 8,
            "name": "Workspace",
            "component": "InstitutionalWorkspace.execute_request()",
            "status": "ok",
            "details": {
                "request_id": ws_result["request_id"],
                "total_duration_ms": ws_result["trace"]["total_duration_ms"],
                "final_conclusion": ws_result["final_conclusion"],
                "contributors": len(ws_result["trace"]["contributor_chain"]),
            },
        })

        # Step 9: Dashboard (would render the result)
        pipeline_steps.append({
            "step": 9,
            "name": "Dashboard",
            "component": "PluginValidationWorkspace (this dashboard)",
            "status": "ok",
            "details": {"rendered": True},
        })

        return {
            "pipeline_steps": pipeline_steps,
            "workspace_result": ws_result,
            "total_duration_ms": ws_result["trace"]["total_duration_ms"],
        }


def _serialize_output(output: Any) -> Any:
    """Convert TAOutput to JSON-safe dict."""
    if output is None:
        return None
    if hasattr(output, "to_event_payload"):
        return output.to_event_payload()
    if hasattr(output, "__dict__"):
        try:
            return {
                k: _safe(v)
                for k, v in output.__dict__.items()
                if not k.startswith("_")
            }
        except Exception:
            return str(output)
    if isinstance(output, dict):
        return {k: _safe(v) for k, v in output.items()}
    return _safe(output)


def _safe(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, list):
        return [_safe(x) for x in v[:30]]
    if isinstance(v, dict):
        return {str(k): _safe(val) for k, val in list(v.items())[:30]}
    return str(v)[:200]
