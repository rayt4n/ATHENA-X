"""Tests for Institutional Workspace — Stage 16.3 acceptance."""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from athena_x_runtime_repository_interface import QueryResult
from athena_x_ta_base import Timeframe

from athena_x_runtime_institutional_workspace import (
    InstitutionalWorkspace,
    RuntimeDiscovery,
    AdapterRegistry,
    RequestTracer,
    build_evidence_report,
    evidence_summary_text,
)


# ============================================================================
# Fake repo (deterministic OHLCV bars)
# ============================================================================

class FakeRepo:
    async def query_bars(self, symbol, timeframe, start, end):
        bars = []
        base_price = 450.0 if symbol == "SPY" else 100.0
        base = datetime.now(timezone.utc) - timedelta(days=200)
        for i in range(200):
            ts = base + timedelta(minutes=i * 15)
            price = base_price + i * 0.1 + (i % 7) * 0.5 - (i % 3) * 0.3
            bars.append({
                "symbol": symbol, "timeframe": timeframe,
                "timestamp": ts.isoformat(),
                "open": round(price - 0.2, 4),
                "high": round(price + 0.5, 4),
                "low": round(price - 0.5, 4),
                "close": round(price, 4),
                "volume": 100000 + i * 100,
            })
        return QueryResult(records=bars, count=len(bars))

    async def read_quote(self, symbol): return None
    async def write_quote(self, record): pass
    async def write_bar(self, record): pass
    async def supersede(self, record_id, corrected): pass
    async def get_history(self, symbol, limit=100):
        return QueryResult(records=[], count=0)


@pytest.fixture
def repo():
    return FakeRepo()


# ============================================================================
# Phase 1 — Discovery
# ============================================================================

class TestDiscovery:
    def test_runtime_discovery_finds_ta_layers(self):
        d = RuntimeDiscovery()
        agents = d.discover_all()
        # Should find at least 20 TA agents (Layer 1:6 + Layer 2:8 + Layer 3:8 + Layer 4:1 + Layer 5:1 + Snapshot:1 = 25)
        assert len(agents) >= 20

    def test_runtime_discovery_finds_layer2_indicators(self):
        d = RuntimeDiscovery()
        layer2 = d.discover_by_layer(2)
        # Should find EMA, SMA, VWAP, RSI, MACD, ADX, ATR, Bollinger = 8 agents
        assert len(layer2) == 8
        names = [a.agent_id for a in layer2]
        assert "ta.ema" in names
        assert "ta.rsi" in names
        assert "ta.macd" in names

    def test_runtime_discovery_finds_layer1_market_structure(self):
        d = RuntimeDiscovery()
        layer1 = d.discover_by_layer(1)
        # Should find 6 Layer 1 agents
        assert len(layer1) == 6
        names = [a.agent_id for a in layer1]
        assert "ta.trend" in names
        assert "ta.swing" in names
        assert "ta.support_resistance" in names
        assert "ta.liquidity" in names
        assert "ta.volume_profile" in names
        assert "ta.multi_timeframe_data" in names

    def test_runtime_discovery_summary(self):
        d = RuntimeDiscovery()
        s = d.get_summary()
        assert s["total_agents"] >= 20
        assert "1" in s["by_layer"]
        assert "2" in s["by_layer"]
        assert "3" in s["by_layer"]

    def test_discovered_agent_has_required_metadata(self):
        d = RuntimeDiscovery()
        agents = d.discover_all()
        ema = next(a for a in agents if a.agent_id == "ta.ema")
        assert ema.class_name == "EMAAgent"
        assert ema.layer == 2
        assert ema.category == "indicator"
        assert "athena_x_ta_layer2_indicators" in ema.module_path
        assert ema.compute_signature.startswith("async compute")


# ============================================================================
# Phase 2 — Adapter Registry
# ============================================================================

class TestAdapterRegistry:
    def test_registry_discovers_and_registers(self):
        r = AdapterRegistry()
        count = r.discover_and_register()
        assert count >= 20

    def test_registry_get_returns_adapter(self):
        r = AdapterRegistry()
        r.discover_and_register()
        adapter = r.get("ta.ema")
        assert adapter is not None
        assert adapter.agent_id == "ta.ema"
        assert adapter.layer == 2

    def test_registry_list_by_layer(self):
        r = AdapterRegistry()
        r.discover_and_register()
        layer2 = r.list_by_layer(2)
        assert len(layer2) == 8

    def test_registry_manifests_are_plugin_compatible(self):
        r = AdapterRegistry()
        r.discover_and_register()
        manifests = r.list_manifests()
        assert len(manifests) >= 20
        ema_manifest = next(m for m in manifests if m["id"] == "ta.ema")
        assert ema_manifest["category"] == "indicator"
        assert ema_manifest["layer"] == "2"
        assert ema_manifest["runtime_path"].startswith("athena_x_ta_layer2_indicators")
        assert ema_manifest["author"] == "ATHENA-X Stage 16.3"

    def test_registry_summary(self):
        r = AdapterRegistry()
        r.discover_and_register()
        s = r.get_summary()
        assert s["total_adapters"] >= 20
        assert "1" in s["by_layer"]
        assert "2" in s["by_layer"]


