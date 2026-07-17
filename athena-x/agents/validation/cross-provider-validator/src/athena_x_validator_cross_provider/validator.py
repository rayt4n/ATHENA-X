"""Cross-provider validator — Stage 3 req 2.4.

Example:
  Yahoo      752.44
  Polygon    752.45
  Finnhub    752.46
  Consensus  752.45

If another provider returns 742.00 → REJECT.

Consensus is computed as the median of peer values. A record is rejected if
its value deviates from consensus by more than the tolerance (default 0.5%).
"""
from __future__ import annotations
import statistics
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Default tolerance: 0.5% deviation from consensus
DEFAULT_TOLERANCE_PCT = 0.005
# Minimum number of peers required for consensus
MIN_PEERS_FOR_CONSENSUS = 2


class ConsensusResult:
    """Result of consensus computation."""
    def __init__(self, consensus: float, peers: dict[str, float],
                 outliers: dict[str, float]):
        self.consensus = consensus
        self.peers = peers
        self.outliers = outliers

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    @property
    def has_consensus(self) -> bool:
        return len(self.peers) >= MIN_PEERS_FOR_CONSENSUS


class CrossProviderValidator(BaseValidator):
    """Validates a record against peer values from other providers."""

    def __init__(self, tolerance_pct: float = DEFAULT_TOLERANCE_PCT):
        super().__init__(ValidatorConfig(
            name="cross-provider-validator",
            blocking=False,  # don't halt — record warning/quarantine
        ))
        self._tolerance_pct = tolerance_pct

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record's 'last' value against peers."""
        if not isinstance(record, dict):
            return self._passed("non-dict record, skipping cross-provider check")

        value = record.get("last")
        if value is None or not isinstance(value, (int, float)):
            return self._passed("no 'last' field to validate")

        peers = context.peer_values
        if not peers:
            # Single source — warning, can't verify
            return self._warning(
                ValidationReason.SINGLE_SOURCE,
                f"Only one provider ({context.provider}); cannot cross-verify",
                confidence_delta=-0.1,
            )

        # Filter to numeric peers
        numeric_peers = {k: v for k, v in peers.items() if isinstance(v, (int, float))}
        if len(numeric_peers) < MIN_PEERS_FOR_CONSENSUS - 1:  # -1 because we count ourselves
            return self._warning(
                ValidationReason.SINGLE_SOURCE,
                f"Only {len(numeric_peers)} peer(s); need {MIN_PEERS_FOR_CONSENSUS} for consensus",
                confidence_delta=-0.05,
            )

        # Include our value in consensus
        all_values = list(numeric_peers.values()) + [value]
        consensus = statistics.median(all_values)

        # Check deviation
        deviation = abs(value - consensus) / consensus if consensus > 0 else 0
        if deviation > self._tolerance_pct:
            # Determine if WE are the outlier, or a peer is
            # If our value is further from consensus than any peer, we're the outlier
            peer_deviations = [
                abs(v - consensus) / consensus if consensus > 0 else 0
                for v in numeric_peers.values()
            ]
            max_peer_deviation = max(peer_deviations) if peer_deviations else 0

            if deviation > max_peer_deviation:
                return self._reject(
                    ValidationReason.CONSENSUS_DISAGREEMENT,
                    f"Value {value} deviates {deviation:.4%} from consensus {consensus:.2f}",
                )
            else:
                # A peer is the outlier — we're fine, but flag it
                return self._warning(
                    ValidationReason.CONSENSUS_DISAGREEMENT,
                    f"Peer outlier detected; consensus {consensus:.2f}",
                    confidence_delta=-0.05,
                )

        # Close to consensus — small confidence boost
        return ValidationResult(
            validatorName=self.name,
            status=ValidationStatus.VERIFIED,
            reason=ValidationReason.PASSED,
            confidenceDelta=min(0.05, 0.05 - deviation * 10),  # up to +0.05 boost
            message=f"Matches consensus {consensus:.2f} (deviation: {deviation:.4%})",
        )
