"""Modularity audit - checks for circular deps, public interfaces, dependency direction.

Stage 5.1 req: No circular dependencies; public interfaces only.
"""
from __future__ import annotations
import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImportEdge:
    """An import edge in the dependency graph."""
    source: str  # package name
    target: str  # imported package name
    file: str


@dataclass
class AuditResult:
    """Result of modularity audit."""
    total_packages: int = 0
    total_imports: int = 0
    circular_imports: list[list[str]] = field(default_factory=list)
    packages_without_init: list[str] = field(default_factory=list)
    dependency_violations: list[str] = field(default_factory=list)
    public_interfaces: dict[str, list[str]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return (
            len(self.circular_imports) == 0
            and len(self.packages_without_init) == 0
            and len(self.dependency_violations) == 0
        )


# Dependency direction rules (lower layers cannot import higher layers)
# Layer 0: types, config, logger
# Layer 1: event-bus, session-awareness, institutional-metadata
# Layer 2: providers, raw-archival, data-freshness
# Layer 3: collectors, validators
# Layer 4: standardizers, repositories
# Layer 5: agents (intelligence, decision, supervisor)
# Layer 6: apps (dashboard, backend)

LAYER_MAP = {
    # Layer 0 - foundation
    "athena_x_runtime_config": 0,
    "athena_x_runtime_logger": 0,
    "athena_x_runtime_di": 0,
    "athena_x_runtime_secrets": 0,
    "athena_x_runtime_auth": 0,
    "athena_x_runtime_validation_types": 0,
    "athena_x_runtime_canonical_types": 0,
    # Layer 1 - infrastructure
    "athena_x_runtime_event_bus": 1,
    "athena_x_runtime_session_awareness": 1,
    "athena_x_runtime_institutional_metadata": 1,
    "athena_x_runtime_schema_registry": 1,
    "athena_x_runtime_symbol_dictionary": 1,
    "athena_x_runtime_market_calendars": 1,
    "athena_x_runtime_audit_trail": 1,
    "athena_x_runtime_raw_archival": 1,
    "athena_x_runtime_data_freshness": 1,
    "athena_x_runtime_health_monitor": 1,
    "athena_x_runtime_scheduler": 1,
    "athena_x_runtime_db_roles": 1,
    "athena_x_runtime_db_partitioning": 1,
    "athena_x_runtime_db_events": 1,
    "athena_x_runtime_db_monitoring": 1,
    "athena_x_runtime_db_backup": 1,
    "athena_x_runtime_repository_interface": 1,
    # Layer 2 - providers
    "athena_x_provider_base": 2,
    "athena_x_provider_simulated": 2,
    "athena_x_provider_yahoo": 2,
    "athena_x_provider_finnhub": 2,
    "athena_x_provider_cnn": 2,
    "athena_x_provider_failover": 2,
    # Layer 3 - collectors + validators
    "athena_x_collector_base": 3,
    "athena_x_collector_market_data": 3,
    "athena_x_collector_options_data": 3,
    "athena_x_collector_news_data": 3,
    "athena_x_collector_cross_market": 3,
    "athena_x_validator_base": 3,
    "athena_x_validator_schema": 3,
    "athena_x_validator_timestamp": 3,
    "athena_x_validator_market_calendar": 3,
    "athena_x_validator_cross_provider": 3,
    "athena_x_validator_market_logic": 3,
    "athena_x_validator_completeness": 3,
    "athena_x_validator_duplicate": 3,
    "athena_x_validator_outlier": 3,
    "athena_x_validator_confidence": 3,
    "athena_x_validator_market_state": 3,
    "athena_x_validator_quarantine": 3,
    # Layer 4 - standardizers + repositories
    "athena_x_standardizer_base": 4,
    "athena_x_standardizer_market": 4,
    "athena_x_standardizer_options": 4,
    "athena_x_standardizer_news": 4,
    "athena_x_standardizer_macro": 4,
    "athena_x_runtime_in_memory_repository": 4,
    # Layer 5 - agents
    # Layer 6 - apps
}


class ModularityAuditor:
    """Audits the codebase for modularity violations."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._edges: list[ImportEdge] = []
        self._packages: set[str] = set()

    def audit(self) -> AuditResult:
        """Run full modularity audit."""
        result = AuditResult()

        # 1. Find all Python packages (directories with __init__.py)
        self._find_packages()
        result.total_packages = len(self._packages)

        # 2. Find all imports
        self._find_imports()
        result.total_imports = len(self._edges)

        # 3. Check for circular imports
        result.circular_imports = self._find_circular_imports()

        # 4. Check for packages without __init__.py
        result.packages_without_init = self._find_packages_without_init()

        # 5. Check dependency direction
        result.dependency_violations = self._check_dependency_direction()

        # 6. Catalog public interfaces
        result.public_interfaces = self._catalog_public_interfaces()

        return result

    def _find_packages(self) -> None:
        """Find all Python packages (directories with __init__.py)."""
        for init_file in self.root.rglob("__init__.py"):
            if "site-packages" in str(init_file) or "node_modules" in str(init_file):
                continue
            if ".venv" in str(init_file):
                continue
            pkg_dir = init_file.parent
            # Determine package name from path
            rel = pkg_dir.relative_to(self.root)
            parts = rel.parts
            if len(parts) >= 2:
                pkg_name = parts[-1]
                self._packages.add(pkg_name)

    def _find_imports(self) -> None:
        """Find all athena_x imports."""
        athena_pattern = re.compile(r"from\s+(athena_x_\w+)\s+import|import\s+(athena_x_\w+)")

        for py_file in self.root.rglob("*.py"):
            if "site-packages" in str(py_file) or ".venv" in str(py_file):
                continue
            try:
                content = py_file.read_text()
            except Exception:
                continue

            # Determine source package
            rel = py_file.relative_to(self.root)
            parts = rel.parts
            if len(parts) < 2:
                continue
            source_pkg = self._find_package_name_for_file(py_file)
            if source_pkg is None:
                continue

            for match in athena_pattern.finditer(content):
                target = match.group(1) or match.group(2)
                if target and target != source_pkg:
                    self._edges.append(ImportEdge(
                        source=source_pkg,
                        target=target,
                        file=str(rel),
                    ))

    def _find_package_name_for_file(self, filepath: Path) -> str | None:
        """Find the package name for a Python file."""
        # Walk up to find __init__.py
        current = filepath.parent
        while current != self.root and current != current.parent:
            if (current / "__init__.py").exists():
                # Check if this is an athena_x package
                for subdir in [current] + list(current.parents):
                    init = subdir / "__init__.py"
                    if init.exists():
                        content = init.read_text()
                        if "athena_x" in content:
                            return subdir.name
            current = current.parent

        # Check if file itself is in src/<pkg>/
        parts = filepath.relative_to(self.root).parts
        if "src" in parts:
            idx = parts.index("src")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return None

    def _find_circular_imports(self) -> list[list[str]]:
        """Find circular import chains using DFS."""
        # Build adjacency list
        graph: dict[str, set[str]] = defaultdict(set)
        for edge in self._edges:
            graph[edge.source].add(edge.target)

        # Find cycles using DFS
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            path.pop()
            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def _find_packages_without_init(self) -> list[str]:
        """Find Python directories without __init__.py."""
        missing = []
        for py_file in self.root.rglob("*.py"):
            if "site-packages" in str(py_file) or ".venv" in str(py_file):
                continue
            if py_file.name == "__init__.py":
                continue
            pkg_dir = py_file.parent
            if not (pkg_dir / "__init__.py").exists():
                # Check if this is a tests/ or scripts/ dir (OK to not have __init__)
                if "tests" in str(py_file) or "scripts" in str(py_file):
                    continue
                missing.append(str(py_file.relative_to(self.root)))
        return missing[:20]  # limit

    def _check_dependency_direction(self) -> list[str]:
        """Check that dependencies flow in the correct direction."""
        violations = []
        for edge in self._edges:
            source_layer = LAYER_MAP.get(edge.source)
            target_layer = LAYER_MAP.get(edge.target)
            if source_layer is not None and target_layer is not None:
                if source_layer < target_layer:
                    violations.append(
                        f"{edge.source} (L{source_layer}) -> {edge.target} (L{target_layer}) in {edge.file}"
                    )
        return violations

    def _catalog_public_interfaces(self) -> dict[str, list[str]]:
        """Catalog public interfaces (exports from __init__.py)."""
        interfaces: dict[str, list[str]] = {}
        for init_file in self.root.rglob("__init__.py"):
            if "site-packages" in str(init_file) or ".venv" in str(init_file):
                continue
            try:
                content = init_file.read_text()
                # Find __all__ or from X import Y
                exports: list[str] = []
                if "__all__" in content:
                    # Parse __all__ list
                    match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
                    if match:
                        exports = re.findall(r'"([^"]+)"', match.group(1))
                if exports:
                    pkg = init_file.parent.name
                    interfaces[pkg] = exports
            except Exception:
                pass
        return interfaces
