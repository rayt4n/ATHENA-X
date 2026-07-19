"""Phase 1 — Discover Everything.

Auto-discovers:
  - Plugin slots in plugins/ directory (manifest metadata only)
  - Runtime TA agents (via Stage 16.3 RuntimeDiscovery)
  - Runtime intelligence hubs
  - Data providers (yahoo, finnhub, cnn, simulated, failover, + 11 stubs)
  - Engines (8 functional + 6 stubs)
  - Validators (11 in agents/validation/)
  - Adapters (Stage 16.3 AgentAdapter registry)
  - Dashboard widgets (12 modules in apps/nextjs-dashboard/src/modules/)

Reuses the Institutional Workspace's RuntimeDiscovery — does NOT duplicate.
"""
from __future__ import annotations
import importlib
import inspect
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from athena_x_runtime_logger import get_logger
# Reuse Stage 16.3 discovery
from athena_x_runtime_institutional_workspace.discovery import (
    RuntimeDiscovery, DiscoveredAgent, TA_LAYER_PACKAGES, HUB_PACKAGES
)

log = get_logger("plugin-validation.discovery")

ROOT = Path("/home/z/my-project/athena-x")


@dataclass
class PluginSlot:
    """A plugin slot in plugins/ directory (manifest metadata only)."""
    name: str
    category: str          # indicators / patterns / options / cross-market / news / forecast
    file_location: str
    has_manifest_yaml: bool = False
    has_manifest_py: bool = False
    has_src: bool = False
    has_tests: bool = False
    is_stub: bool = True
    src_lines: int = 0
    manifest_id: str = ""
    manifest_version: str = ""
    manifest_category: str = ""
    manifest_layer: str = ""
    manifest_inputs: list[str] = field(default_factory=list)
    manifest_outputs: list[str] = field(default_factory=list)
    manifest_dependencies: list[str] = field(default_factory=list)


@dataclass
class ProviderSlot:
    name: str
    file_location: str
    has_adapter: bool = False
    adapter_class: str = ""
    src_lines: int = 0
    is_stub: bool = True
    has_tests: bool = False


@dataclass
class EngineSlot:
    name: str
    file_location: str
    src_lines: int = 0
    is_stub: bool = True
    has_tests: bool = False
    test_lines: int = 0
    public_api: list[str] = field(default_factory=list)


@dataclass
class ValidatorSlot:
    name: str
    file_location: str
    src_lines: int = 0
    is_stub: bool = True
    has_tests: bool = False


@dataclass
class DashboardWidget:
    name: str
    file_location: str
    has_manifest: bool = False
    has_panel_component: bool = False


@dataclass
class ValidationInventory:
    """Complete inventory of every component in the repository."""
    plugin_slots: list[PluginSlot] = field(default_factory=list)
    runtime_agents: list[DiscoveredAgent] = field(default_factory=list)
    providers: list[ProviderSlot] = field(default_factory=list)
    engines: list[EngineSlot] = field(default_factory=list)
    validators: list[ValidatorSlot] = field(default_factory=list)
    dashboard_widgets: list[DashboardWidget] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plugin_slots": [asdict(p) for p in self.plugin_slots],
            "runtime_agents": [asdict(a) for a in self.runtime_agents],
            "providers": [asdict(p) for p in self.providers],
            "engines": [asdict(e) for e in self.engines],
            "validators": [asdict(v) for v in self.validators],
            "dashboard_widgets": [asdict(w) for w in self.dashboard_widgets],
            "summary": {
                "total_plugin_slots": len(self.plugin_slots),
                "total_runtime_agents": len(self.runtime_agents),
                "total_providers": len(self.providers),
                "total_engines": len(self.engines),
                "total_validators": len(self.validators),
                "total_dashboard_widgets": len(self.dashboard_widgets),
            },
        }


STUB_MARKERS = (
    "NotImplementedError",
    "STEP 4 implementation",
    "Implementation comes in STEP 4",
    "implementation comes in step 4",
    "TODO: implement",
)


