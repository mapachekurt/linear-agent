"""Agent health monitoring and rotation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class HealthStatus:
    """State representing agent health and quotas."""

    healthy: bool
    reason: str
    remaining_quota: int

    def to_dict(self) -> Dict[str, object]:
        return {"healthy": self.healthy, "reason": self.reason, "remaining_quota": self.remaining_quota}


class HealthMonitor:
    """Simple quota-based health monitor."""

    def __init__(self, quota_limit: int = 1_000):
        self.quota_limit = quota_limit
        self.quota_remaining = quota_limit

    def consume_quota(self, amount: int = 1) -> HealthStatus:
        self.quota_remaining = max(0, self.quota_remaining - amount)
        return self.status()

    def status(self) -> HealthStatus:
        healthy = self.quota_remaining > 0
        reason = "Within quota" if healthy else "Quota exhausted"
        return HealthStatus(healthy=healthy, reason=reason, remaining_quota=self.quota_remaining)
