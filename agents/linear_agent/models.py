"""
Data models for the Linear Product Management Agent.

Contains dataclasses for tickets, routes, surfaces, and agent outputs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueSource(str, Enum):
    """Source of a Linear issue."""

    USER = "source:user"  # Kurt created manually
    OPPORTUNITY_AGENT = "source:opportunity-agent"  # Created by Opportunity Agent
    SYSTEM_MIGRATION = "source:system-migration"  # Bulk/legacy imports


class ProductSurface(str, Enum):
    """Product surface classification."""

    SOLUTIONS = "surface:solutions"  # mapache.solutions web apps
    APP = "surface:app"  # mapache.app OS
    BRIDGE = "surface:bridge"  # Moving flows from .solutions → .app (MCP-GUI)


class IssueSize(str, Enum):
    """Size estimation for routing decisions."""

    SMALL = "size:small"  # Single-file or localized
    MEDIUM = "size:medium"  # Multi-component but straightforward
    LARGE = "size:large"  # Cross-cutting, multiple services, redesign


class ExecutionRoute(str, Enum):
    """Execution routing target."""

    COPILOT_AGENT = "route:copilot-agent"  # Large work, long-running sessions
    COPILOT_CHAT = "route:copilot-chat"  # Small/medium, focused sessions
    MANUAL = "route:manual"  # Strategy/architecture, ambiguous scope


class IssueStatus(str, Enum):
    """Issue lifecycle status."""

    CANDIDATE = "status:candidate"  # New, needs triage
    SHAPED = "status:shaped"  # Lean format, clear outcome
    READY = "status:ready"  # Ready for execution (has route)
    PARKED = "status:parked"  # Later / maybe never
    DISCARDED = "status:discarded"  # Intentionally dropped


@dataclass
class LeanTicket:
    """
    Standard Lean format for issue descriptions.

    The agent converts bloated tickets into this format.
    """

    problem: str  # Short, user-centered description
    desired_outcome: str  # What changes when done
    product_surfaces: list[ProductSurface] = field(default_factory=list)
    context_and_constraints: str = ""  # Links, repos, hard constraints
    execution_route_hint: str = ""  # Route with one-line rationale

    def to_markdown(self) -> str:
        """Convert to markdown format for Linear."""
        surfaces_str = ", ".join(s.value.replace("surface:", "") for s in self.product_surfaces)
        return f"""## Problem
{self.problem}

## Desired Outcome
{self.desired_outcome}

## Product Surface
{surfaces_str}

## Context & Constraints
{self.context_and_constraints}

## Execution Route Hint
{self.execution_route_hint}
"""


@dataclass
class CopilotBrief:
    """
    Machine-readable brief for GitHub Copilot coding agent.

    Used when routing to copilot-agent.
    """

    problem: str
    outcome: str
    constraints: list[str] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)
    suggested_steps: list[str] = field(default_factory=list)
    linear_issue_id: str | None = None
    linear_issue_url: str | None = None

    def to_prompt(self) -> str:
        """Generate a prompt for Copilot agent."""
        if self.constraints:
            constraints_str = "\n".join(f"- {c}" for c in self.constraints)
        else:
            constraints_str = "None"
        if self.repos:
            repos_str = "\n".join(f"- {r}" for r in self.repos)
        else:
            repos_str = "Not specified"
        if self.suggested_steps:
            steps_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.suggested_steps))
        else:
            steps_str = "Plan based on current codebase"

        return f"""# Task Brief

## Problem
{self.problem}

## Expected Outcome
{self.outcome}

## Repositories
{repos_str}

## Constraints
{constraints_str}

## Suggested Approach
{steps_str}

## References
- Linear Issue: {self.linear_issue_url or 'N/A'}
"""


@dataclass
class ChatPromptSnippet:
    """
    Prompt snippet for GitHub Copilot Chat.

    Used when routing to copilot-chat for small/medium work.
    """

    context: str
    problem: str
    constraints: str
    acceptance_criteria: str

    def to_prompt(self) -> str:
        """Generate a paste-able prompt for Copilot Chat."""
        return f"""Context: {self.context}

Problem: {self.problem}

Constraints: {self.constraints}

Acceptance Criteria: {self.acceptance_criteria}
"""


@dataclass
class TriageResult:
    """Result of triaging an issue."""

    issue_id: str
    original_title: str
    is_relevant: bool
    surfaces: list[ProductSurface] = field(default_factory=list)
    size: IssueSize | None = None
    route: ExecutionRoute | None = None
    status: IssueStatus = IssueStatus.CANDIDATE
    lean_ticket: LeanTicket | None = None
    priority_score: float = 0.0
    rationale: str = ""
    needs_human_review: bool = False


@dataclass
class PrioritizationResult:
    """Result of prioritizing an issue."""

    issue_id: str
    priority_score: float  # Higher = more important
    priority_rank: int | None = None  # P1, P2, P3, P4
    rationale: str = ""
    boosted: bool = False  # Was this boosted (e.g., bridge work)?
    demoted: bool = False  # Was this demoted (e.g., low-signal)?


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    issue_id: str
    route: ExecutionRoute
    rationale: str
    copilot_brief: CopilotBrief | None = None
    chat_snippet: ChatPromptSnippet | None = None


@dataclass
class SelfImprovementTicket:
    """
    Issue to log in Linear Agent – Improvements project.

    Created when the agent detects failures or misbehavior.
    """

    timestamp: str
    input_summary: str  # What input it saw
    decision_made: str  # What decision it made
    why_wrong: str  # Why it believes this was wrong
    suggested_adjustment: str  # Suggested rule adjustment
    severity: str = "low"  # low, medium, high
    original_issue_id: str | None = None

    def to_description(self) -> str:
        """Generate issue description for Linear."""
        return f"""## Self-Improvement Report

**Timestamp:** {self.timestamp}
**Severity:** {self.severity}
**Original Issue:** {self.original_issue_id or 'N/A'}

### Input Summary
{self.input_summary}

### Decision Made
{self.decision_made}

### Why This Was Wrong
{self.why_wrong}

### Suggested Adjustment
{self.suggested_adjustment}
"""


@dataclass
class LinearIssue:
    """Representation of a Linear issue."""

    id: str
    identifier: str  # e.g., "MAP-123"
    title: str
    description: str | None = None
    state: str | None = None
    priority: int | None = None
    labels: list[str] = field(default_factory=list)
    project_id: str | None = None
    url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LinearIssue":
        """Create from Linear API response."""
        return cls(
            id=data["id"],
            identifier=data.get("identifier", ""),
            title=data.get("title", ""),
            description=data.get("description"),
            state=data.get("state", {}).get("name") if data.get("state") else None,
            priority=data.get("priority"),
            labels=[
                lbl.get("name", "")
                for lbl in data.get("labels", {}).get("nodes", [])
            ],
            project_id=data.get("project", {}).get("id") if data.get("project") else None,
            url=data.get("url"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class LinearProject:
    """Representation of a Linear project."""

    id: str
    name: str
    description: str | None = None
    state: str | None = None
    url: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LinearProject":
        """Create from Linear API response."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description"),
            state=data.get("state"),
            url=data.get("url"),
        )
