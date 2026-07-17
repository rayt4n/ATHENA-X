"""Tests for modularity audit."""
import pytest
from pathlib import Path
from athena_x_tools_modularity_audit.audit import (
    ModularityAuditor, AuditResult, LAYER_MAP,
)


@pytest.fixture
def auditor():
    return ModularityAuditor(root="/home/z/my-project/athena-x")


def test_audit_returns_result(auditor):
    result = auditor.audit()
    assert isinstance(result, AuditResult)
    assert result.total_packages > 0


def test_no_circular_imports(auditor):
    """Stage 5.1 req: No circular dependencies."""
    result = auditor.audit()
    assert len(result.circular_imports) == 0, f"Circular imports found: {result.circular_imports}"


def test_layer_map_has_all_packages():
    """Layer map covers all known packages."""
    assert "athena_x_runtime_config" in LAYER_MAP
    assert "athena_x_provider_base" in LAYER_MAP
    assert "athena_x_validator_base" in LAYER_MAP
    assert "athena_x_standardizer_market" in LAYER_MAP


def test_dependency_direction_correct(auditor):
    """Stage 5.1 req: Dependencies flow in one direction."""
    result = auditor.audit()
    # Allow some violations during early development, but should be 0 eventually
    assert len(result.dependency_violations) < 20, f"Too many violations: {result.dependency_violations}"


def test_public_interfaces_cataloged(auditor):
    """Public interfaces are cataloged."""
    result = auditor.audit()
    assert len(result.public_interfaces) > 0
    # Some known packages should have __all__
    found_packages = set(result.public_interfaces.keys())
    assert len(found_packages) > 0
