"""Confidence engine — Stage 3 req 2.9.

Assigns every record a confidence score (0.0..1.0).

Factors:
  - Provider reliability (historical accuracy)
  - Agreement with peers (cross-provider)
  - Freshness (how recent)
  - Latency (provider response time)
  - Completeness (all required fields present)
  - Historical provider accuracy

Example:
  Price    0.998
  News     0.92
  Dark Pool 0.75

This engine doesn't replace the pipeline's accumulated confidence_delta —
it adds a final adjustment based on factors the other validators don't see.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)
from athena_x_runtime_institutional_metadata import ProviderDefaults


@dataclass
class ConfidenceFactors:
    """Factors influencing confidence."""
    provider_reliability: float = 1.0    # 0..1, from ProviderDefaults
    peer_agreement: float = 1.0          # 0..1, set by cross-provider validator
    freshness: float = 1.0               # 0..1, 1=just received
    latency_score: float = 1.0           # 0..1, 1=instant
    completeness: float = 1.0            # 0..1, 1=all fields
    historical_accuracy: float = 1.0     # 0..1, rolling avg

    @property
    def weighted_score(self) -> float:
        """Compute weighted confidence score.

        Weights (sum to 1.0):
          - provider_reliability: 0.25
          - peer_agreement: 0.25
          - freshness: 0.15
          - latency: 0.10
          - completeness: 0.15
          - historical_accuracy: 0.10
        """
        return (
            0.25 * self.provider_reliability +
            0.25 * self.peer_agreement +
            0.15 * self.freshness +
            0.10 * self.latency_score +
            0.15 * self.completeness +
            0.10 * self.historical_accuracy
        )


class ConfidenceEngine(BaseValidator):
    """Computes a confidence score for each record."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="confidence-engine",
            blocking=False,
        ))
        self._provider_accuracy: dict[str, float] = {}  # rolling accuracy per provider

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Compute confidence factors and return a (positive) confidence delta."""
        factors = self._compute_factors(record, context)
        score = factors.weighted_score

        # The pipeline starts at 1.0 and deducts. We want to SET the final score,
        # so we return a delta that brings the accumulated score closer to ours.
        # If score is 0.95, we want to boost by ~0 (already high).
        # If score is 0.5, we want to deduct ~0.5.
        # Use: delta = score - 1.0 (so final = 1.0 + delta = score)
        # But other validators have already deducted. So we add a small boost
        # for high-confidence records and a larger deduction for low-confidence.

        if score >= 0.95:
            delta = 0.05  # small boost
            status = ValidationStatus.VERIFIED
            reason = ValidationReason.PASSED
            message = f"high confidence ({score:.3f})"
        elif score >= 0.80:
            delta = 0.0  # neutral
            status = ValidationStatus.VERIFIED
            reason = ValidationReason.PASSED
            message = f"acceptable confidence ({score:.3f})"
        elif score >= 0.60:
            delta = -0.1  # small deduction
            status = ValidationStatus.WARNING
            reason = ValidationReason.UNKNOWN
            message = f"low confidence ({score:.3f})"
        elif score >= 0.30:
            delta = -0.3
            status = ValidationStatus.QUARANTINED
            reason = ValidationReason.UNKNOWN
            message = f"very low confidence ({score:.3f})"
        else:
            delta = -0.5
            status = ValidationStatus.QUARANTINED
            reason = ValidationReason.UNKNOWN
            message = f"reject-level confidence ({score:.3f})"

        return ValidationResult(
            validatorName=self.name,
            status=status,
            reason=reason,
            confidenceDelta=delta,
            message=message,
            metadata={"confidence_score": score, "factors": factors.__dict__},
        )

    def _compute_factors(self, record: Any, context: ValidationContext) -> ConfidenceFactors:
        """Compute confidence factors from record + context."""
        # Provider reliability
        provider_reliability = ProviderDefaults.get_confidence(context.provider)

        # Peer agreement (1.0 if no peers, else based on count)
        peer_count = len(context.peer_values)
        if peer_count == 0:
            peer_agreement = 0.5  # no peers = can't verify
        elif peer_count == 1:
            peer_agreement = 0.8
        else:
            peer_agreement = min(1.0, 0.8 + 0.1 * (peer_count - 1))

        # Freshness (use recent_values count as proxy — more recent = more data)
        freshness = 1.0 if len(context.recent_values) >= 5 else 0.7

        # Latency (from record's metadata if present, else default)
        latency_score = 1.0
        if isinstance(record, dict):
            lat = record.get("provider_latency") or record.get("latency")
            if isinstance(lat, (int, float)):
                latency_score = max(0.0, 1.0 - lat / 1000.0)  # 1s = 0 score

        # Completeness
        completeness = 1.0
        if isinstance(record, dict):
            required = ["symbol", "last", "timestamp"]
            missing = sum(1 for f in required if f not in record or record[f] is None)
            completeness = 1.0 - 0.2 * missing

        # Historical accuracy
        historical_accuracy = self._provider_accuracy.get(context.provider, 0.9)

        return ConfidenceFactors(
            provider_reliability=provider_reliability,
            peer_agreement=peer_agreement,
            freshness=freshness,
            latency_score=latency_score,
            completeness=completeness,
            historical_accuracy=historical_accuracy,
        )

    def update_provider_accuracy(self, provider: str, accuracy: float) -> None:
        """Update historical accuracy for a provider (called by self-correction)."""
        self._provider_accuracy[provider] = accuracy
