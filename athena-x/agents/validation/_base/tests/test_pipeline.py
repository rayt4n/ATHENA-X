"""Tests for validation pipeline."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason, VALIDATOR_VERSION,
)
from athena_x_runtime_audit_trail import AuditTrail
from athena_x_validator_base import (
    BaseValidator, ValidatorConfig, ValidationPipeline,
)


class AlwaysPassValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-pass", blocking=False))
    async def validate(self, record, context):
        return self._passed("all good")


class AlwaysRejectValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-reject", blocking=True))
    async def validate(self, record, context):
        return self._reject(ValidationReason.UNKNOWN, "rejected")


class AlwaysWarnValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-warn", blocking=False))
    async def validate(self, record, context):
        return self._warning(ValidationReason.UNKNOWN, "warning", -0.2)


@pytest.fixture
def context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo",
        symbol="SPY",
        asset_class="etf",
    )


async def test_pipeline_passes_clean_record(context):
    """A record passing all validators is Verified."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    result = await pipeline.validate({"symbol": "SPY", "last": 450.0}, context)
    assert result.final_status == ValidationStatus.VERIFIED
    assert result.accepted is True
    assert result.confidence_score == 1.0
    assert result.quality_grade.value == "A+"


async def test_pipeline_rejects_on_blocking_validator(context):
    """A blocking validator rejection halts the pipeline."""
    pipeline = ValidationPipeline(
        validators=[AlwaysRejectValidator(), AlwaysPassValidator()]
    )
    result = await pipeline.validate({}, context)
    assert result.final_status == ValidationStatus.REJECTED
    assert result.quarantined is True
    # Only the first validator ran (blocking)
    assert len(result.results) == 1


async def test_pipeline_continues_on_warning(context):
    """Warnings don't halt the pipeline."""
    pipeline = ValidationPipeline(
        validators=[AlwaysWarnValidator(), AlwaysPassValidator()]
    )
    result = await pipeline.validate({}, context)
    assert result.final_status == ValidationStatus.WARNING
    assert result.accepted is True  # warnings still go to canonical DB
    assert len(result.results) == 2
    assert result.confidence_score == 0.8  # 1.0 - 0.2


async def test_pipeline_logs_to_audit_trail(context):
    """Every validation decision is logged."""
    audit = AuditTrail()
    pipeline = ValidationPipeline(
        validators=[AlwaysPassValidator()],
        audit_trail=audit,
    )
    await pipeline.validate({}, context)
    assert audit.count() == 1


async def test_pipeline_metadata_includes_6_fields(context):
    """to_metadata() returns the 6 confidence metadata fields."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    result = await pipeline.validate({}, context)
    metadata = result.to_metadata()
    assert "validation_status" in metadata
    assert "validation_time" in metadata
    assert "validator_version" in metadata
    assert "confidence_score" in metadata
    assert "quality_grade" in metadata
    assert "validation_reason" in metadata


async def test_pipeline_stats_tracked(context):
    """Pipeline tracks acceptance/rejection stats."""
    pipeline = ValidationPipeline(
        validators=[AlwaysRejectValidator()]
    )
    await pipeline.validate({}, context)
    await pipeline.validate({}, context)
    stats = pipeline.get_stats()
    assert stats["total_records"] == 2
    assert stats["rejected"] == 2
    assert stats["rejection_rate"] == 1.0


async def test_pipeline_deterministic(context):
    """Same input + version → same output (replay determinism)."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    r1 = await pipeline.validate({"x": 1}, context)
    r2 = await pipeline.validate({"x": 1}, context)
    # Same final status + confidence
    assert r1.final_status == r2.final_status
    assert r1.confidence_score == r2.confidence_score
    assert r1.validator_version == r2.validator_version
