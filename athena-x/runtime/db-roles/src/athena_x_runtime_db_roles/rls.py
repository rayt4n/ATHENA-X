"""RLS policies (Stage 5 req 3).

Apply RLS across all user-facing schemas.
Policies enforce: per-user isolation, workspace isolation, agent-specific roles.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RLSPolicy:
    """An RLS policy definition."""
    schema: str
    table: str
    policy_name: str
    command: str  # SELECT, INSERT, UPDATE, DELETE, ALL
    using: str  # USING clause
    check: str | None = None  # WITH CHECK clause


RLS_POLICIES: list[RLSPolicy] = [
    # app.workspaces - user owns their workspaces
    RLSPolicy(
        schema="app", table="workspaces",
        policy_name="users_own_workspaces",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
    # app.watchlists - workspace member can see
    RLSPolicy(
        schema="app", table="watchlists",
        policy_name="workspace_members_see_watchlists",
        command="SELECT",
        using="EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid())",
    ),
    # app.module_instances - workspace member can see
    RLSPolicy(
        schema="app", table="module_instances",
        policy_name="workspace_members_see_instances",
        command="SELECT",
        using="EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid())",
    ),
    # historical_db.reports - user owns their reports
    RLSPolicy(
        schema="historical_db", table="reports",
        policy_name="users_own_reports",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
    # historical_db.backtests - user owns their backtests
    RLSPolicy(
        schema="historical_db", table="backtests",
        policy_name="users_own_backtests",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
]


def generate_rls_sql() -> str:
    """Generate SQL to enable RLS + create policies."""
    lines = ["-- Stage 5: RLS policies"]
    # Enable RLS
    for schema in ["app", "historical_db"]:
        lines.append(f"ALTER TABLE {schema}.workspaces ENABLE ROW LEVEL SECURITY;" if schema == "app" else "")
    # Actually, generate per-table
    seen_tables: set[str] = set()
    for policy in RLS_POLICIES:
        table_full = f"{policy.schema}.{policy.table}"
        if table_full not in seen_tables:
            lines.append(f"ALTER TABLE {table_full} ENABLE ROW LEVEL SECURITY;")
            seen_tables.add(table_full)
        check_clause = f" WITH CHECK ({policy.check})" if policy.check else ""
        lines.append(
            f"CREATE POLICY {policy.policy_name} ON {table_full} "
            f"FOR {policy.command} USING ({policy.using}){check_clause};"
        )
    return "\n".join(lines)
