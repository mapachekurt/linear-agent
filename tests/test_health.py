"""Tests for the health monitoring module."""

import pytest

from linear_agent.health import (
    HealthMonitor,
    HealthReport,
    HealthStatus,
    QuotaInfo,
    ServiceHealth,
)


class TestQuotaInfo:
    """Tests for QuotaInfo."""

    def test_usage_percent(self) -> None:
        """Test quota usage percentage calculation."""
        quota = QuotaInfo(remaining=800, limit=1000)
        assert quota.usage_percent == 20.0

    def test_usage_percent_none(self) -> None:
        """Test usage percent when values are None."""
        quota = QuotaInfo()
        assert quota.usage_percent is None

    def test_is_low_true(self) -> None:
        """Test low quota detection."""
        quota = QuotaInfo(remaining=100, limit=1000)  # 10% remaining
        assert quota.is_low is True

    def test_is_low_false(self) -> None:
        """Test non-low quota."""
        quota = QuotaInfo(remaining=500, limit=1000)  # 50% remaining
        assert quota.is_low is False

    def test_exhausted(self) -> None:
        """Test exhausted quota."""
        quota = QuotaInfo(remaining=0, limit=1000, exhausted=True)
        assert quota.exhausted is True


class TestServiceHealth:
    """Tests for ServiceHealth."""

    def test_default_values(self) -> None:
        """Test default service health values."""
        health = ServiceHealth(name="test")
        assert health.name == "test"
        assert health.status == HealthStatus.HEALTHY
        assert health.last_error is None


class TestHealthReport:
    """Tests for HealthReport."""

    def test_default_values(self) -> None:
        """Test default health report values."""
        report = HealthReport()
        assert report.overall_status == HealthStatus.HEALTHY
        assert report.is_healthy() is True

    def test_summary(self) -> None:
        """Test generating summary."""
        report = HealthReport()
        report.linear.quota.remaining = 100
        report.linear.quota.limit = 1000
        summary = report.summary()
        assert "Health Report" in summary
        assert "Linear Quota: 100/1000" in summary


class TestHealthMonitor:
    """Tests for HealthMonitor."""

    @pytest.fixture
    def monitor(self) -> HealthMonitor:
        """Create a health monitor instance."""
        return HealthMonitor()

    async def test_check_health(self, monitor: HealthMonitor) -> None:
        """Test health check."""
        report = await monitor.check_health()
        assert isinstance(report, HealthReport)
        assert report.overall_status == HealthStatus.HEALTHY

    async def test_update_linear_quota(self, monitor: HealthMonitor) -> None:
        """Test updating Linear quota."""
        # First do a health check to initialize the report
        await monitor.check_health()

        monitor.update_linear_quota(remaining=500, limit=1000)
        assert monitor.last_report is not None
        assert monitor.last_report.linear.quota.remaining == 500
        assert monitor.last_report.linear.quota.limit == 1000

    async def test_update_github_quota(self, monitor: HealthMonitor) -> None:
        """Test updating GitHub quota."""
        await monitor.check_health()

        monitor.update_github_quota(remaining=4000, limit=5000)
        assert monitor.last_report is not None
        assert monitor.last_report.github.quota.remaining == 4000

    async def test_record_linear_error(self, monitor: HealthMonitor) -> None:
        """Test recording Linear error."""
        await monitor.check_health()

        monitor.record_linear_error("Test error")
        assert monitor.last_report is not None
        assert monitor.last_report.linear.last_error == "Test error"
        assert monitor.last_report.linear.status == HealthStatus.DEGRADED

    async def test_record_github_error(self, monitor: HealthMonitor) -> None:
        """Test recording GitHub error."""
        await monitor.check_health()

        monitor.record_github_error("GitHub error")
        assert monitor.last_report is not None
        assert monitor.last_report.github.last_error == "GitHub error"
        assert monitor.last_report.github.status == HealthStatus.DEGRADED

    async def test_clear_errors(self, monitor: HealthMonitor) -> None:
        """Test clearing errors."""
        await monitor.check_health()

        monitor.record_linear_error("Error 1")
        monitor.record_github_error("Error 2")
        monitor.clear_errors()

        assert monitor.last_report is not None
        assert monitor.last_report.linear.last_error is None
        assert monitor.last_report.github.last_error is None
        assert monitor.last_report.overall_status == HealthStatus.HEALTHY

    def test_is_quota_exhausted_false(self, monitor: HealthMonitor) -> None:
        """Test quota exhausted check when not exhausted."""
        assert monitor.is_quota_exhausted() is False

    async def test_is_quota_exhausted_true(self, monitor: HealthMonitor) -> None:
        """Test quota exhausted check when exhausted."""
        await monitor.check_health()

        monitor.update_linear_quota(remaining=0, limit=1000)
        assert monitor.is_quota_exhausted() is True

    def test_get_status(self, monitor: HealthMonitor) -> None:
        """Test getting current status."""
        assert monitor.get_status() == HealthStatus.HEALTHY

    async def test_overall_status_unhealthy(self, monitor: HealthMonitor) -> None:
        """Test overall status becomes unhealthy."""
        await monitor.check_health()

        monitor.update_linear_quota(remaining=0, limit=1000)
        assert monitor.last_report is not None
        assert monitor.last_report.overall_status == HealthStatus.UNHEALTHY

    async def test_overall_status_degraded(self, monitor: HealthMonitor) -> None:
        """Test overall status becomes degraded."""
        await monitor.check_health()

        # Low quota (< 20%)
        monitor.update_linear_quota(remaining=50, limit=1000)
        assert monitor.last_report is not None
        assert monitor.last_report.overall_status == HealthStatus.DEGRADED
