"""Public interface for the Mapache Linear agent package."""
from .classification import TicketClassifier
from .coding_agents import AgentCapacity, AgentConfig, load_coding_agents, select_coding_agent
from .connectors import GitHubConnector, LinearConnector
from .orchestrator import AgentTools, LinearProductAgent
from .prioritization import TicketPrioritizer
from .routing import RoutingDecider
from .shaping import LeanTicketShaper
from .models import (
    ActionPlan,
    Classification,
    LeanTicket,
    PrioritizedTicket,
    RoutingDecision,
    Surface,
    TicketContext,
    TicketSize,
    TicketSource,
)

__all__ = [
    "ActionPlan",
    "AgentTools",
    "Classification",
    "GitHubConnector",
    "LeanTicket",
    "LeanTicketShaper",
    "LinearConnector",
    "LinearProductAgent",
    "AgentCapacity",
    "AgentConfig",
    "load_coding_agents",
    "select_coding_agent",
    "PrioritizedTicket",
    "RoutingDecision",
    "RoutingDecider",
    "Surface",
    "TicketClassifier",
    "TicketContext",
    "TicketPrioritizer",
    "TicketSize",
    "TicketSource",
]
