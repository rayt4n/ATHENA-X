"""Options Plugin Executor - executes options plugins + publishes events.

Stage 8 rule: Every output is published as an options:* event.
"""
from __future__ import annotations
import time
from typing import Any
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_engine_plugin_engine import PluginExecutor as BaseExecutor

log = get_logger("options-plugin-executor")


class OptionsPluginExecutor:
    """Executes options plugins and publishes options:* events.

    Usage:
        executor = OptionsPluginExecutor(manager, event_bus)
        result = await executor.execute("gamma_flip", input_data=...)
    """

    def __init__(self, manager, event_bus: Any = None):
        self._manager = manager
        self._bus = event_bus
        self._execution_count = 0
        self._error_count = 0

    async def execute(self, plugin_id: str, input_data: Any = None) -> dict:
        """Execute a plugin and publish the result."""
        start = time.monotonic()

        try:
            instance = self._manager.get_instance(plugin_id)
            if instance is None:
                instance = self._manager.load(plugin_id)

            if hasattr(instance, "compute"):
                output = instance.compute(input_data) if input_data else instance.compute()
            else:
                raise AttributeError(f"Plugin {plugin_id} has no compute method")

            elapsed_ms = (time.monotonic() - start) * 1000
            self._execution_count += 1

            result = {
                "plugin_id": plugin_id,
                "value": output.value if hasattr(output, "value") else output,
                "confidence": output.confidence if hasattr(output, "confidence") else 1.0,
                "calculation_time_ms": elapsed_ms,
                "success": True,
            }

            # Publish event
            if self._bus is not None:
                symbol = input_data.symbol if input_data and hasattr(input_data, "symbol") else "UNKNOWN"
                event = create_event(
                    event_type=f"options:{plugin_id}_updated",
                    source_agent=f"options.{plugin_id}",
                    symbol=symbol,
                    priority=EventPriority.HIGH,
                    payload=result,
                    processing_time_ms=int(elapsed_ms),
                )
                await self._bus.publish(event)

            return result

        except Exception as e:
            self._error_count += 1
            elapsed_ms = (time.monotonic() - start) * 1000
            log.error("options_plugin_failed", plugin_id=plugin_id, error=str(e))
            return {
                "plugin_id": plugin_id,
                "value": None,
                "success": False,
                "error": str(e),
                "calculation_time_ms": elapsed_ms,
            }

    def get_stats(self) -> dict:
        return {
            "total_executions": self._execution_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._execution_count if self._execution_count > 0 else 0.0,
        }
