"""
Configuration module for Linear Agent.

This module provides dataclass-based configuration objects for
Linear API, GitHub API, and storage settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """Load environment variables from .env file if present."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


@dataclass
class BackoffPolicy:
    """Configuration for exponential backoff on rate limiting."""

    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    max_retries: int = 5

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = self.initial_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)


@dataclass
class LinearSettings:
    """Configuration for Linear API connection."""

    api_key: str = ""
    api_url: str = "https://api.linear.app/graphql"
    timeout: float = 30.0
    backoff: BackoffPolicy = field(default_factory=BackoffPolicy)

    @classmethod
    def from_env(cls) -> "LinearSettings":
        """Create settings from environment variables."""
        _load_env()
        return cls(
            api_key=os.getenv("LINEAR_API_KEY", ""),
            api_url=os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql"),
            timeout=float(os.getenv("LINEAR_TIMEOUT", "30.0")),
        )


@dataclass
class GitHubSettings:
    """Configuration for GitHub API connection."""

    api_key: str = ""
    api_url: str = "https://api.github.com"
    timeout: float = 30.0
    backoff: BackoffPolicy = field(default_factory=BackoffPolicy)

    @classmethod
    def from_env(cls) -> "GitHubSettings":
        """Create settings from environment variables."""
        _load_env()
        return cls(
            api_key=os.getenv("GITHUB_TOKEN", ""),
            api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
            timeout=float(os.getenv("GITHUB_TIMEOUT", "30.0")),
        )


@dataclass
class StorageSettings:
    """Configuration for persistent storage."""

    audit_log_path: Path = field(default_factory=lambda: Path("audit.jsonl"))
    state_file_path: Path = field(default_factory=lambda: Path("agent_state.json"))
    max_audit_entries: int = 10000

    @classmethod
    def from_env(cls) -> "StorageSettings":
        """Create settings from environment variables."""
        _load_env()
        return cls(
            audit_log_path=Path(os.getenv("AUDIT_LOG_PATH", "audit.jsonl")),
            state_file_path=Path(os.getenv("STATE_FILE_PATH", "agent_state.json")),
            max_audit_entries=int(os.getenv("MAX_AUDIT_ENTRIES", "10000")),
        )


@dataclass
class AgentConfig:
    """Complete agent configuration combining all settings."""

    linear: LinearSettings = field(default_factory=LinearSettings)
    github: GitHubSettings = field(default_factory=GitHubSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create complete configuration from environment variables."""
        return cls(
            linear=LinearSettings.from_env(),
            github=GitHubSettings.from_env(),
            storage=StorageSettings.from_env(),
        )
