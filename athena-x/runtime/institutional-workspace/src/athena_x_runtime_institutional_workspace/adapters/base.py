"""Agent Adapter — wraps a runtime agent as a PluginManifest-compatible entry.

The adapter does NOT duplicate agent logic. It holds a reference to the
agent instance and exposes:
  - manifest() → dict matching PluginManifest shape (for registry compatibility)
  - execute(symbol, timeframe, repo) → TAOutput (delegates to agent.compute)
  - health() → dict (delegates to agent.get_health if present)

This lets the PluginRegistry see runtime agents as if they were plugins,
without rewriting any agent code.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AdapterManifest:
    """PluginManifest-compatible manifest for an adapted runtime agent."""
    id: str                       # "ta.ema"
    name: str                     # "EMA"
    version: str                  # "0.1.0"
    category: str                 # "indicator"
    layer: str                    # "2"
    timeframes: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    refresh_interval_seconds: int = 1
    enabled: bool = True
    description: str = ""
    author: str = "ATHENA-X Stage 16.3"
    config: dict = field(default_factory=dict)
    runtime_path: str = ""        # the actual agent module path

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "layer": self.layer,
            "timeframes": list(self.timeframes),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "dependencies": list(self.dependencies),
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "enabled": self.enabled,
            "description": self.description,
            "author": self.author,
            "runtime_path": self.runtime_path,
        }


class AgentAdapter:
    """Wraps a runtime agent instance as a PluginManifest-compatible plugin.

    The adapter holds a (lazily-created) reference to the agent instance.
    All compute calls delegate to the agent's compute() method — no logic
    is duplicated.
    """

    def __init__(
        self,
        agent_id: str,
        agent_class: type,
        module_path: str,
        layer: int | str,
        category: str,
        description: str = "",
        inputs: tuple[str, ...] = (),
        outputs: tuple[str, ...] = (),
        dependencies: tuple[str, ...] = (),
        agent_factory=None,  # optional callable that returns an agent instance
    ):
        self.agent_id = agent_id
        self.agent_class = agent_class
        self.module_path = module_path
        self.layer = layer
        self.category = category
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.dependencies = dependencies
        self._agent_factory = agent_factory
        self._instance: Any = None

        # Build a human-readable name from the agent_id
        # "ta.ema" → "EMA", "ta.support_resistance" → "Support Resistance"
        parts = agent_id.split(".", 1)[-1].split("_")
        self.name = " ".join(p.upper() if len(p) <= 3 else p.title() for p in parts)

        # Build the manifest
        self.manifest = AdapterManifest(
            id=agent_id,
            name=self.name,
            version="0.1.0",
            category=category,
            layer=str(layer),
            timeframes=("1M","1W","1D","4H","1H","30M","15M","5M","1m"),
            inputs=inputs,
            outputs=outputs,
            dependencies=dependencies,
            description=description,
            runtime_path=module_path,
        )

    def get_instance(self):
        """Lazily instantiate the agent. BarCache defaults to a fresh instance."""
        if self._instance is None:
            if self._agent_factory is not None:
                self._instance = self._agent_factory()
            else:
                # Default: try no-arg constructor first; if that fails, try with bar_cache=None
                try:
                    self._instance = self.agent_class()
                except TypeError:
                    try:
                        self._instance = self.agent_class(bar_cache=None)
                    except Exception as e:
                        raise RuntimeError(f"Cannot instantiate {self.agent_class.__name__}: {e}")
        return self._instance

    async def execute(self, symbol: str, timeframe, repo, event_bus=None) -> Any:
        """Execute the agent. Delegates to agent.compute() or compute_and_publish()."""
        instance = self.get_instance()
        if event_bus is not None and hasattr(instance, "compute_and_publish"):
            return await instance.compute_and_publish(symbol, timeframe, repo, event_bus)
        if hasattr(instance, "compute"):
            return await instance.compute(symbol, timeframe, repo)
        raise AttributeError(f"Agent {self.agent_id} has no compute method")

    def health(self) -> dict:
        """Return agent health if the agent supports it."""
        instance = self._instance
        if instance is not None and hasattr(instance, "get_health"):
            return instance.get_health()
        return {"agent_id": self.agent_id, "running": False}


def adapt_agent(discovered) -> AgentAdapter:
    """Build an AgentAdapter from a DiscoveredAgent record.

    Imports the agent's class lazily so that discovery remains metadata-only
    until execution is requested.
    """
    import importlib
    module = importlib.import_module(discovered.module_path)
    cls = getattr(module, discovered.class_name)
    return AgentAdapter(
        agent_id=discovered.agent_id,
        agent_class=cls,
        module_path=discovered.module_path,
        layer=discovered.layer,
        category=discovered.category,
        description=discovered.description,
        inputs=discovered.inputs,
        outputs=discovered.outputs,
        dependencies=discovered.dependencies,
    )
