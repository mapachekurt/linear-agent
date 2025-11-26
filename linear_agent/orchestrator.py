"""Primary orchestrator for the Linear agent."""
from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

from .config import AgentSettings
from .github_integration import GitHubIntegration
from .health import HealthMonitor
from .linear_client import LinearClient
from .logging_utils import LogContext, configure_logging, log_with_context
from .self_learning import SelfLearningRecorder


class AgentOrchestrator:
    """Coordinate Linear, GitHub, and self-learning workflows."""

    def __init__(
        self,
        settings: AgentSettings,
        linear_client: LinearClient,
        github: GitHubIntegration,
        learning: SelfLearningRecorder,
        health_monitor: Optional[HealthMonitor] = None,
        logger: Optional[logging.Logger] = None,
    ):
        settings.validate()
        self.settings = settings
        self.linear_client = linear_client
        self.github = github
        self.learning = learning
        self.health_monitor = health_monitor or HealthMonitor()
        self.logger = logger or configure_logging()

    def handle_webhook(self, payload: dict, signature: Optional[str]) -> dict:
        """Handle a Linear webhook payload and return a structured response."""

        valid = self.linear_client.validate_webhook_signature(signature, str(payload).encode())
        context = LogContext(correlation_id=payload.get("id"))
        if not valid:
            log_with_context(self.logger, logging.WARNING, "Invalid webhook signature", context)
            self.learning.record_failure("webhook_validation", {"payload": payload})
            return {"status": "rejected", "reason": "invalid signature"}

        event_type = payload.get("type")
        log_with_context(self.logger, logging.INFO, f"Processing webhook {event_type}", context)
        self.learning.record_success("webhook_received", {"type": event_type})
        return {"status": "accepted", "event": event_type}

    def create_issue_and_link_pr(
        self,
        team_id: str,
        title: str,
        description: str,
        repo: str,
        pull_number: int,
    ) -> Dict[str, str]:
        """Create a Linear issue and link it to the GitHub pull request."""

        health = self.health_monitor.consume_quota()
        if not health.healthy:
            self.learning.record_failure("quota_check", health.to_dict())
            return {"status": "unhealthy", "reason": health.reason}

        issue = self.linear_client.create_issue(team_id, title, description)
        context = LogContext(linear_issue_id=issue.id, github_repo=repo)
        log_with_context(self.logger, logging.INFO, "Created Linear issue", context)

        self.github.link_pull_request(repo, pull_number, issue.id)
        log_with_context(self.logger, logging.INFO, "Linked PR to Linear", context)
        self.learning.record_success("issue_linked", {"issue": issue.id, "pull": pull_number})
        return {"status": "linked", "issue": issue.id, "pull": pull_number}

    def generate_improvement_suggestions(self) -> Dict[str, object]:
        """Run self-learning to produce actionable recommendations."""

        suggestions = self.learning.emit_suggestions(self.logger, LogContext())
        return {"count": len(suggestions), "suggestions": suggestions}

    def rotation_needed(self) -> bool:
        """Determine whether the agent should rotate based on health."""

        status = self.health_monitor.status()
        if not status.healthy:
            self.learning.record_failure("rotation_trigger", status.to_dict())
        return not status.healthy

    def run_health_check(self) -> Dict[str, object]:
        """Return a health summary suitable for monitoring or alerting."""

        status = self.health_monitor.status()
        context = LogContext()
        level = logging.INFO if status.healthy else logging.WARNING
        log_with_context(self.logger, level, f"Health check: {status.reason}", context)
        return status.to_dict()

    def action_router(self) -> Dict[str, Callable[..., dict]]:
        """Expose available actions to any multi-agent coordinator."""

        return {
            "handle_webhook": self.handle_webhook,
            "create_issue_and_link_pr": self.create_issue_and_link_pr,
            "generate_improvement_suggestions": lambda: self.generate_improvement_suggestions(),
            "run_health_check": lambda: self.run_health_check(),
        }
