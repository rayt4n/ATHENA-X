"""Database role definitions (Stage 5 req 2).

Each schema has exactly one writing authority.
Enforcement: dedicated database roles per agent.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DBRole:
    """A database role with specific permissions."""
    name: str
    schema: str
    permissions: list[str]  # INSERT, UPDATE, SELECT, etc.
    description: str
    can_write: bool = True


# 12 writer roles - one per schema
DB_ROLES: dict[str, DBRole] = {
    "role_market_standardizer": DBRole(
        name="role_market_standardizer",
        schema="canonical_market",
        permissions=["INSERT", "UPDATE"],
        description="Market Standardization Agent - ONLY writer to canonical_market",
    ),
    "role_options_standardizer": DBRole(
        name="role_options_standardizer",
        schema="canonical_options",
        permissions=["INSERT", "UPDATE"],
        description="Options Standardization Agent - ONLY writer to canonical_options",
    ),
    "role_news_standardizer": DBRole(
        name="role_news_standardizer",
        schema="canonical_news",
        permissions=["INSERT"],
        description="News Standardization Agent - ONLY writer to canonical_news",
    ),
    "role_macro_standardizer": DBRole(
        name="role_macro_standardizer",
        schema="canonical_macro",
        permissions=["INSERT"],
        description="Macro Standardization Agent - ONLY writer to canonical_macro",
    ),
    "role_validation": DBRole(
        name="role_validation",
        schema="validation_db",
        permissions=["INSERT"],
        description="Validation Agents - write validation decisions",
    ),
    "role_intelligence": DBRole(
        name="role_intelligence",
        schema="ai_intelligence",
        permissions=["INSERT"],
        description="Intelligence Agents - write TA/Options/News/Macro signals",
    ),
    "role_decision": DBRole(
        name="role_decision",
        schema="forecast_db",
        permissions=["INSERT"],
        description="Decision Agents - write regime/scenario/forecast",
    ),
    "role_report_engine": DBRole(
        name="role_report_engine",
        schema="historical_db",
        permissions=["INSERT"],
        description="Report Engine - write reports + backtests",
    ),
    "role_replay_recorder": DBRole(
        name="role_replay_recorder",
        schema="market_replay_db",
        permissions=["INSERT"],
        description="Market Replay Recorder - write minute snapshots",
    ),
    "role_self_correction": DBRole(
        name="role_self_correction",
        schema="ai_memory_db",
        permissions=["INSERT", "UPDATE"],
        description="Self-Correction Agents - write predictions + outcomes + lessons",
    ),
    "role_provider": DBRole(
        name="role_provider",
        schema="raw_landing",
        permissions=["INSERT"],
        description="Provider Adapters - write raw payloads",
    ),
    "role_app_user": DBRole(
        name="role_app_user",
        schema="app",
        permissions=["SELECT", "INSERT", "UPDATE", "DELETE"],
        description="Frontend users - own rows only (RLS enforced)",
    ),
}


# Reader role - read-only access to all schemas
READER_ROLE = DBRole(
    name="role_reader",
    schema="*",
    permissions=["SELECT"],
    description="Read-only access to all canonical schemas",
    can_write=False,
)


ROLE_PERMISSIONS = {name: role.permissions for name, role in DB_ROLES.items()}


def get_role_for_schema(schema: str) -> DBRole | None:
    """Get the writer role for a schema."""
    for role in DB_ROLES.values():
        if role.schema == schema:
            return role
    return None


def list_roles() -> list[str]:
    """List all role names."""
    return list(DB_ROLES.keys())


def generate_role_sql() -> str:
    """Generate SQL to create all roles."""
    lines = ["-- Stage 5: Database roles (writer-lock enforcement)"]
    for role in DB_ROLES.values():
        lines.append(f"CREATE ROLE {role.name} NOLOGIN;")
        lines.append(f"GRANT {', '.join(role.permissions)} ON SCHEMA {role.schema} TO {role.name};")
        lines.append("")
    # Reader role
    lines.append("CREATE ROLE role_reader NOLOGIN;")
    lines.append("GRANT SELECT ON ALL TABLES IN SCHEMA canonical_market, canonical_options, canonical_news, canonical_macro, validation_db, ai_intelligence, forecast_db, historical_db, market_replay_db, ai_memory_db TO role_reader;")
    return "\n".join(lines)
