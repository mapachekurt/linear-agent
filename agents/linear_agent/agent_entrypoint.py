"""Agent Engine entrypoint for the Mapache Linear Product Management Agent.

This module builds the ADK-compatible ``root_agent`` object that Vertex AI Agent
Engine expects. The tools exposed here wrap the orchestrator and coding-agent
selection logic described in ``AgentSpec.md``.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

try:  # Prefer the Vertex AI preview namespace when available
    from vertexai.preview import agentbuilder
except ImportError:  # pragma: no cover - fallback for alternate installation layouts
    from google.cloud.aiplatform import agentbuilder  # type: ignore

from .coding_agents import load_coding_agents, select_coding_agent
from .connectors import GitHubConnector, LinearConnector
from .orchestrator import LinearProductAgent
from .classification import TicketClassifier
from .prioritization import TicketPrioritizer
from .routing import RoutingDecider
from .shaping import LeanTicketShaper, RawTicket
from .models import TicketContext, TicketSource


# Shared components for tool executions
_linear_connector = LinearConnector()
_github_connector = GitHubConnector()
_coding_agents = load_coding_agents()
_product_agent = LinearProductAgent(
    linear=_linear_connector,
    github=_github_connector,
    coding_agents=_coding_agents,
)
_shaper = LeanTicketShaper()
_classifier = TicketClassifier()
_prioritizer = TicketPrioritizer()
_router = RoutingDecider()


@agentbuilder.tool
def process_linear_webhook(payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, Any]:
    """Validate and triage a Linear webhook payload into an action plan."""

    plan = _product_agent.process_webhook(payload=payload, signature=signature)
    return asdict(plan)


@agentbuilder.tool
def analyze_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Shape, classify, prioritize, and route a single issue payload."""

    raw = RawTicket(
        title=issue.get("title", "Untitled"),
        description=issue.get("description", ""),
        reporter=issue.get("reporter"),
        owner=issue.get("owner"),
    )
    context = TicketContext(
        source=TicketSource(issue.get("source") or TicketSource.INTERNAL),
        surface_hint=None,
        size_hint=None,
        status=issue.get("status"),
        issue_id=issue.get("issue_id"),
        raw_payload=issue,
    )
    lean = _shaper.shape(raw, context)
    classification = _classifier.classify(lean, context)
    prioritized = _prioritizer.score(classification, lean)
    routing = _router.route(
        prioritized,
        status=context.status,
        select_agent=lambda prioritized_ticket: _select_agent(prioritized_ticket, context),
    )
    return {
        "lean_ticket": asdict(lean),
        "classification": asdict(classification),
        "priority": asdict(prioritized),
        "routing": asdict(routing),
    }


def _select_agent(prioritized_ticket, context: TicketContext) -> Optional[str]:
    job_id = context.issue_id or prioritized_ticket.lean_ticket.title
    agent = select_coding_agent(prioritized_ticket.classification, _coding_agents, job_id=job_id)
    return agent.name if agent else None


root_agent = agentbuilder.LlmAgent(
    model="gemini-2.0-flash",
    tools=[process_linear_webhook, analyze_issue],
    instructions=(
        "You are the Mapache Linear Product Management Agent. Use Lean ticket shaping, "
        "surface classification (solutions, app, bridge), size estimation, and routing "
        "decisions that honor the Mapache funnel (.solutions -> .app). When a ticket is "
        "status:ready, select a Copilot coding agent when capacity allows."
    ),
)
"""
Exported object for Vertex AI Agent Engine.
entrypoint_module = "agents.linear_agent.agent_entrypoint"
entrypoint_object = "root_agent"
"""
