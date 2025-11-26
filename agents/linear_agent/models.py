"""Domain models for the Mapache Linear agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional


class Surface(str, Enum):
    """Product surface associated with a ticket."""

    SOLUTIONS = "solutions"
    APP = "app"
    BRIDGE = "bridge"


class TicketSize(str, Enum):
    """Relative size estimate for a ticket."""

    SMALL = "s"
    MEDIUM = "m"
    LARGE = "l"


class TicketSource(str, Enum):
    """Origin of the ticket information."""

    CUSTOMER = "customer"
    INTERNAL = "internal"
    MARKET = "market"


@dataclass
class LeanTicket:
    """Normalized Lean ticket representation for downstream agents."""

    title: str
    problem: str
    impact: str
    scope: str
    acceptance_criteria: List[str] = field(default_factory=list)
    owner: Optional[str] = None

    def is_crisp(self) -> bool:
        """Return whether the ticket has enough shape for automation."""

        return bool(self.problem.strip() and self.impact.strip() and self.acceptance_criteria)


@dataclass
class TicketContext:
    """Additional context captured from Linear or Slack inputs."""

    source: TicketSource
    surface_hint: Optional[Surface] = None
    size_hint: Optional[TicketSize] = None
    slack_thread: Optional[str] = None
    reporter: Optional[str] = None
    status: Optional[str] = None
    issue_id: Optional[str] = None
    raw_payload: dict | None = None


@dataclass
class Classification:
    """Classification of a ticket."""

    surface: Surface
    size: TicketSize
    source: TicketSource
    confidence: float


@dataclass
class PrioritizedTicket:
    """Priority record for a classified ticket."""

    classification: Classification
    lean_ticket: LeanTicket
    priority_score: float
    rationale: str


@dataclass
class RoutingDecision:
    """Routing output for the coordinator."""

    destination: str
    confidence: float
    rationale: str
    selected_agent: Optional[str] = None


@dataclass
class ActionPlan:
    """Complete decision bundle for a ticket."""

    lean_ticket: LeanTicket
    classification: Classification
    priority: PrioritizedTicket
    routing: RoutingDecision
    next_steps: List[str]


def acceptance_from_lines(description: str) -> List[str]:
    """Extract acceptance criteria from a markdown-like description."""

    criteria: List[str] = []
    for line in description.splitlines():
        stripped = line.strip("- ")
        if not stripped:
            continue
        if stripped.lower().startswith("acceptance"):
            continue
        if line.strip().startswith(('*', '-', '+')):
            criteria.append(stripped)
    return criteria


def normalize_acceptance(raw: Iterable[str]) -> List[str]:
    """Normalize and deduplicate acceptance criteria strings."""

    seen: set[str] = set()
    results: List[str] = []
    for item in raw:
        normalized = item.strip()
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        results.append(normalized)
    return results
