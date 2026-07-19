"""Phase 8 — Per-Plugin Evidence Report.

For every plugin, generates an evidence report with:
  - Mathematical correctness (cross-validation against pandas-ta)
  - Logic correctness (trading-logic scenario pass rate)
  - Runtime correctness (does it execute without error?)
  - Performance (latency)
  - Dependencies (declared in manifest)
  - Failure cases (which scenarios failed)
  - Improvement suggestions
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PluginEvidence:
    """Evidence report for one plugin/agent."""
    agent_id: str
    name: str
    layer: int | str
    category: str

    # Scores (0-100)
    math_score: float = 0.0          # cross-validation pass rate
    logic_score: float = 0.0         # trading-logic scenario pass rate
    runtime_score: float = 0.0       # execution success rate
    performance_score: float = 0.0   # latency-based

    # Details
    math_evidence: list[dict] = field(default_factory=list)    # cross-validation results
    logic_evidence: list[dict] = field(default_factory=list)   # scenario results
    runtime_evidence: list[dict] = field(default_factory=list) # execution results
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    error_count: int = 0

    # Certification
    certification: str = ""         # CERTIFIED / PROVISIONAL / NEEDS IMPROVEMENT
    failure_cases: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def build_evidence_report(
    agent_id: str,
    name: str,
    layer: int | str,
    category: str,
    crossval_results: list[dict],
    scenario_results: list[dict],
    execution_results: list[dict],
    dependencies: list[str] | None = None,
) -> PluginEvidence:
    """Build a PluginEvidence report from collected results."""
    ev = PluginEvidence(
        agent_id=agent_id, name=name, layer=layer, category=category,
        dependencies=list(dependencies or []),
    )

    # Math score: cross-validation pass rate
    ev.math_evidence = crossval_results
    if crossval_results:
        n_pass = sum(1 for r in crossval_results if r.get("passed"))
        ev.math_score = n_pass / len(crossval_results) * 100

    # Logic score: scenario pass rate
    ev.logic_evidence = scenario_results
    if scenario_results:
        n_pass = sum(1 for r in scenario_results if r.get("passed"))
        ev.logic_score = n_pass / len(scenario_results) * 100
        # Collect failure cases
        for r in scenario_results:
            if not r.get("passed"):
                ev.failure_cases.append(f"{r.get('scenario_id')}: {r.get('message', '')}")

    # Runtime score: execution success rate
    ev.runtime_evidence = execution_results
    if execution_results:
        n_pass = sum(1 for r in execution_results if r.get("success"))
        ev.runtime_score = n_pass / len(execution_results) * 100
        ev.error_count = sum(1 for r in execution_results if not r.get("success"))
        # Avg latency
        latencies = [r.get("latency_ms", 0) for r in execution_results if r.get("latency_ms")]
        if latencies:
            ev.avg_latency_ms = sum(latencies) / len(latencies)
        # Avg confidence
        confs = [r.get("confidence") for r in execution_results if r.get("confidence") is not None]
        if confs:
            ev.avg_confidence = sum(confs) / len(confs)

    # Performance score
    if ev.avg_latency_ms < 5:
        ev.performance_score = 100.0
    elif ev.avg_latency_ms < 50:
        ev.performance_score = 80.0
    elif ev.avg_latency_ms < 200:
        ev.performance_score = 50.0
    else:
        ev.performance_score = 20.0

    # Certification logic
    # CERTIFIED: math ≥ 80, logic ≥ 70, runtime = 100, performance ≥ 80
    # PROVISIONAL: runtime = 100 (works, but not all thresholds met)
    # NEEDS IMPROVEMENT: runtime < 100
    if ev.runtime_score >= 100 and ev.math_score >= 80 and ev.logic_score >= 70 and ev.performance_score >= 80:
        ev.certification = "CERTIFIED"
    elif ev.runtime_score >= 100:
        ev.certification = "PROVISIONAL"
    else:
        ev.certification = "NEEDS IMPROVEMENT"

    # Improvement suggestions
    if ev.math_score < 80:
        ev.improvement_suggestions.append(
            f"Math correctness {ev.math_score:.0f}% below 80% threshold — verify formula against pandas-ta reference"
        )
    if ev.logic_score < 70:
        ev.improvement_suggestions.append(
            f"Logic correctness {ev.logic_score:.0f}% below 70% threshold — review failed scenarios"
        )
    if ev.runtime_score < 100:
        ev.improvement_suggestions.append(
            f"Runtime {ev.runtime_score:.0f}% — {ev.error_count} execution errors detected"
        )
    if ev.avg_confidence < 0.5 and ev.avg_confidence > 0:
        ev.improvement_suggestions.append(
            f"Average confidence {ev.avg_confidence:.2f} below 0.5 — agent may need more data or better warmup handling"
        )
    if not ev.math_evidence:
        ev.improvement_suggestions.append(
            "No cross-validation reference available — consider adding pandas-ta reference implementation"
        )

    return ev
