"""Schema registry — Stage 4 additional req.

Centralized service where every AI agent retrieves canonical schemas.
Allows adding new providers, asset classes, or data fields with minimal changes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.schema-registry")


@dataclass(frozen=True)
class SchemaVersion:
    """Semantic version for schema evolution."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, s: str) -> "SchemaVersion":
        parts = s.split(".")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Same major version = compatible."""
        return self.major == other.major


@dataclass
class SchemaDefinition:
    """A canonical schema definition."""
    name: str  # "MarketRecord", "OptionsRecord", etc.
    version: SchemaVersion
    fields: dict[str, str]  # field_name → type (e.g., "last_price" → "float")
    required: list[str]
    optional: list[str]
    description: str = ""


class SchemaRegistry:
    """Centralized registry of canonical schemas.

    Usage:
        registry = SchemaRegistry()
        registry.register(MARKET_RECORD_SCHEMA)
        schema = registry.get("MarketRecord", version="1.0.0")
        # All AI agents retrieve schemas from here instead of embedding in code
    """

    def __init__(self):
        self._schemas: dict[str, dict[str, SchemaDefinition]] = {}  # name → version_str → def
        self._lock = RLock()

    def register(self, schema: SchemaDefinition) -> None:
        """Register a schema version."""
        with self._lock:
            version_str = str(schema.version)
            self._schemas.setdefault(schema.name, {})[version_str] = schema
            log.info("schema_registered",
                     name=schema.name,
                     version=version_str,
                     fields=len(schema.fields))

    def get(self, name: str, version: str | None = None) -> SchemaDefinition | None:
        """Get a schema by name and optional version.

        If version is None, returns the latest registered version.
        """
        with self._lock:
            versions = self._schemas.get(name, {})
            if not versions:
                return None
            if version is None:
                # Get latest (highest semver)
                latest = max(versions.keys(), key=lambda v: tuple(map(int, v.split("."))))
                return versions[latest]
            return versions.get(version)

    def list_schemas(self) -> list[str]:
        with self._lock:
            return list(self._schemas.keys())

    def list_versions(self, name: str) -> list[str]:
        with self._lock:
            return list(self._schemas.get(name, {}).keys())

    def validate_record(self, name: str, record: dict, version: str | None = None) -> tuple[bool, list[str]]:
        """Validate a record against its schema.

        Returns (is_valid, list_of_errors).
        """
        schema = self.get(name, version)
        if schema is None:
            return False, [f"Unknown schema: {name}"]

        errors = []
        for required_field in schema.required:
            if required_field not in record:
                errors.append(f"Missing required field: {required_field}")
            elif record[required_field] is None:
                errors.append(f"Null value in required field: {required_field}")

        # Check for unknown fields (warn, don't fail)
        known = set(schema.fields.keys())
        unknown = set(record.keys()) - known
        if unknown:
            log.warning("unknown_fields", schema=name, fields=list(unknown))

        return len(errors) == 0, errors
