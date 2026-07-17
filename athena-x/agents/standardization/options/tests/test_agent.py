"""Tests for Options Standardization Agent."""
import pytest
from datetime import datetime, timezone
from athena_x_standardizer_options import OptionsStandardizationAgent
from athena_x_standardizer_base import StandardizationContext
from athena_x_runtime_canonical_types import OptionsRecord


@pytest.fixture
def agent():
    return OptionsStandardizationAgent()


@pytest.fixture
def context():
    return StandardizationContext(
        provider="polygon", provider_version="1.0.0",
        raw_payload_id="raw-opt-1", validation_id="val-opt-1",
        validation_status="verified", confidence_score=0.92, quality_grade="A",
    )


def test_standardize_chain(agent, context):
    """Standardize an options chain into individual OptionsRecords."""
    chain = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strikes": [
            {"strike": 125.0, "call": {"bid": 5.0, "ask": 5.5, "iv": 0.45, "delta": 0.65, "volume": 1000, "open_interest": 5000}},
            {"strike": 125.0, "put": {"bid": 2.0, "ask": 2.2, "iv": 0.42, "delta": -0.35, "volume": 800, "open_interest": 3000}},
        ],
    }
    records = agent.standardize_chain(chain, context)
    assert len(records) == 2
    assert all(isinstance(r, OptionsRecord) for r in records)
    assert records[0].underlying == "NVDA"
    assert records[0].strike == 125.0
    assert records[0].option_type == "call"
    assert records[1].option_type == "put"


def test_options_no_calculations(agent, context):
    """Stage 4 rule: No calculations. IV/delta/etc are passed through, not computed."""
    chain = {
        "symbol": "SPY",
        "expiry": "2026-07-18",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strikes": [
            {"strike": 450.0, "call": {"iv": 0.15, "delta": 0.5, "gamma": 0.02}},
        ],
    }
    records = agent.standardize_chain(chain, context)
    assert len(records) == 1
    # Values are passed through as-is, not computed
    assert records[0].implied_volatility == 0.15
    assert records[0].delta == 0.5
    assert records[0].gamma == 0.02


def test_options_provenance(agent, context):
    """Options records have provenance fields."""
    chain = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strikes": [
            {"strike": 125.0, "call": {"bid": 5.0}},
        ],
    }
    records = agent.standardize_chain(chain, context)
    assert len(records) == 1
    assert records[0].source_provider == "polygon"
    assert records[0].raw_payload_id == "raw-opt-1"
    assert records[0].schema_version == "1.0.0"
