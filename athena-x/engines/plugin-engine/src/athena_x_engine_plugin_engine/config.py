"""Configuration Service - enables/disables plugins without modifying code.

yaml config:
  enabled:
    ema: true
    sma: true
    macd: true
    rsi: true
    bollinger: false
    elliott: false
    wyckoff: true
"""
from __future__ import annotations
from pathlib import Path
from threading import RLock
from typing import Any
import yaml
from athena_x_runtime_logger import get_logger

from .registry import PluginRegistry

log = get_logger("plugin.config")


class PluginConfigService:
    """Manages plugin enable/disable configuration.

    Usage:
        config = PluginConfigService(registry)
        config.load_from_file("plugins/config.yaml")
        config.set_enabled("ema", True)
        config.set_enabled("bollinger", False)
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._lock = RLock()
        self._config: dict[str, bool] = {}  # plugin_id -> enabled

    def load_from_file(self, path: str | Path) -> None:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            log.warning("config_file_not_found", path=str(path))
            return

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        enabled_map = data.get("enabled", {})
        with self._lock:
            self._config = {k: bool(v) for k, v in enabled_map.items()}

        # Apply to registry
        for plugin_id, enabled in self._config.items():
            self._registry.set_enabled(plugin_id, enabled)

        log.info("config_loaded",
                 path=str(path),
                 plugins=len(self._config),
                 enabled=sum(1 for v in self._config.values() if v))

    def load_from_dict(self, config: dict[str, bool]) -> None:
        """Load configuration from a dict."""
        with self._lock:
            self._config = {k: bool(v) for k, v in config.items()}
        for plugin_id, enabled in self._config.items():
            self._registry.set_enabled(plugin_id, enabled)

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable/disable a plugin at runtime (no restart needed)."""
        with self._lock:
            self._config[plugin_id] = enabled
        self._registry.set_enabled(plugin_id, enabled)
        log.info("plugin_enabled_changed",
                 plugin_id=plugin_id,
                 enabled=enabled)

    def is_enabled(self, plugin_id: str) -> bool:
        """Check if a plugin is enabled."""
        with self._lock:
            return self._config.get(plugin_id, True)  # default: enabled

    def get_config(self) -> dict[str, bool]:
        """Get the full configuration."""
        with self._lock:
            return dict(self._config)

    def save_to_file(self, path: str | Path) -> None:
        """Save current configuration to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump({"enabled": self.get_config()}, f, default_flow_style=False)
        log.info("config_saved", path=str(path))
