"""ATHENA-X Stage 16.5 — Plugin Validation Workspace.

Reuses the existing Institutional Workspace (Stage 16.3) and adds:
  - Trading-logic validation scenarios (formula, params, edge cases)
  - Cross-validation against pandas-ta reference implementations
  - Per-plugin evidence reports with Math/Logic/Runtime/Performance scores
  - Final certification table

Does NOT modify the Institutional Workspace. Does NOT rewrite any agent.
"""
from .discovery import ValidationDiscovery, ValidationInventory
from .logic.scenarios import LogicScenarioRunner, LOGIC_SCENARIOS
from .crossval.reference import CrossValidator, ReferenceResult
from .evidence import PluginEvidence, build_evidence_report
from .workspace import PluginValidationWorkspace

__all__ = [
    "PluginValidationWorkspace",
    "ValidationDiscovery",
    "ValidationInventory",
    "LogicScenarioRunner",
    "LOGIC_SCENARIOS",
    "CrossValidator",
    "ReferenceResult",
    "PluginEvidence",
    "build_evidence_report",
]
__version__ = "0.1.0"
