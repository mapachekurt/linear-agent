"""
Health monitoring module for Linear Agent.

This module provides health monitoring capabilities including
API quota tracking, status reporting, and health checks.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from linear_agent.client import LinearClient
from linear_agent.github_client import GitHubClient

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class QuotaInfo:
    """Information about API quota."""

    remaining: int | None = None
    limit: int | None = None
    exhausted: bool = False

    @property
    def usage_percent(self) -> float | None:
        """Calculate quota usage percentage."""
        if self.limit and self.limit > 0 and self.remaining is not None:
            return ((self.limit - self.remaining) / self.limit) * 100
        return None

    @property
    def is_low(self) -> bool:
        """Check if quota is running low (below 20%)."""
        if self.remaining is not None and self.limit:
            return self.remaining < (self.limit * 0.2)
        return False


@dataclass
class ServiceHealth:
    """Health status for a single service."""

    name: str
    status: HealthStatus = HealthStatus.HEALTHY
    quota: QuotaInfo = field(default_factory=QuotaInfo)
    last_check: str | None = None
    last_error: str | None = None


@dataclass
class HealthReport:
    """Complete health report for the agent."""

    overall_status: HealthStatus = HealthStatus.HEALTHY
    linear: ServiceHealth = field(default_factory=lambda: ServiceHealth(name="linear"))
    github: ServiceHealth = field(default_factory=lambda: ServiceHealth(name="github"))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, str] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """Check if the agent is healthy."""
        return self.overall_status == HealthStatus.HEALTHY

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"Health Report ({self.timestamp})",
            f"Overall Status: {self.overall_status.value}",
            f"Linear: {self.linear.status.value}",
            f"GitHub: {self.github.status.value}",
        ]
        if self.linear.quota.remaining is not None:
            lines.append(f"  Linear Quota: {self.linear.quota.remaining}/{self.linear.quota.limit}")
        if self.github.quota.remaining is not None:
            lines.append(f"  GitHub Quota: {self.github.quota.remaining}/{self.github.quota.limit}")
        return "\n".join(lines)


class HealthMonitor:
    """Health monitoring for the Linear Agent."""

    def __init__(
        self,
        linear_client: LinearClient | None = None,
        github_client: GitHubClient | None = None,
    ):
        """
        Initialize the health monitor.

        Args:
            linear_client: Optional Linear client instance.
            github_client: Optional GitHub client instance.
        """
        self._linear_client = linear_client
        self._github_client = github_client
        self._last_report: HealthReport | None = None

    @property
    def last_report(self) -> HealthReport | None:
        """Get the last health report."""
        return self._last_report

    def update_linear_quota(
        self,
        remaining: int | None,
        limit: int | None,
    ) -> None:
        """
        Update Linear API quota information.

        Args:
            remaining: Remaining quota.
            limit: Quota limit.
        """
        if self._last_report:
            self._last_report.linear.quota.remaining = remaining
            self._last_report.linear.quota.limit = limit
            is_exhausted = remaining == 0 if remaining is not None else False
            self._last_report.linear.quota.exhausted = is_exhausted
            self._check_overall_status()

    def update_github_quota(
        self,
        remaining: int | None,
        limit: int | None,
    ) -> None:
        """
        Update GitHub API quota information.

        Args:
            remaining: Remaining quota.
            limit: Quota limit.
        """
        if self._last_report:
            self._last_report.github.quota.remaining = remaining
            self._last_report.github.quota.limit = limit
            is_exhausted = remaining == 0 if remaining is not None else False
            self._last_report.github.quota.exhausted = is_exhausted
            self._check_overall_status()

    def record_linear_error(self, error: str) -> None:
        """
        Record a Linear API error.

        Args:
            error: Error message.
        """
        if self._last_report:
            self._last_report.linear.last_error = error
            self._last_report.linear.status = HealthStatus.DEGRADED
            self._check_overall_status()

    def record_github_error(self, error: str) -> None:
        """
        Record a GitHub API error.

        Args:
            error: Error message.
        """
        if self._last_report:
            self._last_report.github.last_error = error
            self._last_report.github.status = HealthStatus.DEGRADED
            self._check_overall_status()

    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        if self._last_report:
            self._last_report.linear.last_error = None
            self._last_report.linear.status = HealthStatus.HEALTHY
            self._last_report.github.last_error = None
            self._last_report.github.status = HealthStatus.HEALTHY
            self._check_overall_status()

    def _check_overall_status(self) -> None:
        """Update the overall status based on service statuses."""
        if not self._last_report:
            return

        # Check for unhealthy conditions
        if (
            self._last_report.linear.quota.exhausted
            or self._last_report.github.quota.exhausted
        ):
            self._last_report.overall_status = HealthStatus.UNHEALTHY
            return

        # Check for degraded conditions
        if (
            self._last_report.linear.status == HealthStatus.DEGRADED
            or self._last_report.github.status == HealthStatus.DEGRADED
            or self._last_report.linear.quota.is_low
            or self._last_report.github.quota.is_low
        ):
            self._last_report.overall_status = HealthStatus.DEGRADED
            return

        self._last_report.overall_status = HealthStatus.HEALTHY

    async def check_health(self) -> HealthReport:
        """
        Perform a complete health check.

        Returns:
            The health report.
        """
        report = HealthReport()
        now = datetime.now(timezone.utc).isoformat()

        # Check Linear health
        if self._linear_client:
            try:
                # Update quota from client's last known values
                report.linear.quota.remaining = self._linear_client.rate_limit_remaining
                report.linear.quota.limit = self._linear_client.rate_limit_limit
                report.linear.quota.exhausted = (
                    report.linear.quota.remaining == 0
                    if report.linear.quota.remaining is not None
                    else False
                )
                report.linear.last_check = now

                if report.linear.quota.exhausted:
                    report.linear.status = HealthStatus.UNHEALTHY
                elif report.linear.quota.is_low:
                    report.linear.status = HealthStatus.DEGRADED
                else:
                    report.linear.status = HealthStatus.HEALTHY

            except Exception as e:
                logger.error(f"Linear health check failed: {e}")
                report.linear.status = HealthStatus.UNHEALTHY
                report.linear.last_error = str(e)

        # Check GitHub health
        if self._github_client:
            try:
                report.github.quota.remaining = self._github_client.rate_limit_remaining
                report.github.quota.limit = self._github_client.rate_limit_limit
                report.github.quota.exhausted = (
                    report.github.quota.remaining == 0
                    if report.github.quota.remaining is not None
                    else False
                )
                report.github.last_check = now

                if report.github.quota.exhausted:
                    report.github.status = HealthStatus.UNHEALTHY
                elif report.github.quota.is_low:
                    report.github.status = HealthStatus.DEGRADED
                else:
                    report.github.status = HealthStatus.HEALTHY

            except Exception as e:
                logger.error(f"GitHub health check failed: {e}")
                report.github.status = HealthStatus.UNHEALTHY
                report.github.last_error = str(e)

        # Determine overall status
        if (
            report.linear.status == HealthStatus.UNHEALTHY
            or report.github.status == HealthStatus.UNHEALTHY
        ):
            report.overall_status = HealthStatus.UNHEALTHY
        elif (
            report.linear.status == HealthStatus.DEGRADED
            or report.github.status == HealthStatus.DEGRADED
        ):
            report.overall_status = HealthStatus.DEGRADED
        else:
            report.overall_status = HealthStatus.HEALTHY

        self._last_report = report
        logger.info(f"Health check completed: {report.overall_status.value}")
        return report

    def is_quota_exhausted(self) -> bool:
        """
        Check if any API quota is exhausted.

        Returns:
            True if any quota is exhausted.
        """
        if not self._last_report:
            return False
        return (
            self._last_report.linear.quota.exhausted
            or self._last_report.github.quota.exhausted
        )

    def get_status(self) -> HealthStatus:
        """
        Get the current health status.

        Returns:
            Current health status.
        """
        if self._last_report:
            return self._last_report.overall_status
        return HealthStatus.HEALTHY
