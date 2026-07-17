"""Wire Stage 3 validation pipeline with all 11 validators."""
from __future__ import annotations
from athena_x_runtime_validation_types import VALIDATOR_VERSION
from athena_x_runtime_audit_trail import AuditTrail
from athena_x_validator_base import ValidationPipeline
from athena_x_validator_schema import SchemaValidator
from athena_x_validator_timestamp import TimestampValidator
from athena_x_validator_market_calendar import MarketCalendarValidator
from athena_x_validator_cross_provider import CrossProviderValidator
from athena_x_validator_market_logic import MarketLogicValidator
from athena_x_validator_completeness import CompletenessValidator
from athena_x_validator_duplicate import DuplicateDetector
from athena_x_validator_outlier import OutlierDetector
from athena_x_validator_confidence import ConfidenceEngine
from athena_x_validator_market_state import MarketStateValidator
from athena_x_validator_quarantine import QuarantineManager


def create_validation_pipeline(
    *,
    audit_trail: AuditTrail | None = None,
    quarantine_manager: QuarantineManager | None = None,
) -> tuple[ValidationPipeline, AuditTrail, QuarantineManager]:
    """Create the full 11-validator pipeline in correct order.

    Order (per Stage 3 plan):
      1. Schema (blocking)
      2. Timestamp (blocking)
      3. Market Calendar (blocking)
      4. Cross-Provider (non-blocking)
      5. Market Logic (blocking)
      6. Completeness (non-blocking)
      7. Duplicate (blocking)
      8. Outlier (non-blocking — quarantine)
      9. Confidence (non-blocking)
      10. (Quality Classification is done by pipeline itself via QualityGrade)
      11. Market State (non-blocking — synchronization check)
    """
    audit = audit_trail or AuditTrail()
    quarantine = quarantine_manager or QuarantineManager()

    validators = [
        SchemaValidator(),              # 1
        TimestampValidator(),           # 2
        MarketCalendarValidator(),      # 3
        CrossProviderValidator(),       # 4
        MarketLogicValidator(),         # 5
        CompletenessValidator(),        # 6
        DuplicateDetector(),            # 7
        OutlierDetector(),              # 8
        ConfidenceEngine(),             # 9
        # 10 = pipeline itself (QualityGrade.from_confidence)
        MarketStateValidator(),         # 11
    ]

    pipeline = ValidationPipeline(validators=validators, audit_trail=audit)
    return pipeline, audit, quarantine
