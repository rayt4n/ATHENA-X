"""Tests for stage-gate checker."""
import pytest
from pathlib import Path
from athena_x_tools_stage_gate_checklist.checker import (
    StageGateChecker, CheckResult, StageGateReport,
)


@pytest.fixture
def checker():
    return StageGateChecker(project_root="/home/z/my-project/athena-x")


def test_check_result_dataclass():
    r = CheckResult(name="Functional", passed=True, details="ok")
    assert r.passed is True
    assert r.name == "Functional"


def test_stage_gate_report_all_passed():
    report = StageGateReport(stage=5)
    report.results = [
        CheckResult(name="Functional", passed=True),
        CheckResult(name="Tested", passed=True),
    ]
    assert report.all_passed is True
    assert report.pass_count == 2
    assert report.fail_count == 0


def test_stage_gate_report_has_failures():
    report = StageGateReport(stage=5)
    report.results = [
        CheckResult(name="Functional", passed=True),
        CheckResult(name="Tested", passed=False),
    ]
    assert report.all_passed is False
    assert report.pass_count == 1
    assert report.fail_count == 1


def test_check_stage_returns_6_results(checker):
    """check_stage returns 6 CheckResults (one per criterion)."""
    report = checker.check_stage(5)
    assert len(report.results) == 6
    names = [r.name for r in report.results]
    assert "Functional" in names
    assert "Tested" in names
    assert "Modular" in names
    assert "Documented" in names
    assert "Verifiable" in names
    assert "Production-ready" in names


def test_summary_string(checker):
    report = checker.check_stage(5)
    summary = report.summary()
    assert "Stage 5" in summary
    assert "PASS" in summary or "FAIL" in summary
