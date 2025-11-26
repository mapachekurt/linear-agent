"""
Self-learning module for Linear Agent.

This module provides self-learning capabilities including
action logging, failure analysis, and recommendation generation.
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from linear_agent.storage import AuditEntry, AuditStorage

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """A recommendation based on failure patterns."""

    action: str
    suggestion: str
    confidence: float  # 0.0 to 1.0
    failure_count: int
    examples: list[str] = field(default_factory=list)


@dataclass
class ActionStats:
    """Statistics for a specific action type."""

    action: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    common_errors: list[tuple[str, int]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


@dataclass
class LearningReport:
    """Report summarizing learned patterns."""

    total_actions: int = 0
    success_count: int = 0
    failure_count: int = 0
    action_stats: list[ActionStats] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_actions == 0:
            return 0.0
        return self.success_count / self.total_actions


class SelfLearning:
    """Self-learning capabilities for the Linear Agent."""

    # Common failure patterns and their suggested fixes
    FAILURE_PATTERNS: dict[str, str] = {
        "rate limit": "Implement longer backoff delays or reduce request frequency",
        "not found": "Verify resource IDs before making requests",
        "unauthorized": "Check API key validity and permissions",
        "timeout": "Increase timeout settings or retry with exponential backoff",
        "invalid": "Validate input parameters before making API calls",
        "permission": "Verify API key has required scopes",
        "quota": "Monitor quota usage and implement request throttling",
    }

    def __init__(self, audit_storage: AuditStorage):
        """
        Initialize the self-learning module.

        Args:
            audit_storage: Storage for audit entries.
        """
        self._audit = audit_storage

    async def record_success(
        self,
        action: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """
        Record a successful action.

        Args:
            action: The action that succeeded.
            details: Optional additional details.

        Returns:
            The created audit entry.
        """
        entry = AuditEntry.success(action, details)
        await self._audit.append(entry)
        logger.debug(f"Recorded success: {action}")
        return entry

    async def record_failure(
        self,
        action: str,
        error: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """
        Record a failed action with auto-generated suggestion.

        Args:
            action: The action that failed.
            error: The error message.
            details: Optional additional details.

        Returns:
            The created audit entry.
        """
        suggestion = self._generate_suggestion(error)
        entry = AuditEntry.failure(action, error, suggestion, details)
        await self._audit.append(entry)
        logger.warning(f"Recorded failure: {action} - {error}")
        return entry

    def _generate_suggestion(self, error: str) -> str:
        """
        Generate an improvement suggestion based on error pattern.

        Args:
            error: The error message.

        Returns:
            Suggested improvement.
        """
        error_lower = error.lower()
        for pattern, suggestion in self.FAILURE_PATTERNS.items():
            if pattern in error_lower:
                return suggestion
        return "Review error logs and consider adding specific error handling"

    async def analyze_failures(self) -> list[Recommendation]:
        """
        Analyze failure patterns and generate recommendations.

        Returns:
            List of recommendations.
        """
        failures = await self._audit.read_failures()
        if not failures:
            return []

        # Group failures by action
        action_failures: dict[str, list[AuditEntry]] = defaultdict(list)
        for entry in failures:
            action_failures[entry.action].append(entry)

        recommendations = []
        for action, entries in action_failures.items():
            # Find common error patterns
            error_patterns: Counter[str] = Counter()
            for entry in entries:
                if entry.error:
                    # Normalize error for pattern matching
                    for pattern in self.FAILURE_PATTERNS:
                        if pattern in entry.error.lower():
                            error_patterns[pattern] += 1
                            break
                    else:
                        error_patterns["unknown"] += 1

            # Get most common pattern
            if error_patterns:
                most_common_pattern, count = error_patterns.most_common(1)[0]
                if most_common_pattern != "unknown":
                    suggestion = self.FAILURE_PATTERNS[most_common_pattern]
                else:
                    suggestion = "Investigate and add specific error handling"

                # Calculate confidence based on frequency
                confidence = min(1.0, count / 10)  # Max confidence at 10+ occurrences

                examples = [
                    e.error for e in entries[:3] if e.error
                ]  # Show up to 3 examples

                recommendations.append(
                    Recommendation(
                        action=action,
                        suggestion=suggestion,
                        confidence=confidence,
                        failure_count=len(entries),
                        examples=examples,
                    )
                )

        # Sort by failure count (most problematic first)
        recommendations.sort(key=lambda r: r.failure_count, reverse=True)
        return recommendations

    async def get_action_stats(self) -> list[ActionStats]:
        """
        Get statistics for all recorded actions.

        Returns:
            List of action statistics.
        """
        entries = await self._audit.read_all()
        if not entries:
            return []

        # Group by action
        action_entries: dict[str, list[AuditEntry]] = defaultdict(list)
        for entry in entries:
            action_entries[entry.action].append(entry)

        stats = []
        for action, entries_list in action_entries.items():
            successes = [e for e in entries_list if e.status == "success"]
            failures = [e for e in entries_list if e.status == "failure"]

            # Count common errors
            error_counts: Counter[str] = Counter()
            for entry in failures:
                if entry.error:
                    # Truncate long errors
                    short_error = entry.error[:100]
                    error_counts[short_error] += 1

            stats.append(
                ActionStats(
                    action=action,
                    total_count=len(entries_list),
                    success_count=len(successes),
                    failure_count=len(failures),
                    common_errors=error_counts.most_common(3),
                )
            )

        # Sort by total count
        stats.sort(key=lambda s: s.total_count, reverse=True)
        return stats

    async def generate_report(self) -> LearningReport:
        """
        Generate a comprehensive learning report.

        Returns:
            The learning report.
        """
        entries = await self._audit.read_all()
        recommendations = await self.analyze_failures()
        action_stats = await self.get_action_stats()

        successes = [e for e in entries if e.status == "success"]
        failures = [e for e in entries if e.status == "failure"]

        return LearningReport(
            total_actions=len(entries),
            success_count=len(successes),
            failure_count=len(failures),
            action_stats=action_stats,
            recommendations=recommendations,
        )

    async def get_improvement_summary(self) -> str:
        """
        Generate a human-readable improvement summary.

        Returns:
            Summary string.
        """
        report = await self.generate_report()

        lines = [
            "=== Self-Learning Summary ===",
            f"Total Actions: {report.total_actions}",
            f"Success Rate: {report.overall_success_rate:.1%}",
            "",
        ]

        if report.recommendations:
            lines.append("Top Recommendations:")
            for i, rec in enumerate(report.recommendations[:5], 1):
                lines.append(f"  {i}. {rec.action}: {rec.suggestion}")
                conf = f"{rec.confidence:.0%}"
                lines.append(f"     (Confidence: {conf}, Failures: {rec.failure_count})")
        else:
            lines.append("No recommendations - keep up the good work!")

        return "\n".join(lines)
