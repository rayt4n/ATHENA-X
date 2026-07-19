"""System Validation Framework - 10-phase test orchestrator."""
from .types import (
    TestPhase, TestResult, TestReport,
    PhaseResult, ValidationConfig,
)
from .orchestrator import TestOrchestrator

__all__ = [
    "TestPhase", "TestResult", "TestReport",
    "PhaseResult", "ValidationConfig",
    "TestOrchestrator",
]
__version__ = "0.1.0"
