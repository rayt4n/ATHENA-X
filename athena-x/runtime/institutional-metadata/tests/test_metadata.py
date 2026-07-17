"""Tests for institutional metadata (Stage 2 req 1.5)."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_institutional_metadata import (
    InstitutionalMetadata,
    DataStatus,
    AssetClass,
    TradingSession,
    ProviderDefaults,
    create_metadata,
)


def test_metadata_has_10_mandatory_fields():
    """All 10 institutional metadata fields are present and required."""
    m = create_metadata(
        provider="yahoo",
        symbol="NVDA",
        asset_class=AssetClass.EQUITY,
    )
    # 10 mandatory fields
    assert m.provider == "yahoo"
    assert m.provider_latency >= 0
    assert m.download_timestamp.tzinfo is not None
    assert m.market_timestamp.tzinfo is not None
    assert m.timezone == "UTC"
    assert m.symbol == "NVDA"
    assert m.asset_class == "equity"
    assert 0.0 <= m.confidence_score <= 1.0
    assert m.status == "fresh"
    assert m.session == "regular"


def test_provider_defaults():
    """Each provider has a default confidence score."""
    assert ProviderDefaults.get_confidence("databento") == 0.98
    assert ProviderDefaults.get_confidence("yahoo") == 0.85
    assert ProviderDefaults.get_confidence("simulated") == 0.50
    # Unknown providers get a conservative default
    assert ProviderDefaults.get_confidence("unknown") == 0.80


def test_metadata_uses_provider_default_confidence():
    """If confidence not specified, uses provider default."""
    m = create_metadata(provider="databento", symbol="ES", asset_class="future")
    assert m.confidence_score == 0.98


def test_metadata_accepts_explicit_confidence():
    m = create_metadata(
        provider="yahoo",
        symbol="NVDA",
        asset_class="equity",
        confidence_score=0.99,
    )
    assert m.confidence_score == 0.99


def test_metadata_rejects_naive_timestamps():
    """Timestamps must be UTC-aware."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        InstitutionalMetadata(
            provider="yahoo",
            providerLatency=10,
            downloadTimestamp=datetime.now(),  # naive!
            marketTimestamp=datetime.now(timezone.utc),
            timezone="UTC",
            symbol="NVDA",
            assetClass=AssetClass.EQUITY,
            confidenceScore=0.85,
            status=DataStatus.FRESH,
            session=TradingSession.REGULAR,
        )


def test_metadata_rejects_invalid_confidence():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        InstitutionalMetadata(
            provider="yahoo",
            providerLatency=10,
            downloadTimestamp=datetime.now(timezone.utc),
            marketTimestamp=datetime.now(timezone.utc),
            timezone="UTC",
            symbol="NVDA",
            assetClass=AssetClass.EQUITY,
            confidenceScore=1.5,  # invalid
            status=DataStatus.FRESH,
            session=TradingSession.REGULAR,
        )


def test_metadata_serializes_with_camel_case():
    """Metadata serializes to JSON with camelCase aliases."""
    m = create_metadata(provider="yahoo", symbol="NVDA", asset_class="equity")
    json_str = m.model_dump_json(by_alias=True)
    assert '"providerLatency"' in json_str
    assert '"downloadTimestamp"' in json_str
    assert '"marketTimestamp"' in json_str
    assert '"assetClass"' in json_str
    assert '"confidenceScore"' in json_str


def test_metadata_supports_all_asset_classes():
    """All 10 asset classes are supported."""
    for ac in AssetClass:
        m = create_metadata(provider="yahoo", symbol="X", asset_class=ac)
        assert m.asset_class == ac.value


def test_metadata_supports_all_sessions():
    """All 6 trading sessions are supported."""
    for s in TradingSession:
        m = create_metadata(
            provider="yahoo", symbol="X", asset_class="equity", session=s
        )
        assert m.session == s.value


def test_metadata_supports_all_statuses():
    """All 4 data statuses are supported."""
    for s in DataStatus:
        m = create_metadata(
            provider="yahoo", symbol="X", asset_class="equity", status=s
        )
        assert m.status == s.value
