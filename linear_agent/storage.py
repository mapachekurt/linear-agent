"""
Storage module for Linear Agent.

This module provides persistent storage for audit entries (JSONL)
and agent state (JSON).
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""

    timestamp: str
    action: str
    status: str  # "success" or "failure"
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    suggestion: str | None = None

    @classmethod
    def success(cls, action: str, details: dict[str, Any] | None = None) -> "AuditEntry":
        """Create a success audit entry."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            status="success",
            details=details or {},
        )

    @classmethod
    def failure(
        cls,
        action: str,
        error: str,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> "AuditEntry":
        """Create a failure audit entry."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            status="failure",
            details=details or {},
            error=error,
            suggestion=suggestion,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary."""
        return asdict(self)


class AuditStorage:
    """JSONL-based audit log storage."""

    def __init__(self, file_path: Path, max_entries: int = 10000):
        """
        Initialize audit storage.

        Args:
            file_path: Path to the JSONL audit log file.
            max_entries: Maximum number of entries to keep.
        """
        self.file_path = file_path
        self.max_entries = max_entries
        self._lock = asyncio.Lock()

    async def append(self, entry: AuditEntry) -> None:
        """
        Append an audit entry to the log.

        Args:
            entry: The audit entry to append.
        """
        async with self._lock:
            try:
                async with aiofiles.open(self.file_path, mode="a") as f:
                    await f.write(json.dumps(entry.to_dict()) + "\n")
                logger.debug(f"Appended audit entry: {entry.action}")
            except Exception as e:
                logger.error(f"Failed to write audit entry: {e}")
                raise

    async def read_all(self) -> list[AuditEntry]:
        """
        Read all audit entries from the log.

        Returns:
            List of all audit entries.
        """
        entries: list[AuditEntry] = []
        if not self.file_path.exists():
            return entries

        try:
            async with aiofiles.open(self.file_path) as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        entries.append(AuditEntry(**data))
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            raise

        return entries

    async def read_failures(self) -> list[AuditEntry]:
        """
        Read only failure entries from the log.

        Returns:
            List of failure audit entries.
        """
        all_entries = await self.read_all()
        return [e for e in all_entries if e.status == "failure"]

    async def truncate(self, keep_entries: int | None = None) -> int:
        """
        Truncate the audit log to keep only recent entries.

        Args:
            keep_entries: Number of entries to keep (defaults to max_entries).

        Returns:
            Number of entries removed.
        """
        keep = keep_entries or self.max_entries
        async with self._lock:
            entries = await self.read_all()
            if len(entries) <= keep:
                return 0

            removed = len(entries) - keep
            entries_to_keep = entries[-keep:]

            async with aiofiles.open(self.file_path, mode="w") as f:
                for entry in entries_to_keep:
                    await f.write(json.dumps(entry.to_dict()) + "\n")

            logger.info(f"Truncated audit log, removed {removed} entries")
            return removed


@dataclass
class AgentState:
    """Represents the current state of the agent."""

    last_health_check: str | None = None
    is_healthy: bool = True
    quota_remaining: int | None = None
    quota_limit: int | None = None
    last_error: str | None = None
    processed_issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        """Create state from dictionary."""
        return cls(**data)


class StateStorage:
    """JSON-based agent state storage."""

    def __init__(self, file_path: Path):
        """
        Initialize state storage.

        Args:
            file_path: Path to the JSON state file.
        """
        self.file_path = file_path
        self._lock = asyncio.Lock()

    async def save(self, state: AgentState) -> None:
        """
        Save agent state to file.

        Args:
            state: The agent state to save.
        """
        async with self._lock:
            try:
                async with aiofiles.open(self.file_path, mode="w") as f:
                    await f.write(json.dumps(state.to_dict(), indent=2))
                logger.debug("Saved agent state")
            except Exception as e:
                logger.error(f"Failed to save agent state: {e}")
                raise

    async def load(self) -> AgentState:
        """
        Load agent state from file.

        Returns:
            The loaded agent state, or a new state if file doesn't exist.
        """
        if not self.file_path.exists():
            return AgentState()

        try:
            async with aiofiles.open(self.file_path) as f:
                content = await f.read()
                data = json.loads(content)
                return AgentState.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load agent state: {e}")
            return AgentState()

    async def update(self, **kwargs: Any) -> AgentState:
        """
        Update specific fields in the agent state.

        Args:
            **kwargs: Fields to update.

        Returns:
            The updated agent state.
        """
        state = await self.load()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        await self.save(state)
        return state
