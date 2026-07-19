"""Validator registry — tracks all registered validators."""
from __future__ import annotations
from threading import Lock
from .base import BaseValidator


class ValidatorRegistry:
    """Thread-safe registry of validators."""
    def __init__(self):
        self._validators: dict[str, BaseValidator] = {}
        self._lock = Lock()

    def register(self, validator: BaseValidator) -> None:
        with self._lock:
            self._validators[validator.name] = validator

    def get(self, name: str) -> BaseValidator | None:
        with self._lock:
            return self._validators.get(name)

    def list_all(self) -> list[BaseValidator]:
        with self._lock:
            return list(self._validators.values())

    def list_enabled(self) -> list[BaseValidator]:
        with self._lock:
            return [v for v in self._validators.values() if v.enabled]
