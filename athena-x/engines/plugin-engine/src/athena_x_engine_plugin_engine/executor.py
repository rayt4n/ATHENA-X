"""Plugin Executor - executes a plugin and publishes the result as an event.

Stage 7 rule: Every output is published as an ai:technical:* event.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority

from .manager import PluginManager

log = get_logger("plugin.executor")


@dataclass
class ExecutionResult:
    """Result of executing a plugin."""
    plugin_id: str
    symbol: str
    timeframe: str
    value: Any
    confidence: float = 1.0
    calculation_time_ms: float = 0.0
    success: bool = True
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PluginExecutor:
    """Executes plugins and publishes results as events.

    Usage:
        executor = PluginExecutor(manager, event_bus)
        result = await executor.execute("ema", symbol="SPY", timeframe="15m", data=closes)
    """

    def __init__(self, manager: PluginManager, event_bus: Any = None):
        self._manager = manager
        self._bus = event_bus
        self._execution_count = 0
        self._error_count = 0

    async def execute(
        self,
        plugin_id: str,
        symbol: str,
        timeframe: str,
        data: Any = None,
    ) -> ExecutionResult:
        """Execute a plugin and publish the result."""
        start = time.monotonic()

        try:
            instance = self._manager.get_instance(plugin_id)
            if instance is None:
                instance = self._manager.load(plugin_id)

            # Call compute or calculate method
            if hasattr(instance, "compute"):
                output = instance.compute(data) if data else instance.compute()
            elif hasattr(instance, "calculate"):
                output = instance.calculate(data) if data else instance.calculate()
            else:
                raise AttributeError(f"Plugin {plugin_id} has no compute/calculate method")

            elapsed_ms = (time.monotonic() - start) * 1000
            self._execution_count += 1

            result = ExecutionResult(
                plugin_id=plugin_id,
                symbol=symbol,
                timeframe=timeframe,
                value=output,
                calculation_time_ms=elapsed_ms,
            )

            # Publish event
            if self._bus is not None:
                event = create_event(
                    event_type=f"ai:technical:{plugin_id}",
                    source_agent=f"ta.{plugin_id}",
                    symbol=symbol,
                    priority=EventPriority.NORMAL,
                    payload={
                        "agent": f"{plugin_id}Agent",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "indicator": plugin_id.upper(),
                        "value": output if not isinstance(output, dict) else output,
                        "confidence": result.confidence,
                        "calculation_time_ms": int(elapsed_ms),
                    },
                    processing_time_ms=int(elapsed_ms),
                )
                await self._bus.publish(event)

            return result

        except Exception as e:
            self._error_count += 1
            elapsed_ms = (time.monotonic() - start) * 1000
            log.error("plugin_execution_failed",
                      plugin_id=plugin_id,
                      error=str(e))
            return ExecutionResult(
                plugin_id=plugin_id,
                symbol=symbol,
                timeframe=timeframe,
                value=None,
                calculation_time_ms=elapsed_ms,
                success=False,
                error=str(e),
            )

    def get_stats(self) -> dict:
        return {
            "total_executions": self._execution_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._execution_count if self._execution_count > 0 else 0.0,
        }
