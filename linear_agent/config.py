"""Configuration models for the Linear agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional


@dataclass
class BackoffPolicy:
    """Configuration for exponential backoff when calling external services."""

    base_delay: float = 0.5
    multiplier: float = 2.0
    max_delay: float = 30.0
    jitter: float = 0.2

    def to_durations(self) -> tuple[timedelta, timedelta]:
        """Return base and maximum delays as :class:`datetime.timedelta` values."""

        return timedelta(seconds=self.base_delay), timedelta(seconds=self.max_delay)


@dataclass
class LinearSettings:
    """Credentials and options for talking to Linear."""

    api_key: str
    api_url: str = "https://api.linear.app/graphql"
    webhook_secret: Optional[str] = None
    backoff: BackoffPolicy = field(default_factory=BackoffPolicy)


@dataclass
class GitHubSettings:
    """Settings for GitHub communication."""

    token: str
    api_url: str = "https://api.github.com"
    default_repo: Optional[str] = None
    backoff: BackoffPolicy = field(default_factory=BackoffPolicy)


@dataclass
class StorageSettings:
    """Paths and thresholds for local storage used by the agent."""

    audit_log_path: str = "./data/audit_log.jsonl"
    state_path: str = "./data/agent_state.json"
    rotate_after: int = 10_000


@dataclass
class AgentSettings:
    """Root settings bundle for the agent."""

    linear: LinearSettings
    github: GitHubSettings
    storage: StorageSettings = field(default_factory=StorageSettings)
    workspace_notification_channel: Optional[str] = None

    def validate(self) -> None:
        """Validate that required fields are present.

        Raises:
            ValueError: If mandatory configuration is missing.
        """

        if not self.linear.api_key:
            raise ValueError("Linear API key is required")
        if not self.github.token:
            raise ValueError("GitHub token is required")
