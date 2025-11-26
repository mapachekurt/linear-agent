"""Self-learning utilities that capture agent telemetry and propose improvements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .logging_utils import LogContext, log_with_context
from .storage import AuditEntry, FileStorage


@dataclass
class ImprovementSuggestion:
    """Represents a suggestion generated from agent behavior."""

    summary: str
    recommendation: str


class SelfLearningRecorder:
    """Record agent actions and produce suggestions based on failures."""

    def __init__(self, storage: FileStorage):
        self.storage = storage

    def record_success(self, action: str, details: dict) -> None:
        """Persist a successful action to the audit log."""

        entry = AuditEntry(event=action, details={**details, "outcome": "success"})
        self.storage.append_audit_entries([entry])

    def record_failure(self, action: str, details: dict) -> ImprovementSuggestion:
        """Persist a failed action and generate an improvement suggestion."""

        entry = AuditEntry(event=action, details={**details, "outcome": "failure"})
        self.storage.append_audit_entries([entry])
        recommendation = (
            "Investigate repeated failures for this action and consider adding additional "
            "validation or fallback strategies."
        )
        return ImprovementSuggestion(summary=action, recommendation=recommendation)

    def emit_suggestions(self, logger, context: LogContext) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions from persisted audit history."""

        entries = self.storage.load_audit_entries(limit=100)
        failures = [entry for entry in entries if entry.details.get("outcome") == "failure"]
        suggestions = [
            ImprovementSuggestion(
                summary=f"Stabilize action '{entry.event}'",
                recommendation="Add retries, better validation, and richer telemetry.",
            )
            for entry in failures
        ]
        log_with_context(
            logger=logger,
            level=logger.level,
            message=f"Generated {len(suggestions)} improvement suggestions",
            context=context,
        )
        return suggestions
