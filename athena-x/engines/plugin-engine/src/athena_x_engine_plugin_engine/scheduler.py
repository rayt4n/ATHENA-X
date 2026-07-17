"""Execution Scheduler - runs indicators at configurable frequencies.

Each plugin controls its refresh rate via manifest.refresh_interval_seconds.

Example:
  EMA: every 1 second
  VWAP: every 5 seconds
  Wyckoff: every 15 seconds
  Elliott Wave: every 60 seconds
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Awaitable, Callable
from athena_x_runtime_logger import get_logger

from .registry import PluginRegistry

log = get_logger("plugin.scheduler")


@dataclass
class ScheduleEntry:
    """A scheduled plugin execution."""
    plugin_id: str
    interval_seconds: float
    last_run: float = 0.0  # monotonic timestamp
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True


class PluginScheduler:
    """Schedules plugin execution at configurable frequencies.

    Usage:
        scheduler = PluginScheduler(registry)
        await scheduler.start()
        # Plugins run at their configured intervals
        await scheduler.stop()
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._schedules: dict[str, ScheduleEntry] = {}
        self._lock = RLock()
        self._running = False
        self._task: asyncio.Task | None = None
        self._executor: Callable[..., Awaitable[Any]] | None = None
        self._build_schedules()

    def _build_schedules(self) -> None:
        """Build schedule entries from registered plugins."""
        for entry in self._registry.list_enabled():
            self._schedules[entry.manifest.id] = ScheduleEntry(
                plugin_id=entry.manifest.id,
                interval_seconds=entry.manifest.refresh_interval_seconds,
                enabled=entry.manifest.enabled,
            )

    def set_executor(self, executor: Callable[..., Awaitable[Any]]) -> None:
        """Set the function that executes a plugin."""
        self._executor = executor

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("scheduler_started",
                 plugins=len(self._schedules))

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        log.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = time.monotonic()
            with self._lock:
                due = [
                    s for s in self._schedules.values()
                    if s.enabled and (now - s.last_run) >= s.interval_seconds
                ]

            for schedule in due:
                if self._executor is None:
                    continue
                try:
                    await self._executor(schedule.plugin_id)
                    with self._lock:
                        schedule.last_run = now
                        schedule.run_count += 1
                except Exception as e:
                    with self._lock:
                        schedule.error_count += 1
                    log.error("plugin_execution_failed",
                              plugin_id=schedule.plugin_id,
                              error=str(e))

            await asyncio.sleep(0.1)  # check every 100ms

    def run_now(self, plugin_id: str) -> None:
        """Force a plugin to run immediately (regardless of schedule)."""
        with self._lock:
            schedule = self._schedules.get(plugin_id)
            if schedule:
                schedule.last_run = 0.0  # will be due next loop iteration

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable/disable a plugin's schedule at runtime."""
        with self._lock:
            schedule = self._schedules.get(plugin_id)
            if schedule:
                schedule.enabled = enabled

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_scheduled": len(self._schedules),
                "enabled": sum(1 for s in self._schedules.values() if s.enabled),
                "total_runs": sum(s.run_count for s in self._schedules.values()),
                "total_errors": sum(s.error_count for s in self._schedules.values()),
                "schedules": [
                    {
                        "plugin_id": s.plugin_id,
                        "interval": s.interval_seconds,
                        "run_count": s.run_count,
                        "error_count": s.error_count,
                        "enabled": s.enabled,
                    }
                    for s in self._schedules.values()
                ],
            }

    def rebuild(self) -> None:
        """Rebuild schedules from registry (after plugins added/removed)."""
        with self._lock:
            self._schedules.clear()
            self._build_schedules()
        log.info("scheduler_rebuilt", plugins=len(self._schedules))
