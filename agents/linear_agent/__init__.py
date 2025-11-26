"""
Linear Product Management Agent.

The product/backlog brain for Mapache that:
- Keeps Linear projects/issues lean and up to date
- Reflects the Mapache business model (solutions → app)
- Orchestrates execution routing to GitHub Copilot
- Acts as glue between Slack, Linear, and GitHub
"""

__version__ = "0.3.0"

from agents.linear_agent.config import AgentConfig
from agents.linear_agent.core import LinearAgentCore
from agents.linear_agent.models import (
    CopilotBrief,
    ExecutionRoute,
    IssueSize,
    IssueSource,
    IssueStatus,
    LeanTicket,
    ProductSurface,
    TriageResult,
)

__all__ = [
    "IssueSource",
    "ProductSurface",
    "IssueSize",
    "ExecutionRoute",
    "IssueStatus",
    "LeanTicket",
    "CopilotBrief",
    "TriageResult",
    "AgentConfig",
    "LinearAgentCore",
]
