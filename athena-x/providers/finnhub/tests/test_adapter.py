"""Tests for Finnhub provider."""
import pytest
import httpx
from athena_x_provider_finnhub import FinnhubAdapter


def mock_finnhub_quote() -> dict:
    return {
        "c": 128.45,
        "d": 1.45,
        "dp": 1.14,
        "h": 130.0,
        "l": 127.5,
        "o": 129.0,
        "pc": 127.0,
        "t": 1700000000,
    }


@pytest.fixture
async def provider():
    def handler(request):
        return httpx.Response(200, json=mock_finnhub_quote())

    p = FinnhubAdapter(api_key="test-key")
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    yield p
    await p.close()


async def test_fetch_quote(provider):
    result = await provider.fetch_quote("NVDA")
    assert result.provider == "finnhub"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] == 128.45
    assert result.data["change"] == 1.45
    assert result.data["change_percent"] == 1.14


async def test_api_key_required():
    """Provider raises if no API key is set."""
    p = FinnhubAdapter(api_key=None)
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await p.fetch_quote("NVDA")


async def test_http_error_raises(provider):
    """HTTP errors raise ProviderError."""
    def handler(request):
        return httpx.Response(500, text="Internal Server Error")
    provider = FinnhubAdapter(api_key="test")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await provider.fetch_quote("NVDA")
    await provider.close()
