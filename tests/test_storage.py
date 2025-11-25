"""Tests for the storage module."""

from pathlib import Path

import pytest

from linear_agent.storage import AgentState, AuditEntry, AuditStorage, StateStorage


class TestAuditEntry:
    """Tests for AuditEntry."""

    def test_success_entry(self) -> None:
        """Test creating a success entry."""
        entry = AuditEntry.success("test_action", {"key": "value"})
        assert entry.action == "test_action"
        assert entry.status == "success"
        assert entry.details == {"key": "value"}
        assert entry.error is None
        assert entry.suggestion is None
        assert entry.timestamp is not None

    def test_failure_entry(self) -> None:
        """Test creating a failure entry."""
        entry = AuditEntry.failure(
            "test_action",
            "Something went wrong",
            "Try again later",
            {"context": "info"},
        )
        assert entry.action == "test_action"
        assert entry.status == "failure"
        assert entry.error == "Something went wrong"
        assert entry.suggestion == "Try again later"
        assert entry.details == {"context": "info"}

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        entry = AuditEntry.success("action", {"key": "value"})
        data = entry.to_dict()
        assert "timestamp" in data
        assert data["action"] == "action"
        assert data["status"] == "success"
        assert data["details"] == {"key": "value"}


class TestAuditStorage:
    """Tests for AuditStorage."""

    @pytest.fixture
    def audit_file(self, tmp_path: Path) -> Path:
        """Create a temporary audit file path."""
        return tmp_path / "test_audit.jsonl"

    @pytest.fixture
    def audit_storage(self, audit_file: Path) -> AuditStorage:
        """Create an AuditStorage instance."""
        return AuditStorage(audit_file, max_entries=100)

    async def test_append_and_read(self, audit_storage: AuditStorage) -> None:
        """Test appending and reading entries."""
        entry1 = AuditEntry.success("action1")
        entry2 = AuditEntry.failure("action2", "error")

        await audit_storage.append(entry1)
        await audit_storage.append(entry2)

        entries = await audit_storage.read_all()
        assert len(entries) == 2
        assert entries[0].action == "action1"
        assert entries[0].status == "success"
        assert entries[1].action == "action2"
        assert entries[1].status == "failure"

    async def test_read_failures(self, audit_storage: AuditStorage) -> None:
        """Test reading only failure entries."""
        await audit_storage.append(AuditEntry.success("action1"))
        await audit_storage.append(AuditEntry.failure("action2", "error1"))
        await audit_storage.append(AuditEntry.success("action3"))
        await audit_storage.append(AuditEntry.failure("action4", "error2"))

        failures = await audit_storage.read_failures()
        assert len(failures) == 2
        assert failures[0].action == "action2"
        assert failures[1].action == "action4"

    async def test_read_empty_file(self, audit_storage: AuditStorage) -> None:
        """Test reading from non-existent file."""
        entries = await audit_storage.read_all()
        assert entries == []

    async def test_truncate(self, audit_storage: AuditStorage) -> None:
        """Test truncating the audit log."""
        # Add 10 entries
        for i in range(10):
            await audit_storage.append(AuditEntry.success(f"action{i}"))

        # Truncate to 5
        removed = await audit_storage.truncate(5)
        assert removed == 5

        entries = await audit_storage.read_all()
        assert len(entries) == 5
        # Should keep the last 5
        assert entries[0].action == "action5"
        assert entries[4].action == "action9"


class TestAgentState:
    """Tests for AgentState."""

    def test_default_values(self) -> None:
        """Test default state values."""
        state = AgentState()
        assert state.is_healthy is True
        assert state.quota_remaining is None
        assert state.processed_issues == []

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        state = AgentState(
            is_healthy=False,
            quota_remaining=100,
            quota_limit=1000,
        )
        data = state.to_dict()
        assert data["is_healthy"] is False
        assert data["quota_remaining"] == 100
        assert data["quota_limit"] == 1000

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        data = {
            "last_health_check": "2024-01-01T00:00:00Z",
            "is_healthy": True,
            "quota_remaining": 500,
            "quota_limit": 1000,
            "last_error": None,
            "processed_issues": ["issue1", "issue2"],
            "metadata": {"key": "value"},
        }
        state = AgentState.from_dict(data)
        assert state.is_healthy is True
        assert state.quota_remaining == 500
        assert len(state.processed_issues) == 2


class TestStateStorage:
    """Tests for StateStorage."""

    @pytest.fixture
    def state_file(self, tmp_path: Path) -> Path:
        """Create a temporary state file path."""
        return tmp_path / "test_state.json"

    @pytest.fixture
    def state_storage(self, state_file: Path) -> StateStorage:
        """Create a StateStorage instance."""
        return StateStorage(state_file)

    async def test_save_and_load(self, state_storage: StateStorage) -> None:
        """Test saving and loading state."""
        state = AgentState(
            is_healthy=True,
            quota_remaining=500,
            quota_limit=1000,
            processed_issues=["issue1"],
        )

        await state_storage.save(state)
        loaded = await state_storage.load()

        assert loaded.is_healthy == state.is_healthy
        assert loaded.quota_remaining == state.quota_remaining
        assert loaded.quota_limit == state.quota_limit
        assert loaded.processed_issues == state.processed_issues

    async def test_load_missing_file(self, state_storage: StateStorage) -> None:
        """Test loading from non-existent file."""
        state = await state_storage.load()
        assert isinstance(state, AgentState)
        assert state.is_healthy is True

    async def test_update(self, state_storage: StateStorage) -> None:
        """Test updating specific fields."""
        initial = AgentState(is_healthy=True, quota_remaining=1000)
        await state_storage.save(initial)

        updated = await state_storage.update(quota_remaining=500, is_healthy=False)
        assert updated.quota_remaining == 500
        assert updated.is_healthy is False

        # Verify persisted
        loaded = await state_storage.load()
        assert loaded.quota_remaining == 500
        assert loaded.is_healthy is False