# ============================================================================
# Phase 3 — Standalone Agent Execution
# ============================================================================

class TestStandaloneExecution:
    async def test_execute_ema_standalone(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_agent("ta.ema", "SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result["agent_id"] == "ta.ema"
        assert "output" in result
        assert "trace" in result
        assert "evidence" in result
        assert result["trace"]["success"] is True
        # Output should have an EMA value
        out = result["output"]
        assert out.get("indicator", "").startswith("EMA")
        assert out.get("value") is not None

    async def test_execute_rsi_returns_0_to_100(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_agent("ta.rsi", "SPY", Timeframe.FIFTEEN_MIN, repo)
        out = result["output"]
        assert 0 <= out["value"] <= 100

    async def test_execute_trend_returns_bullish_bearish_or_ranging(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_agent("ta.trend", "SPY", Timeframe.FIFTEEN_MIN, repo)
        out = result["output"]
        assert out["value"] in ("bullish", "bearish", "ranging", "unknown")

    async def test_execute_unknown_agent_raises(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        with pytest.raises(ValueError):
            await ws.execute_agent("ta.does_not_exist", "SPY", Timeframe.FIFTEEN_MIN, repo)

    async def test_standalone_execution_produces_evidence(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_agent("ta.macd", "SPY", Timeframe.FIFTEEN_MIN, repo)
        evidence = result["evidence"]
        assert evidence["total_agents_executed"] == 1
        assert len(evidence["primary_contributors"]) + \
               len(evidence["supporting_contributors"]) + \
               len(evidence["contextual_contributors"]) == 1


# ============================================================================
# Phase 4 — Full Pipeline Execution
# ============================================================================

class TestFullPipeline:
    async def test_execute_request_runs_all_layers(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_request("SPY", Timeframe.FIFTEEN_MIN, repo, data_provider="fake")

        assert "request_id" in result
        assert result["symbol"] == "SPY"
        assert result["timeframe"].lower() == "15m"
        assert "final_conclusion" in result
        assert "trace" in result
        assert "evidence" in result
        assert "all_outputs" in result

        # Should have executed multiple agents
        trace = result["trace"]
        assert len(trace["events"]) >= 15  # at least Layer 1+2+3+4

        # Should have outputs from multiple layers
        outputs = result["all_outputs"]
        assert "ta.ema" in outputs
        assert "ta.rsi" in outputs
        assert "ta.trend" in outputs

    async def test_pipeline_produces_evidence_report(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_request("SPY", Timeframe.FIFTEEN_MIN, repo)
        evidence = result["evidence"]
        assert evidence["total_agents_executed"] >= 15
        assert "primary_contributors" in evidence
        assert "supporting_contributors" in evidence
        assert "contextual_contributors" in evidence
        assert "layer_breakdown" in evidence

    async def test_pipeline_records_history(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        await ws.execute_request("SPY", Timeframe.FIFTEEN_MIN, repo)
        history = ws.get_history()
        assert len(history) >= 1
        assert history[0]["symbol"] == "SPY"

    async def test_evidence_report_retrievable_by_request_id(self, repo):
        ws = InstitutionalWorkspace()
        ws.discover()
        result = await ws.execute_request("SPY", Timeframe.FIFTEEN_MIN, repo)
        rid = result["request_id"]
        evidence = ws.get_evidence_report(rid)
        assert evidence is not None
        assert evidence["request_id"] == rid


# ============================================================================
# Phase 5 — Tracer
# ============================================================================

class TestTracer:
    def test_tracer_start_finish(self):
        t = RequestTracer()
        record = t.start_request("SPY", "15m", data_provider="fake")
        assert record.symbol == "SPY"
        assert record.timeframe == "15m"
        assert record.data_provider == "fake"
        t.finish_request(record, final_conclusion="test")
        assert record.finished_at is not None
        assert record.total_duration_ms >= 0
        assert record.final_conclusion == "test"

    async def test_tracer_records_event(self, repo):
        t = RequestTracer()
        record = t.start_request("SPY", "15m")
        async with t.trace_agent("ta.ema", layer=2, category="indicator"):
            await asyncio.sleep(0.001)
        t.finish_request(record)
        assert len(record.events) == 1
        event = record.events[0]
        assert event.agent_id == "ta.ema"
        assert event.duration_ms > 0
        assert event.success is True


# ============================================================================
# Phase 6 — Evidence
# ============================================================================

class TestEvidence:
    def test_evidence_report_classifies_by_layer(self, repo):
        """Layer 4/5 → primary; Layer 2 → supporting; Layer 1 → contextual."""
        from athena_x_runtime_institutional_workspace.tracer import TraceEvent
        t = RequestTracer()
        record = t.start_request("SPY", "15m")
        # Manually add fake events
        record.events = [
            TraceEvent("ta.trend", 1, "market_structure", 0, 5, True, "Trend=bullish", 0.85),
            TraceEvent("ta.ema", 2, "indicator", 5, 3, True, "EMA20=450.5", 0.99),
            TraceEvent("ta.wyckoff", 3, "institutional", 8, 4, True, "Wyckoff=accumulation", 0.80),
            TraceEvent("ta.consensus", 4, "consensus", 12, 2, True, "alignment=bullish", 0.90),
        ]
        t.finish_request(record, final_conclusion="alignment=bullish")
        report = build_evidence_report(record)
        # Layer 4 (consensus) and Layer 3 (institutional) → primary
        assert len(report.primary_contributors) >= 1
        # Layer 2 (ema) → supporting
        assert len(report.supporting_contributors) >= 1
        # Layer 1 (trend) → contextual
        assert len(report.contextual_contributors) >= 1

    def test_evidence_summary_text_includes_all_sections(self, repo):
        from athena_x_runtime_institutional_workspace.tracer import TraceEvent
        t = RequestTracer()
        record = t.start_request("SPY", "15m")
        record.events = [
            TraceEvent("ta.ema", 2, "indicator", 0, 3, True, "EMA20=450.5", 0.99),
        ]
        t.finish_request(record, final_conclusion="EMA=450.5")
        report = build_evidence_report(record)
        text = evidence_summary_text(report)
        assert "Evidence Report" in text
        assert "Primary contributors" in text
        assert "Supporting contributors" in text
        assert "Contextual contributors" in text


# ============================================================================
# Phase 7 — Component Inventory (for Dashboard)
# ============================================================================

class TestComponentInventory:
    def test_list_components_returns_full_inventory(self):
        ws = InstitutionalWorkspace()
        ws.discover()
        components = ws.list_components()
        assert len(components) >= 20
        # Each component has required fields
        for c in components:
            assert "agent_id" in c
            assert "name" in c
            assert "category" in c
            assert "layer" in c
            assert "description" in c
            assert "inputs" in c
            assert "outputs" in c
            assert "dependencies" in c
            assert "module_path" in c
            assert "manifest" in c
            assert "health" in c

    def test_get_component_returns_one(self):
        ws = InstitutionalWorkspace()
        ws.discover()
        ema = ws.get_component("ta.ema")
        assert ema is not None
        assert ema["agent_id"] == "ta.ema"
        assert ema["layer"] == 2

    def test_get_component_returns_none_for_unknown(self):
        ws = InstitutionalWorkspace()
        ws.discover()
        assert ws.get_component("ta.does_not_exist") is None


# ============================================================================
# Phase 8 — No Regression (existing tests must still pass)
# ============================================================================

class TestNoRegression:
    """These tests confirm that the institutional workspace layer does NOT
    break any existing runtime functionality. The underlying TA agents,
    Layer 1-5 wiring, and Stage 7 integration continue to work unchanged."""

    async def test_stage7_wire_still_works(self):
        """The Stage 7 container still wires up correctly."""
        from athena_x_runtime_stage7_integration.wire import create_stage7_container
        container = create_stage7_container()
        assert container["total_agent_count"] >= 23
        # Layer counts
        assert len(container["layer1"]) == 6
        assert len(container["layer2"]) == 8
        assert len(container["layer3"]) == 8
        assert len(container["layer4"]) == 1

    async def test_individual_ta_agents_still_compute(self, repo):
        """Original TA agents (not via adapter) still work."""
        from athena_x_ta_layer2_indicators import EMAAgent
        agent = EMAAgent(period=20)
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.value is not None
        assert result.confidence.score >= 0.9

    async def test_adapter_and_direct_produce_same_result(self, repo):
        """The adapter layer does NOT change agent output."""
        from athena_x_ta_layer2_indicators import EMAAgent
        # Direct call
        direct_agent = EMAAgent(period=20)
        direct_result = await direct_agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        # Via adapter
        ws = InstitutionalWorkspace()
        ws.discover()
        adapter_result = await ws.execute_agent("ta.ema", "SPY", Timeframe.FIFTEEN_MIN, repo)
        # Values should match (same algorithm, same input)
        assert direct_result.value == adapter_result["output"]["value"]
