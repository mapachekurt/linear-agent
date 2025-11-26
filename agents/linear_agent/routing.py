"""Routing decisions for the Mapache Linear agent."""
from __future__ import annotations

from typing import Callable, Optional

from .models import PrioritizedTicket, RoutingDecision


class RoutingDecider:
    """Decide whether to send work to Copilot agents, Copilot chat, or manual review."""

    def route(
        self,
        prioritized: PrioritizedTicket,
        status: str | None = None,
        select_agent: Optional[Callable[[PrioritizedTicket], Optional[str]]] = None,
    ) -> RoutingDecision:
        """Return a routing decision based on size, clarity, and agent capacity."""

        lean = prioritized.lean_ticket
        size = prioritized.classification.size.value
        destination: str
        confidence: float
        rationale: str

        if lean.is_crisp() and size == "s":
            destination = "route:copilot-agent"
            confidence = 0.9
            rationale = "Crisp problem with small scope suits autonomous coding agent."
        elif size == "l" or not lean.is_crisp():
            destination = "route:manual"
            confidence = 0.75
            rationale = "Large or ambiguous scope requires manual shaping."
        else:
            destination = "route:copilot-chat"
            confidence = 0.8
            rationale = "Medium work benefits from conversational refinement with Copilot chat."

        selected_agent = None
        if status and status.lower() == "ready" and destination == "route:copilot-agent" and select_agent:
            selected_agent = select_agent(prioritized)
            if selected_agent is None:
                destination = "route:manual"
                confidence = 0.5
                rationale = "No coding agent capacity available; falling back to manual triage."

        return RoutingDecision(
            destination=destination,
            confidence=confidence,
            rationale=rationale,
            selected_agent=selected_agent,
        )
