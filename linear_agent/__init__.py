"""
Linear Agent - Autonomous Linear agent for issue management.

This package provides tools for interacting with Linear's GraphQL API,
integrating with GitHub, and self-learning capabilities.
"""

__version__ = "0.1.0"

from linear_agent.client import LinearClient
from linear_agent.config import GitHubSettings, LinearSettings, StorageSettings
from linear_agent.github_client import GitHubClient
from linear_agent.health import HealthMonitor
from linear_agent.orchestrator import Orchestrator
from linear_agent.self_learning import SelfLearning
from linear_agent.storage import AuditStorage, StateStorage

__all__ = [
    "LinearSettings",
    "GitHubSettings",
    "StorageSettings",
    "LinearClient",
    "GitHubClient",
    "HealthMonitor",
    "SelfLearning",
    "AuditStorage",
    "StateStorage",
    "Orchestrator",
]