def _is_stub(src_dir: Path) -> tuple[bool, int]:
    """Check if a src/ directory contains only stubs. Returns (is_stub, total_lines)."""
    if not src_dir.exists():
        return True, 0
    total_lines = 0
    has_stub_marker = False
    has_real_code = False
    for f in src_dir.rglob("*.py"):
        if f.name == "__init__.py":
            continue
        try:
            txt = f.read_text(errors="ignore")
        except Exception:
            continue
        lines = txt.count("\n") + 1
        total_lines += lines
        for marker in STUB_MARKERS:
            if marker in txt:
                has_stub_marker = True
                break
        # Heuristic: file with >25 lines and methods that aren't all NotImplementedError
        if lines > 25 and "def " in txt:
            # Check if there are real method bodies (not just raise NotImplementedError)
            method_lines = [l for l in txt.splitlines() if l.strip().startswith("def ") or l.strip().startswith("async def ")]
            for ml in method_lines[1:]:
                # Find the next non-empty line
                idx = txt.splitlines().index(ml)
                for next_line in txt.splitlines()[idx+1:idx+5]:
                    if next_line.strip() and not next_line.strip().startswith(("raise", "pass", "#", '"""', "return")):
                        has_real_code = True
                        break
    if has_real_code:
        return False, total_lines
    if has_stub_marker:
        return True, total_lines
    if total_lines < 25:
        return True, total_lines
    return False, total_lines


