"""Tests for DB roles (Stage 5 req 2)."""
import pytest
from athena_x_runtime_db_roles import DB_ROLES, get_role_for_schema, list_roles, generate_rls_sql


def test_12_writer_roles_defined():
    """12 writer roles - one per schema."""
    assert len(DB_ROLES) == 12


def test_each_schema_has_exactly_one_writer():
    """Each schema has exactly one writer role (writer-lock rule)."""
    schemas = [role.schema for role in DB_ROLES.values()]
    # No duplicates
    assert len(schemas) == len(set(schemas))


def test_get_role_for_canonical_market():
    """canonical_market's writer is role_market_standardizer."""
    role = get_role_for_schema("canonical_market")
    assert role is not None
    assert role.name == "role_market_standardizer"
    assert "INSERT" in role.permissions


def test_get_role_for_unknown_schema():
    assert get_role_for_schema("nonexistent") is None


def test_list_roles_returns_all():
    roles = list_roles()
    assert len(roles) == 12
    assert "role_market_standardizer" in roles
    assert "role_app_user" in roles


def test_role_permissions_are_write_or_read():
    """Writer roles have INSERT; reader doesn't."""
    for role in DB_ROLES.values():
        if role.can_write:
            assert "INSERT" in role.permissions
        else:
            assert "INSERT" not in role.permissions


def test_generate_rls_sql():
    """generate_rls_sql produces valid SQL."""
    sql = generate_rls_sql()
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY" in sql
    assert "users_own_workspaces" in sql
