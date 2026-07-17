"""Tests for backup manager (Stage 5 req 9)."""
import pytest
from athena_x_runtime_db_backup import BackupManager, BackupType


class FakeDataProvider:
    """Fake data provider for testing."""
    def __init__(self):
        self.data = {
            "canonical_market": [{"symbol": "SPY", "last": 450.0}],
            "canonical_options": [{"symbol": "NVDA", "strike": 125.0}],
        }

    async def dump_schema(self, schema):
        return self.data.get(schema, [])

    async def restore_schema(self, schema, data):
        self.data[schema] = data
        return len(data)


@pytest.fixture
def backup_mgr(tmp_path):
    return BackupManager(backup_root=tmp_path / "backups")


async def test_backup_creates_files(backup_mgr):
    """Backup creates files on disk."""
    provider = FakeDataProvider()
    result = await backup_mgr.backup(
        schemas=["canonical_market", "canonical_options"],
        data_provider=provider,
    )
    assert result.success
    assert len(result.schemas_included) == 2
    assert result.size_bytes > 0


async def test_restore_recovers_data(backup_mgr):
    """Restore recovers data from backup."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    # Clear provider data
    provider.data["canonical_market"] = []
    # Restore
    result = await backup_mgr.restore(backup.backup_id, data_provider=provider)
    assert result.success
    assert "canonical_market" in result.schemas_restored
    assert result.records_restored == 1
    assert len(provider.data["canonical_market"]) == 1


async def test_restore_nonexistent_backup_fails(backup_mgr):
    result = await backup_mgr.restore("nonexistent-id")
    assert not result.success
    assert "not found" in result.error


async def test_verify_backup(backup_mgr):
    """verify_backup checks backup exists."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    assert backup_mgr.verify_backup(backup.backup_id) is True
    assert backup_mgr.verify_backup("nonexistent") is False


async def test_verify_restore(backup_mgr):
    """verify_restore tests that backup can be restored (CI/CD check)."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    result = await backup_mgr.verify_restore(backup.backup_id, data_provider=provider)
    assert result is True


def test_backup_types():
    assert BackupType.FULL.value == "full"
    assert BackupType.INCREMENTAL.value == "incremental"
