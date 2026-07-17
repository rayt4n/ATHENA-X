"""Plugin manifest - each indicator declares itself via manifest.yaml.

The engine reads this automatically. No code changes needed to add an indicator.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import yaml


class PluginCategory(str, Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    STRUCTURE = "structure"
    PATTERN = "pattern"
    LIQUIDITY = "liquidity"
    PROJECTION = "projection"


class PluginLayer(str, Enum):
    MARKET_STRUCTURE = "1"
    INDICATOR = "2"
    INSTITUTIONAL = "3"
    CONSENSUS = "4"

    @classmethod
    def _missing_(cls, value):
        """Handle int → str conversion for layer values."""
        if isinstance(value, int):
            return cls(str(value))
        return None


@dataclass(frozen=True)
class PluginManifest:
    """Manifest declared by each plugin via manifest.yaml."""
    id: str                    # e.g., "ema"
    name: str                  # e.g., "EMA"
    version: str               # semver "1.0.0"
    category: PluginCategory
    layer: PluginLayer
    timeframes: list[str]      # ["1M", "1W", "1D", "4H", "1H", "30M", "15M", "5M", "1m"]
    inputs: list[str]          # ["OHLCV"]
    outputs: list[str]         # ["ema20", "ema50", "ema200"]
    dependencies: list[str]    # [] or ["ema"] for MACD
    refresh_interval_seconds: int = 1
    enabled: bool = True
    description: str = ""
    author: str = ""
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "PluginManifest":
        """Load manifest from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        """Create manifest from a dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            category=PluginCategory(data.get("category", "trend")),
            layer=PluginLayer(data.get("layer", "2")),
            timeframes=data.get("timeframes", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            dependencies=data.get("dependencies", []),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 1),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            author=data.get("author", ""),
            config=data.get("config", {}),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "layer": self.layer.value,
            "timeframes": self.timeframes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "enabled": self.enabled,
            "description": self.description,
        }
