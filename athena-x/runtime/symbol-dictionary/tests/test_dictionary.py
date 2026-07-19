"""Tests for symbol dictionary (Stage 4 req 3)."""
import pytest
from athena_x_runtime_symbol_dictionary import SymbolDictionary


@pytest.fixture
def dictionary():
    return SymbolDictionary()


def test_spy_aliases_resolve(dictionary):
    """SPY.US, NYSEARCA:SPY all resolve to SPY."""
    assert dictionary.resolve("SPY") == "SPY"
    assert dictionary.resolve("SPY.US", provider="yahoo") == "SPY"
    assert dictionary.resolve("NYSEARCA:SPY", provider="polygon") == "SPY"


def test_es_futures_aliases(dictionary):
    """ES futures aliases resolve to ES."""
    assert dictionary.resolve("ES=F", provider="yahoo") == "ES"
    assert dictionary.resolve("ES1!", provider="polygon") == "ES"
    assert dictionary.resolve("ESU26", provider="tradestation") == "ES"
    assert dictionary.resolve("ES") == "ES"


def test_brk_b_dash_resolves_to_dot(dictionary):
    """BRK-B resolves to BRK.B (canonical form)."""
    assert dictionary.resolve("BRK-B", provider="yahoo") == "BRK.B"
    assert dictionary.resolve("BRK.B", provider="polygon") == "BRK.B"


def test_vix_with_caret(dictionary):
    """^VIX (Yahoo) resolves to VIX."""
    assert dictionary.resolve("^VIX", provider="yahoo") == "VIX"
    assert dictionary.resolve("VIX") == "VIX"


def test_btc_usd_resolves(dictionary):
    """BTC-USD resolves correctly across providers."""
    assert dictionary.resolve("BTC-USD") == "BTC-USD"
    assert dictionary.resolve("X:BTCUSD", provider="polygon") == "BTC-USD"


def test_unknown_symbol_returns_original(dictionary):
    """Unknown symbols are returned as-is (will be flagged by validator)."""
    assert dictionary.resolve("UNKNOWN") == "UNKNOWN"


def test_case_insensitive(dictionary):
    """Symbol lookup is case-insensitive."""
    assert dictionary.resolve("spy") == "SPY"
    assert dictionary.resolve("Spy") == "SPY"


def test_register_new_symbol(dictionary):
    """New symbols can be registered."""
    dictionary.register("NEW", aliases={"yahoo": ["NEW.US"]}, asset_class="equity")
    assert dictionary.resolve("NEW.US", provider="yahoo") == "NEW"


def test_get_mapping_returns_metadata(dictionary):
    """get_mapping returns full mapping with metadata."""
    m = dictionary.get_mapping("SPY")
    assert m is not None
    assert m.canonical == "SPY"
    assert m.asset_class == "etf"
    assert m.exchange == "NYSEARCA"


def test_list_all_returns_all_mappings(dictionary):
    """list_all returns all registered mappings."""
    mappings = dictionary.list_all()
    canonicals = [m.canonical for m in mappings]
    assert "SPY" in canonicals
    assert "ES" in canonicals
    assert "VIX" in canonicals
    assert "BRK.B" in canonicals


def test_count(dictionary):
    """count returns the number of registered symbols."""
    assert dictionary.count() >= 20  # we registered at least 20 defaults
