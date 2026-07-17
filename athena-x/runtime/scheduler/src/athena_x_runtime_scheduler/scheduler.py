"""APScheduler wrapper for cron + on-demand tasks.

Used for:
- Periodic data collection (e.g., every 5 seconds during market hours)
- Nightly backtests
- Intraday report generation
- Heartbeat emission
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.scheduler")


@dataclass
class ScheduledTask:
    """Description of a scheduled task."""
    id: str
    name: str
    trigger: str  # 'cron' | 'interval' | 'date'
    trigger_args: dict
    func: Callable[..., Awaitable[Any]]
    next_run: datetime | None = None
    last_run: datetime | None = None


class Scheduler:
    """Async scheduler wrapping APScheduler.

    Usage:
        sched = Scheduler()
        await sched.start()

        # Cron: every weekday at 09:30 ET
        await sched.add_cron("market_open", "0 30 9 * * MON-FRI", market_open_handler)

        # Interval: every 5 seconds
        await sched.add_interval("heartbeat", seconds=5, func=heartbeat_handler)

        # One-shot: at specific time
        await sched.add_once("report", run_date=datetime(...), func=report_handler)

        await sched.shutdown()
    """

    def __init__(self):
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="UTC",
        )
        self._tasks: dict[str, ScheduledTask] = {}

    async def start(self) -> None:
        self._scheduler.start()
        log.info("scheduler_started")

    async def shutdown(self, wait: bool = True) -> None:
        self._scheduler.shutdown(wait=wait)
        log.info("scheduler_stopped")

    async def add_cron(self, task_id: str, cron_expr: str,
                       func: Callable[..., Awaitable[Any]]) -> str:
        """Add a cron-scheduled task.

        Args:
            task_id: unique task identifier
            cron_expr: standard cron expression (e.g., "0 30 9 * * MON-FRI")
            func: async callable to execute
        """
        trigger = CronTrigger.from_crontab(cron_expr)
        self._scheduler.add_job(
            self._wrap(func, task_id),
            trigger=trigger,
            id=task_id,
            replace_existing=True,
        )
        self._tasks[task_id] = ScheduledTask(
            id=task_id,
            name=task_id,
            trigger="cron",
            trigger_args={"cron": cron_expr},
            func=func,
        )
        log.info("cron_task_added", task_id=task_id, cron=cron_expr)
        return task_id

    async def add_interval(self, task_id: str, *,
                           seconds: int = 0, minutes: int = 0, hours: int = 0,
                           func: Callable[..., Awaitable[Any]]) -> str:
        """Add an interval-scheduled task."""
        trigger = IntervalTrigger(seconds=seconds, minutes=minutes, hours=hours)
        self._scheduler.add_job(
            self._wrap(func, task_id),
            trigger=trigger,
            id=task_id,
            replace_existing=True,
        )
        self._tasks[task_id] = ScheduledTask(
            id=task_id,
            name=task_id,
            trigger="interval",
            trigger_args={"seconds": seconds, "minutes": minutes, "hours": hours},
            func=func,
        )
        log.info("interval_task_added", task_id=task_id,
                 seconds=seconds, minutes=minutes, hours=hours)
        return task_id

    async def add_once(self, task_id: str, run_date: datetime,
                       func: Callable[..., Awaitable[Any]]) -> str:
        """Add a one-shot task at a specific datetime."""
        trigger = DateTrigger(run_date=run_date)
        self._scheduler.add_job(
            self._wrap(func, task_id),
            trigger=trigger,
            id=task_id,
            replace_existing=True,
        )
        self._tasks[task_id] = ScheduledTask(
            id=task_id,
            name=task_id,
            trigger="date",
            trigger_args={"run_date": run_date.isoformat()},
            func=func,
            next_run=run_date,
        )
        log.info("oneshot_task_added", task_id=task_id, run_date=run_date.isoformat())
        return task_id

    async def remove(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id not in self._tasks:
            return False
        try:
            self._scheduler.remove_job(task_id)
        except Exception:
            pass
        del self._tasks[task_id]
        log.info("task_removed", task_id=task_id)
        return True

    def list_tasks(self) -> list[ScheduledTask]:
        """List all scheduled tasks."""
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> ScheduledTask | None:
        return self._tasks.get(task_id)

    def _wrap(self, func: Callable[..., Awaitable[Any]], task_id: str):
        """Wrap a coroutine function with logging + error handling."""
        async def wrapped():
            from athena_x_runtime_logger import log_context
            with log_context(agent_id=f"scheduler.{task_id}"):
                task = self._tasks.get(task_id)
                if task:
                    task.last_run = datetime.utcnow()
                try:
                    await func()
                except Exception as e:
                    log.error("scheduled_task_failed", task_id=task_id, error=str(e))
                    raise
                # Update next_run
                if task:
                    job = self._scheduler.get_job(task_id)
                    if job and job.next_run_time:
                        task.next_run = job.next_run_time
        return wrapped
