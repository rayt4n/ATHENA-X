"""Base validator framework.

Each validator implements `validate(record, context) -> ValidationResult`.
Validators are PURE FUNCTIONS — deterministic, no side effects, no time-dependent
logic. This ensures replay determinism (Stage 3 req: replay capability).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus,
)


@dataclass
class ValidatorConfig:
    """Configuration for a validator."""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    # If True, a REJECTED status from this validator halts the pipeline
    # (subsequent validators don't run). If False, the pipeline continues.
    blocking: bool = True


class BaseValidator(ABC):
    """Abstract base class for all validators.

    Subclasses implement `validate()`. The base class provides:
      - Name + version metadata
      - Enable/disable toggle
      - Blocking behavior (does a rejection halt the pipeline?)
    """

    def __init__(self, config: ValidatorConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def blocking(self) -> bool:
        return self.config.blocking

    @abstractmethod
    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate a record. MUST be deterministic.

        Args:
            record: the raw data record (dict)
            context: validation context (provider, symbol, peers, etc.)

        Returns:
            ValidationResult with status, reason, confidence_delta
        """
        ...

    def _passed(self, message: str = "") -> ValidationResult:
        """Helper: return a 'passed' result."""
        from athena_x_runtime_validation_types import create_result, ValidationReason
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.VERIFIED,
            reason=ValidationReason.PASSED,
            confidence_delta=0.0,
            message=message,
        )

    def _warning(self, reason, message: str, confidence_delta: float = -0.1) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.WARNING,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )

    def _quarantine(self, reason, message: str, confidence_delta: float = -0.5) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.QUARANTINED,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )

    def _reject(self, reason, message: str, confidence_delta: float = -1.0) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.REJECTED,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )
