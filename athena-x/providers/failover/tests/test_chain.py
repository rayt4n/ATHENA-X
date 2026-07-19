"""Tests for provider failover chain (Stage 2 req 1)."""
import pytest
from athena_x_provider_base.provider import ProviderError, ProviderResult
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_runtime_event_bus import InMemoryBusClient, BusEvent
from datetime import datetime, timezone


class FailingProvider:
    """Provider that always fails — for testing failover."""
    name = "failing"
    transport = "test"
    asset_classes = ["equity"]

    async def fetch_quote(self, symbol):
        raise ProviderError("failing", f"intentional failure for {symbol}")

    async def health_check(self):
        return {"provider": "failing", "connection": "disconnected"}


@pytest.fixture
async def bus():
    b = InMemoryBusClient()
    yield b
    await b.close()


async def test_failover_to_next_provider_on_failure(bus):
    """If the first provider fails, the chain tries the next."""
    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    result = await chain.fetch_quote("NVDA")

    assert result.provider_used == "simulated"
    assert result.failed_over is True
    assert len(result.attempts) == 2
    assert result.attempts[0][0] == "failing"
    assert result.attempts[0][1] is not None  # error message
    assert result.attempts[1][0] == "simulated"
    assert result.attempts[1][1] is None  # success


async def test_no_failover_when_first_succeeds(bus):
    """If the first provider succeeds, no failover occurs."""
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[simulated], bus=bus)

    result = await chain.fetch_quote("NVDA")
    assert result.provider_used == "simulated"
    assert result.failed_over is False


async def test_failover_publishes_event(bus):
    """Failover publishes market:provider-failed-over event."""
    received_events = []

    async def handler(event):
        received_events.append(event)

    await bus.subscribe("market:provider-failed-over", handler)

    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    await chain.fetch_quote("NVDA")

    assert len(received_events) == 1
    event = received_events[0]
    assert event.event_type == "market:provider-failed-over"
    assert event.payload["from"] == "failing"
    assert event.payload["to"] == "simulated"


async def test_all_providers_fail_raises(bus):
    """If all providers fail, the chain raises."""
    failing1 = FailingProvider()
    failing1.name = "failing1"
    failing2 = FailingProvider()
    failing2.name = "failing2"

    chain = FailoverChain(providers=[failing1, failing2], bus=bus)

    with pytest.raises(ProviderError):
        await chain.fetch_quote("NVDA")


async def test_failover_stats_tracked(bus):
    """Chain tracks failover counts per provider."""
    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    await chain.fetch_quote("NVDA")
    await chain.fetch_quote("SPY")

    stats = chain.get_failover_stats()
    assert stats["failing"] == 2  # failed twice
    assert stats["simulated"] == 0  # never failed
