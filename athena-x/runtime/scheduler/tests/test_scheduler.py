"""Tests for Scheduler."""
import pytest
import asyncio
from datetime import datetime, timedelta
from athena_x_runtime_scheduler import Scheduler


@pytest.fixture
async def scheduler():
    s = Scheduler()
    await s.start()
    yield s
    await s.shutdown(wait=False)


async def test_interval_task_executes(scheduler):
    """Interval task runs at the specified interval."""
    call_count = 0

    async def task():
        nonlocal call_count
        call_count += 1

    await scheduler.add_interval("test", seconds=1, func=task)
    await asyncio.sleep(2.5)
    assert call_count >= 2


async def test_oneshot_task_executes_once(scheduler):
    """One-shot task runs exactly once at the specified time."""
    call_count = 0

    async def task():
        nonlocal call_count
        call_count += 1

    run_at = datetime.utcnow() + timedelta(seconds=1)
    await scheduler.add_once("oneshot", run_date=run_at, func=task)
    await asyncio.sleep(2)
    assert call_count == 1


async def test_remove_task(scheduler):
    """Removed tasks no longer execute."""
    call_count = 0

    async def task():
        nonlocal call_count
        call_count += 1

    await scheduler.add_interval("test", seconds=1, func=task)
    await asyncio.sleep(1.5)
    assert call_count >= 1

    await scheduler.remove("test")
    count_after_removal = call_count
    await asyncio.sleep(2)
    assert call_count == count_after_removal


async def test_list_tasks(scheduler):
    async def task(): pass
    await scheduler.add_interval("t1", seconds=10, func=task)
    await scheduler.add_interval("t2", seconds=20, func=task)

    tasks = scheduler.list_tasks()
    assert len(tasks) == 2
    task_ids = {t.id for t in tasks}
    assert task_ids == {"t1", "t2"}


async def test_task_failure_does_not_crash_scheduler(scheduler):
    """A failing task does not crash the scheduler — it logs and continues."""
    call_count = 0

    async def failing_task():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("intentional failure")

    async def healthy_task():
        nonlocal call_count
        call_count += 1

    await scheduler.add_interval("failing", seconds=1, func=failing_task)
    await scheduler.add_interval("healthy", seconds=1, func=healthy_task)

    await asyncio.sleep(2.5)
    # Both should have run multiple times despite failing_task raising
    assert call_count >= 4