def _discover_plugin_slots() -> list[PluginSlot]:
    """Walk plugins/{indicators,patterns,options,cross-market,news,forecast}."""
    slots: list[PluginSlot] = []
    plugin_root = ROOT / "plugins"
    if not plugin_root.exists():
        return slots

    import yaml
    for category_dir in sorted(plugin_root.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for plugin_dir in sorted(category_dir.iterdir()):
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue
            slot = PluginSlot(
                name=plugin_dir.name,
                category=category,
                file_location=str(plugin_dir.relative_to(ROOT)),
            )
            slot.has_manifest_yaml = (plugin_dir / "manifest.yaml").exists()
            slot.has_manifest_py = any(plugin_dir.rglob("manifest.py"))
            slot.has_src = (plugin_dir / "src").exists()
            slot.has_tests = (plugin_dir / "tests").exists()

            src_dir = plugin_dir / "src"
            slot.is_stub, slot.src_lines = _is_stub(src_dir)

            # Parse manifest.yaml
            manifest_path = plugin_dir / "manifest.yaml"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        m = yaml.safe_load(f) or {}
                    slot.manifest_id = m.get("id", "")
                    slot.manifest_version = m.get("version", "")
                    slot.manifest_category = m.get("category", "")
                    slot.manifest_layer = str(m.get("layer", ""))
                    slot.manifest_inputs = list(m.get("inputs", []) or [])
                    slot.manifest_outputs = list(m.get("outputs", []) or [])
                    slot.manifest_dependencies = list(m.get("dependencies", []) or [])
                except Exception:
                    pass

            slots.append(slot)
    return slots


def _discover_providers() -> list[ProviderSlot]:
    """Walk providers/ directory."""
    slots: list[ProviderSlot] = []
    providers_dir = ROOT / "providers"
    if not providers_dir.exists():
        return slots
    for d in sorted(providers_dir.iterdir()):
        if not d.is_dir() or d.name == "base":
            continue
        slot = ProviderSlot(
            name=d.name,
            file_location=str(d.relative_to(ROOT)),
        )
        src_dir = d / "src"
        slot.has_adapter = any(src_dir.rglob("adapter.py")) if src_dir.exists() else False
        # Find adapter class name
        if slot.has_adapter:
            for adapter_file in src_dir.rglob("adapter.py"):
                try:
                    import ast
                    tree = ast.parse(adapter_file.read_text(errors="ignore"))
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and "Adapter" in node.name:
                            slot.adapter_class = node.name
                            break
                except Exception:
                    pass
                break
        slot.is_stub, slot.src_lines = _is_stub(src_dir)
        slot.has_tests = (d / "tests").exists() and any((d / "tests").glob("test_*.py"))
        slots.append(slot)
    return slots


def _discover_engines() -> list[EngineSlot]:
    """Walk engines/ directory."""
    slots: list[EngineSlot] = []
    engines_dir = ROOT / "engines"
    if not engines_dir.exists():
        return slots
    for d in sorted(engines_dir.iterdir()):
        if not d.is_dir():
            continue
        slot = EngineSlot(
            name=d.name,
            file_location=str(d.relative_to(ROOT)),
        )
        src_dir = d / "src"
        slot.is_stub, slot.src_lines = _is_stub(src_dir)
        tests_dir = d / "tests"
        if tests_dir.exists():
            slot.has_tests = True
            for tf in tests_dir.rglob("test_*.py"):
                try:
                    slot.test_lines += tf.read_text(errors="ignore").count("\n") + 1
                except Exception:
                    pass
        # Extract public API
        if src_dir.exists():
            for f in src_dir.rglob("*.py"):
                if f.name in ("__init__.py", "engine.py"):
                    continue
                try:
                    import ast
                    tree = ast.parse(f.read_text(errors="ignore"))
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                            slot.public_api.append(node.name)
                except Exception:
                    pass
        slots.append(slot)
    return slots


def _discover_validators() -> list[ValidatorSlot]:
    """Walk agents/validation/ directory."""
    slots: list[ValidatorSlot] = []
    val_dir = ROOT / "agents" / "validation"
    if not val_dir.exists():
        return slots
    for d in sorted(val_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        slot = ValidatorSlot(
            name=d.name,
            file_location=str(d.relative_to(ROOT)),
        )
        src_dir = d / "src"
        slot.is_stub, slot.src_lines = _is_stub(src_dir)
        slot.has_tests = (d / "tests").exists() and any((d / "tests").glob("test_*.py"))
        slots.append(slot)
    return slots


def _discover_dashboard_widgets() -> list[DashboardWidget]:
    """Walk apps/nextjs-dashboard/src/modules/."""
    widgets: list[DashboardWidget] = []
    modules_dir = ROOT / "apps" / "nextjs-dashboard" / "src" / "modules"
    if not modules_dir.exists():
        return widgets
    for d in sorted(modules_dir.iterdir()):
        if not d.is_dir():
            continue
        widget = DashboardWidget(
            name=d.name,
            file_location=str(d.relative_to(ROOT)),
            has_manifest=(d / "manifest.ts").exists(),
            has_panel_component=(d / "index.ts").exists(),
        )
        widgets.append(widget)
    return widgets


class ValidationDiscovery:
    """Discovers every component in the repository.

    Reuses RuntimeDiscovery from Stage 16.3 for runtime agents; adds discovery
    for plugin slots, providers, engines, validators, and dashboard widgets.
    """

    def discover_all(self) -> ValidationInventory:
        """Discover every component."""
        inv = ValidationInventory()

        # Reuse Stage 16.3 discovery for runtime agents
        log.info("discovering_runtime_agents")
        runtime_d = RuntimeDiscovery()
        inv.runtime_agents = runtime_d.discover_all()

        log.info("discovering_plugin_slots")
        inv.plugin_slots = _discover_plugin_slots()

        log.info("discovering_providers")
        inv.providers = _discover_providers()

        log.info("discovering_engines")
        inv.engines = _discover_engines()

        log.info("discovering_validators")
        inv.validators = _discover_validators()

        log.info("discovering_dashboard_widgets")
        inv.dashboard_widgets = _discover_dashboard_widgets()

        log.info(
            "discovery_complete",
            plugin_slots=len(inv.plugin_slots),
            runtime_agents=len(inv.runtime_agents),
            providers=len(inv.providers),
            engines=len(inv.engines),
            validators=len(inv.validators),
            dashboard_widgets=len(inv.dashboard_widgets),
        )
        return inv
