"""Agent Engine entrypoint for the Mapache Linear Product Management Agent.

This module builds the ADK-compatible ``root_agent`` object that Vertex AI Agent
Engine expects. The tools exposed here wrap the orchestrator, core routing
helpers, and coding-agent selection logic described in ``AgentSpec.md``.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

try:  # Prefer the Vertex AI preview namespace when available
    from vertexai.preview import agentbuilder
except ImportError:  # pragma: no cover - fallback for alternate installation layouts
    from google.cloud.aiplatform import agentbuilder  # type: ignore

from .coding_agents import load_coding_agents
from .connectors import GitHubConnector, LinearConnector
from .core import Issue, classify_surfaces, choose_route, estimate_size, prioritize_issue
from .orchestrator import LinearProductAgent
from .shaping import RawTicket
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
    plan = _product_agent.analyze_ticket(raw, context)
    return {
        "lean_ticket": asdict(plan.lean_ticket),
        "classification": asdict(plan.classification),
        "priority": asdict(plan.priority),
        "routing": asdict(plan.routing),
    }


@agentbuilder.tool
def route_core_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Expose the lightweight core helpers for routing and sizing."""

    core_issue = Issue(
        title=issue.get("title", "Untitled"),
        description=issue.get("description", ""),
        labels=issue.get("labels", []) or [],
        source=issue.get("source"),
        linked_repos=issue.get("linked_repos", []),
        metadata=issue.get("metadata", {}) or {},
    )
    surfaces = classify_surfaces(core_issue)
    size = estimate_size(core_issue)
    route = choose_route(core_issue)
    priority = prioritize_issue(core_issue, context={})
    return {"surfaces": sorted(surfaces), "size": size, "route": route, "priority": priority}


root_agent = agentbuilder.LlmAgent(
    model="gemini-2.0-flash",
    tools=[process_linear_webhook, analyze_issue, route_core_issue],
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
