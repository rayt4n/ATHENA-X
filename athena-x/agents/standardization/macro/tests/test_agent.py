"""Tests for Macro Standardization Agent."""
import pytest
from datetime import datetime, timezone
from athena_x_standardizer_macro import MacroStandardizationAgent
from athena_x_standardizer_base import StandardizationContext
from athena_x_runtime_canonical_types import MacroRecord


@pytest.fixture
def agent():
    return MacroStandardizationAgent()


@pytest.fixture
def context():
    return StandardizationContext(
        provider="fred", provider_version="1.0.0",
        raw_payload_id="raw-macro-1", validation_id="val-macro-1",
        validation_status="verified", confidence_score=0.97, quality_grade="A+",
    )


def test_standardize_returns_macro_record(agent, context):
    record = {
        "indicator": "CPI YoY",
        "region": "us",
        "value": 3.2,
        "previous": 3.4,
        "surprise": -0.2,
        "unit": "%",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = agent.standardize(record, context)
    assert isinstance(result, MacroRecord)
    assert result.indicator == "CPI YoY"
    assert result.region == "US"  # normalized
    assert result.value == 3.2
    assert result.source_provider == "fred"


def test_region_normalization(agent, context):
    for raw, expected in [("us", "US"), ("eu", "EU"), ("cn", "CN"), ("jp", "JP"), ("uk", "UK")]:
        record = {
            "indicator": "GDP", "region": raw, "value": 2.1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = agent.standardize(record, context)
        assert result.region == expected


def test_macro_provenance(agent, context):
    record = {
        "indicator": "Unemployment", "region": "US", "value": 3.9,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = agent.standardize(record, context)
    assert result.raw_payload_id == "raw-macro-1"
    assert result.validation_id == "val-macro-1"
    assert result.schema_version == "1.0.0"
