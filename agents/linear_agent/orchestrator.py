"""Vertex AI ADK-compatible orchestrator for the Mapache Linear agent."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .coding_agents import AgentConfig, load_coding_agents, select_coding_agent
from .classification import TicketClassifier
from .connectors import GitHubConnector, LinearConnector
from .models import ActionPlan, LeanTicket, PrioritizedTicket, RoutingDecision
from .models import Surface, TicketContext, TicketSize, TicketSource
from .prioritization import TicketPrioritizer
from .routing import RoutingDecider
from .shaping import LeanTicketShaper


@dataclass
class AgentTools:
    """ADK-style tool registration payload."""

    name: str
    description: str
    parameters: Dict[str, object]


class LinearProductAgent:
    """Implements the business rules outlined in :mod:`AgentSpec.md`."""

    def __init__(
        self,
        linear: LinearConnector,
        github: GitHubConnector,
        shaper: Optional[LeanTicketShaper] = None,
        classifier: Optional[TicketClassifier] = None,
        prioritizer: Optional[TicketPrioritizer] = None,
        router: Optional[RoutingDecider] = None,
        coding_agents: Optional[List[AgentConfig]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.linear = linear
        self.github = github
        self.shaper = shaper or LeanTicketShaper()
        self.classifier = classifier or TicketClassifier()
        self.prioritizer = prioritizer or TicketPrioritizer()
        self.router = router or RoutingDecider()
        self.coding_agents = coding_agents or load_coding_agents()
        self.logger = logger or logging.getLogger(__name__)

    def process_webhook(self, payload: dict, signature: Optional[str]) -> ActionPlan:
        """Validate webhook, shape ticket, classify, prioritize, and route."""

        if not self.linear.validate_webhook(payload, signature):
            raise ValueError("Invalid webhook signature")
        raw_ticket, context = self.linear.parse_ticket(payload)
        lean_ticket = self.shaper.shape(raw_ticket, context)
        classification = self.classifier.classify(lean_ticket, context)
        priority = self.prioritizer.score(classification, lean_ticket)
        routing = self.router.route(
            priority,
            status=context.status,
            select_agent=lambda prioritized: self._select_coding_agent(prioritized, context),
        )
        plan = self._build_plan(lean_ticket, priority, routing)
        self.logger.info("Built action plan", extra={"routing": routing.destination})
        return plan

    def _select_coding_agent(self, prioritized: PrioritizedTicket, context: TicketContext) -> Optional[str]:
        """Select and dispatch a coding agent for ready work, recording capacity usage."""

        job_id = context.issue_id or prioritized.lean_ticket.title
        agent = select_coding_agent(prioritized.classification, self.coding_agents, job_id=job_id)
        if agent:
            self.logger.info(
                "Dispatched coding agent", extra={"agent": agent.name, "job_id": job_id}
            )
            return agent.name
        self.logger.warning("No coding agent available for dispatch", extra={"job_id": job_id})
        return None

    def _build_plan(
        self, lean_ticket: LeanTicket, priority: PrioritizedTicket, routing: RoutingDecision
    ) -> ActionPlan:
        """Create a canonical action plan for downstream agents."""

        next_steps: List[str] = [
            f"Share Lean ticket with {routing.destination}",
            "Confirm scope and acceptance criteria with reporter" if not lean_ticket.is_crisp() else "Start implementation",
            "Link resulting PR to Linear issue via GitHub MCP",
        ]
        return ActionPlan(
            lean_ticket=lean_ticket,
            classification=priority.classification,
            priority=priority,
            routing=routing,
            next_steps=next_steps,
        )

    def tools(self) -> List[AgentTools]:
        """Expose ADK-compatible tool definitions for the coordinator."""

        return [
            AgentTools(
                name="process_linear_webhook",
                description="Validate and triage a Linear webhook payload into a Lean action plan.",
                parameters={
                    "payload": {"type": "object", "description": "Linear webhook payload"},
                    "signature": {
                        "type": ["string", "null"],
                        "description": "HMAC signature from Linear; optional when no secret configured.",
                    },
                },
            )
        ]
