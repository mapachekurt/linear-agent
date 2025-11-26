"""Integration surfaces for Linear and GitHub with MCP-friendly stubs."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional

from .models import TicketContext, TicketSource
from .shaping import RawTicket


class LinearConnector:
    """Minimal Linear connector used for shaping and validation."""

    def __init__(self, webhook_secret: Optional[str] = None) -> None:
        self.webhook_secret = webhook_secret

    def validate_webhook(self, payload: dict, signature: Optional[str]) -> bool:
        """Validate the webhook using HMAC if a secret is configured."""

        if not self.webhook_secret:
            return True
        if not signature:
            return False
        body = json.dumps(payload, separators=(",", ":")).encode()
        digest = hmac.new(self.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    def parse_ticket(self, payload: dict) -> tuple[RawTicket, TicketContext]:
        """Parse a Linear webhook payload into raw ticket and context."""

        issue = payload.get("data", {}).get("issue", {})
        title = issue.get("title", "Untitled")
        description = issue.get("description", "")
        status = issue.get("status") or payload.get("status")
        reporter = issue.get("creator", {}).get("name") or payload.get("user")
        owner = issue.get("assignee", {}).get("name")
        source = TicketSource.CUSTOMER if issue.get("priority") else TicketSource.INTERNAL
        issue_id = issue.get("id")
        context = TicketContext(
            source=source,
            surface_hint=None,
            size_hint=None,
            slack_thread=payload.get("slackThread"),
            reporter=reporter,
            status=status,
            issue_id=issue_id,
            raw_payload=payload,
        )
        return RawTicket(title=title, description=description, reporter=reporter, owner=owner), context


class GitHubConnector:
    """Placeholder connector to surface GitHub metadata for Copilot agents."""

    def __init__(self, default_repo: Optional[str] = None) -> None:
        self.default_repo = default_repo

    def build_summary_comment(self, plan) -> str:
        """Return a markdown comment summarizing the plan for PR reviewers."""

        steps = "\n".join(f"- {step}" for step in plan.next_steps)
        return (
            f"**Lean ticket:** {plan.lean_ticket.title}\n"
            f"**Routing:** {plan.routing.destination}\n"
            f"**Priority:** {plan.priority.priority_score}\n"
            f"**Next steps:**\n{steps}\n"
        )
