"""Validation Framework types - Stage 14."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TestPhase(str, Enum):
    """10 validation phases."""
    STARTUP = "phase_1_startup"
    LIVE_DATA = "phase_2_live_data"
    AGENT = "phase_3_agent"
    PIPELINE = "phase_4_pipeline"
    EVENT_BUS = "phase_5_event_bus"
    FAILURE_INJECTION = "phase_6_failure_injection"
    REPLAY = "phase_7_replay"
    STRESS = "phase_8_stress"
    PAPER_TRADING = "phase_9_paper_trading"
    END_TO_END = "phase_10_end_to_end"


class TestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a single validation phase."""
    phase: TestPhase
    result: TestResult = TestResult.PASS
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    warnings: int = 0
    duration_seconds: float = 0.0
    details: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    """Final validation test report."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    overall_result: TestResult = TestResult.PASS
    total_phases: int = 10
    phases_passed: int = 0
    phases_failed: int = 0
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_warnings: int = 0
    data_loss: int = 0
    replay_consistency: bool = True
    duration_seconds: float = 0.0
    phase_results: list[PhaseResult] = field(default_factory=list)
    resource_usage: dict[str, Any] = field(default_factory=dict)
    system_health: str = "healthy"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_result": self.overall_result.value,
            "total_phases": self.total_phases,
            "phases_passed": self.phases_passed,
            "phases_failed": self.phases_failed,
            "total_tests": self.total_tests,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_warnings": self.total_warnings,
            "data_loss": self.data_loss,
            "replay_consistency": self.replay_consistency,
            "duration_seconds": round(self.duration_seconds, 2),
            "system_health": self.system_health,
            "phases": [
                {
                    "phase": p.phase.value,
                    "result": p.result.value,
                    "tests_run": p.tests_run,
                    "tests_passed": p.tests_passed,
                    "tests_failed": p.tests_failed,
                    "warnings": p.warnings,
                    "duration_seconds": round(p.duration_seconds, 2),
                    "details": p.details[:5],
                }
                for p in self.phase_results
            ],
        }


@dataclass
class ValidationConfig:
    """Configuration for the validation framework."""
    run_all_phases: bool = True
    phases_to_run: list[TestPhase] = field(default_factory=lambda: list(TestPhase))
    stress_multiplier: int = 10
    replay_scenarios: list[str] = field(default_factory=lambda: [
        "FOMC", "CPI", "NFP", "OPEX", "Triple Witching",
        "Banking Crisis", "COVID Crash", "AI Rally", "High-Vol Gap",
    ])
    paper_trading_duration_minutes: int = 60
    event_bus_test_count: int = 10000
    failure_scenarios: list[str] = field(default_factory=lambda: [
        "yahoo_unavailable", "polygon_unavailable", "redis_disconnected",
        "database_unavailable", "corrupted_json", "duplicate_ticks",
        "delayed_timestamps", "invalid_options_chain", "missing_news_feed",
    ])
