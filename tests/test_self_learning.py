"""Tests for the self-learning module."""

from pathlib import Path

import pytest

from linear_agent.self_learning import (
    ActionStats,
    LearningReport,
    Recommendation,
    SelfLearning,
)
from linear_agent.storage import AuditStorage


class TestRecommendation:
    """Tests for Recommendation dataclass."""

    def test_create(self) -> None:
        """Test creating a recommendation."""
        rec = Recommendation(
            action="create_issue",
            suggestion="Implement longer backoff",
            confidence=0.8,
            failure_count=10,
            examples=["rate limit exceeded"],
        )
        assert rec.action == "create_issue"
        assert rec.confidence == 0.8
        assert len(rec.examples) == 1


class TestActionStats:
    """Tests for ActionStats dataclass."""

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        stats = ActionStats(
            action="test",
            total_count=100,
            success_count=80,
            failure_count=20,
        )
        assert stats.success_rate == 0.8

    def test_success_rate_zero(self) -> None:
        """Test success rate with zero actions."""
        stats = ActionStats(action="test")
        assert stats.success_rate == 0.0


class TestLearningReport:
    """Tests for LearningReport dataclass."""

    def test_overall_success_rate(self) -> None:
        """Test overall success rate calculation."""
        report = LearningReport(
            total_actions=100,
            success_count=90,
            failure_count=10,
        )
        assert report.overall_success_rate == 0.9

    def test_overall_success_rate_zero(self) -> None:
        """Test success rate with zero actions."""
        report = LearningReport()
        assert report.overall_success_rate == 0.0


class TestSelfLearning:
    """Tests for SelfLearning."""

    @pytest.fixture
    def audit_file(self, tmp_path: Path) -> Path:
        """Create a temporary audit file path."""
        return tmp_path / "test_audit.jsonl"

    @pytest.fixture
    def audit_storage(self, audit_file: Path) -> AuditStorage:
        """Create an AuditStorage instance."""
        return AuditStorage(audit_file)

    @pytest.fixture
    def learning(self, audit_storage: AuditStorage) -> SelfLearning:
        """Create a SelfLearning instance."""
        return SelfLearning(audit_storage)

    async def test_record_success(self, learning: SelfLearning) -> None:
        """Test recording a successful action."""
        entry = await learning.record_success("test_action", {"key": "value"})
        assert entry.action == "test_action"
        assert entry.status == "success"
        assert entry.details == {"key": "value"}

    async def test_record_failure(self, learning: SelfLearning) -> None:
        """Test recording a failed action."""
        entry = await learning.record_failure(
            "test_action",
            "Rate limit exceeded",
            {"context": "info"},
        )
        assert entry.action == "test_action"
        assert entry.status == "failure"
        assert entry.error == "Rate limit exceeded"
        assert entry.suggestion is not None
        # Should match "rate limit" pattern
        assert "backoff" in entry.suggestion.lower() or "frequency" in entry.suggestion.lower()

    async def test_generate_suggestion_rate_limit(self, learning: SelfLearning) -> None:
        """Test suggestion for rate limit errors."""
        suggestion = learning._generate_suggestion("Rate limit exceeded")
        assert "backoff" in suggestion.lower() or "frequency" in suggestion.lower()

    async def test_generate_suggestion_not_found(self, learning: SelfLearning) -> None:
        """Test suggestion for not found errors."""
        suggestion = learning._generate_suggestion("Resource not found")
        assert "verify" in suggestion.lower() or "id" in suggestion.lower()

    async def test_generate_suggestion_unauthorized(self, learning: SelfLearning) -> None:
        """Test suggestion for unauthorized errors."""
        suggestion = learning._generate_suggestion("Unauthorized access")
        assert "api key" in suggestion.lower() or "permission" in suggestion.lower()

    async def test_generate_suggestion_unknown(self, learning: SelfLearning) -> None:
        """Test suggestion for unknown errors."""
        suggestion = learning._generate_suggestion("Some weird error")
        assert "error" in suggestion.lower()

    async def test_analyze_failures_empty(self, learning: SelfLearning) -> None:
        """Test analyzing with no failures."""
        recommendations = await learning.analyze_failures()
        assert recommendations == []

    async def test_analyze_failures(self, learning: SelfLearning) -> None:
        """Test analyzing failure patterns."""
        # Record multiple failures with the same pattern
        for i in range(5):
            await learning.record_failure(
                "create_issue",
                f"Rate limit exceeded (attempt {i})",
            )

        recommendations = await learning.analyze_failures()
        assert len(recommendations) > 0
        assert recommendations[0].action == "create_issue"
        assert recommendations[0].failure_count == 5

    async def test_get_action_stats(self, learning: SelfLearning) -> None:
        """Test getting action statistics."""
        await learning.record_success("action1")
        await learning.record_success("action1")
        await learning.record_failure("action1", "error")
        await learning.record_success("action2")

        stats = await learning.get_action_stats()
        assert len(stats) == 2

        action1_stats = next(s for s in stats if s.action == "action1")
        assert action1_stats.total_count == 3
        assert action1_stats.success_count == 2
        assert action1_stats.failure_count == 1

    async def test_generate_report(self, learning: SelfLearning) -> None:
        """Test generating a learning report."""
        await learning.record_success("action1")
        await learning.record_failure("action1", "Rate limit exceeded")

        report = await learning.generate_report()
        assert report.total_actions == 2
        assert report.success_count == 1
        assert report.failure_count == 1
        assert len(report.action_stats) == 1

    async def test_get_improvement_summary(self, learning: SelfLearning) -> None:
        """Test getting improvement summary."""
        await learning.record_success("action1")
        await learning.record_failure("action2", "Rate limit exceeded")

        summary = await learning.get_improvement_summary()
        assert "Self-Learning Summary" in summary
        assert "Total Actions: 2" in summary
