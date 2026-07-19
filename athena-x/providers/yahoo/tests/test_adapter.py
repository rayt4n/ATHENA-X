"""Tests for Yahoo provider.

These tests use httpx's MockTransport to avoid hitting real Yahoo Finance.
"""
import pytest
import httpx
from datetime import datetime, timezone
from athena_x_provider_yahoo import YahooAdapter


def mock_yahoo_response(symbol: str = "NVDA") -> dict:
    """Build a mock Yahoo chart API response."""
    return {
        "chart": {
            "result": [{
                "meta": {
                    "symbol": symbol,
                    "regularMarketPrice": 128.45,
                    "bid": 128.44,
                    "ask": 128.46,
                    "regularMarketDayHigh": 130.0,
                    "regularMarketDayLow": 127.5,
                    "regularMarketOpen": 129.0,
                    "chartPreviousClose": 127.0,
                    "regularMarketVolume": 5000000,
                    "regularMarketChange": 1.45,
                    "regularMarketChangePercent": 1.14,
                    "currency": "USD",
                    "exchangeName": "NMS",
                },
                "timestamp": [1700000000, 1700000060, 1700000120],
                "indicators": {
                    "quote": [{
                        "open": [129.0, 129.5, 128.5],
                        "high": [130.0, 130.5, 129.0],
                        "low": [128.5, 129.0, 128.0],
                        "close": [129.5, 129.0, 128.45],
                        "volume": [100000, 150000, 200000],
                    }]
                }
            }],
            "error": None
        }
    }


@pytest.fixture
async def mock_provider():
    """Yahoo adapter with mocked HTTP transport."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_yahoo_response("NVDA"))

    transport = httpx.MockTransport(handler)
    p = YahooAdapter()
    # Inject mock client
    p._client = httpx.AsyncClient(
        transport=transport,
        headers={"User-Agent": "test"},
    )
    yield p
    await p.close()


async def test_fetch_quote_parses_yahoo_response(mock_provider):
    result = await mock_provider.fetch_quote("NVDA")
    assert result.provider == "yahoo"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] == 128.45
    assert result.data["bid"] == 128.44
    assert result.data["ask"] == 128.46
    assert result.data["volume"] == 5000000
    assert result.latency_ms >= 0


async def test_fetch_quote_archives_raw_payload(tmp_path):
    """Yahoo adapter archives raw payload via RawArchiver."""
    from athena_x_runtime_raw_archival import RawArchiver
    archiver = RawArchiver(base_path=tmp_path)

    def handler(request):
        return httpx.Response(200, json=mock_yahoo_response())

    p = YahooAdapter(archiver=archiver)
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await p.fetch_quote("NVDA")
    await p.close()

    # Verify file was archived
    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1


async def test_fetch_quote_handles_error():
    """HTTP errors raise ProviderError."""
    def handler(request):
        return httpx.Response(404, text="Not Found")

    p = YahooAdapter()
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await p.fetch_quote("INVALID")
    await p.close()


async def test_fetch_bars(mock_provider):
    results = await mock_provider._fetch_bars("NVDA", "1m", 3)
    assert len(results) == 3
    bar, ts = results[0]
    assert bar["symbol"] == "NVDA"
    assert bar["close"] == 129.5
    assert bar["open"] == 129.0


async def test_health_check(mock_provider):
    await mock_provider.fetch_quote("NVDA")
    health = await mock_provider.health_check()
    assert health["provider"] == "yahoo"
    assert health["successful_calls"] == 1
    assert health["total_calls"] == 1
