"""Tests for Validation Framework."""
import pytest
from athena_x_engine_validation_framework import (
    TestPhase, TestResult, TestReport,
    PhaseResult, ValidationConfig,
    TestOrchestrator,
)


async def test_orchestrator_runs_all_10_phases():
    """Test orchestrator runs all 10 phases."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    assert len(report.phase_results) == 10
    assert report.total_phases == 10


async def test_orchestrator_all_phases_pass():
    """All phases should pass with the default mock implementation."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    assert report.phases_passed == 10
    assert report.phases_failed == 0
    assert report.overall_result == TestResult.PASS


async def test_report_has_metrics():
    """Report includes performance metrics."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    # Phase 8 (stress) has metrics
    stress_phase = next(p for p in report.phase_results if p.phase == TestPhase.STRESS)
    assert "stress_multiplier" in stress_phase.metrics
    assert "max_cpu" in stress_phase.metrics


async def test_report_includes_data_loss():
    """Report tracks data loss (should be 0)."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    assert report.data_loss == 0


async def test_report_includes_replay_consistency():
    """Report tracks replay consistency."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    assert report.replay_consistency is True


async def test_report_serializable():
    """Report can be serialized to dict."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    d = report.to_dict()
    assert "overall_result" in d
    assert "total_tests" in d
    assert "phases" in d
    assert len(d["phases"]) == 10


async def test_config_customizable():
    """Config allows customizing which phases to run."""
    config = ValidationConfig(
        run_all_phases=False,
        phases_to_run=[TestPhase.STARTUP, TestPhase.AGENT],
    )
    orch = TestOrchestrator(config=config)
    report = await orch.run_all()
    assert len(report.phase_results) == 2


def test_10_phases_defined():
    """10 validation phases are defined."""
    assert TestPhase.STARTUP.value == "phase_1_startup"
    assert TestPhase.LIVE_DATA.value == "phase_2_live_data"
    assert TestPhase.AGENT.value == "phase_3_agent"
    assert TestPhase.PIPELINE.value == "phase_4_pipeline"
    assert TestPhase.EVENT_BUS.value == "phase_5_event_bus"
    assert TestPhase.FAILURE_INJECTION.value == "phase_6_failure_injection"
    assert TestPhase.REPLAY.value == "phase_7_replay"
    assert TestPhase.STRESS.value == "phase_8_stress"
    assert TestPhase.PAPER_TRADING.value == "phase_9_paper_trading"
    assert TestPhase.END_TO_END.value == "phase_10_end_to_end"


async def test_startup_phase_checks_8_items():
    """Phase 1 checks 8 startup items."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    startup = next(p for p in report.phase_results if p.phase == TestPhase.STARTUP)
    assert startup.tests_run == 8
    assert startup.tests_passed == 8


async def test_agent_phase_checks_all_agents():
    """Phase 3 checks all agents."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    agent_phase = next(p for p in report.phase_results if p.phase == TestPhase.AGENT)
    assert agent_phase.metrics.get("agent_count") == 78


async def test_end_to_end_checks_14_steps():
    """Phase 10 checks 14 end-to-end steps."""
    orch = TestOrchestrator()
    report = await orch.run_all()
    e2e = next(p for p in report.phase_results if p.phase == TestPhase.END_TO_END)
    assert e2e.tests_run == 14
    assert e2e.metrics.get("dna_objects_produced") == 7
