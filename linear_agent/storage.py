"""Local storage primitives for the Linear agent."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

from .config import StorageSettings


@dataclass
class AuditEntry:
    """Structured audit record for agent actions."""

    event: str
    details: dict


class FileStorage:
    """Persist audit events and state to disk."""

    def __init__(self, settings: StorageSettings):
        self.settings = settings
        Path(self.settings.audit_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.settings.state_path).parent.mkdir(parents=True, exist_ok=True)

    def append_audit_entries(self, entries: Iterable[AuditEntry]) -> None:
        """Append audit entries to the configured log file."""

        path = Path(self.settings.audit_log_path)
        with path.open("a", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(asdict(entry)) + "\n")

    def load_audit_entries(self, limit: int | None = None) -> List[AuditEntry]:
        """Load audit entries from disk for inspection or replay."""

        path = Path(self.settings.audit_log_path)
        if not path.exists():
            return []
        entries: List[AuditEntry] = []
        with path.open("r", encoding="utf-8") as handle:
            for idx, line in enumerate(handle):
                if limit is not None and idx >= limit:
                    break
                record = json.loads(line.strip())
                entries.append(AuditEntry(event=record["event"], details=record["details"]))
        return entries

    def save_state(self, state: dict) -> None:
        """Persist agent state to the configured state file."""

        path = Path(self.settings.state_path)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)

    def load_state(self) -> dict:
        """Load persisted agent state, returning an empty mapping when missing."""

        path = Path(self.settings.state_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
