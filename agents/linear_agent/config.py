"""
Configuration for the Linear Product Management Agent.

All label names, project IDs, states come from this module.
Supports environment variables and GCP Secret Manager.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


def _load_env() -> None:
    """Load environment variables from .env file if present."""
    load_dotenv()


@dataclass
class LinearConfig:
    """Linear API configuration."""

    api_key: str = ""
    api_url: str = "https://api.linear.app/graphql"
    webhook_secret: str = ""
    timeout: float = 30.0

    # Project IDs
    improvements_project_id: str = ""  # "Linear Agent – Improvements" project

    # Workflow state mappings (Linear state names)
    state_candidate: str = "Backlog"
    state_shaped: str = "Todo"
    state_ready: str = "In Progress"
    state_parked: str = "Canceled"
    state_discarded: str = "Canceled"

    @classmethod
    def from_env(cls) -> "LinearConfig":
        """Create from environment variables."""
        _load_env()
        return cls(
            api_key=os.getenv("LINEAR_API_KEY", ""),
            api_url=os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql"),
            webhook_secret=os.getenv("LINEAR_WEBHOOK_SECRET", ""),
            timeout=float(os.getenv("LINEAR_TIMEOUT", "30.0")),
            improvements_project_id=os.getenv("LINEAR_IMPROVEMENTS_PROJECT_ID", ""),
            state_candidate=os.getenv("LINEAR_STATE_CANDIDATE", "Backlog"),
            state_shaped=os.getenv("LINEAR_STATE_SHAPED", "Todo"),
            state_ready=os.getenv("LINEAR_STATE_READY", "In Progress"),
            state_parked=os.getenv("LINEAR_STATE_PARKED", "Canceled"),
            state_discarded=os.getenv("LINEAR_STATE_DISCARDED", "Canceled"),
        )


@dataclass
class GitHubConfig:
    """GitHub API configuration."""

    token: str = ""
    api_url: str = "https://api.github.com"
    timeout: float = 30.0

    # Repo patterns for surface detection
    solutions_repo_pattern: str = "mapache-solutions-"
    app_repo_pattern: str = "mapache-app-"

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        """Create from environment variables."""
        _load_env()
        return cls(
            token=os.getenv("GITHUB_TOKEN", ""),
            api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
            timeout=float(os.getenv("GITHUB_TIMEOUT", "30.0")),
            solutions_repo_pattern=os.getenv("GITHUB_SOLUTIONS_PATTERN", "mapache-solutions-"),
            app_repo_pattern=os.getenv("GITHUB_APP_PATTERN", "mapache-app-"),
        )


@dataclass
class LabelConfig:
    """Label name configuration - all configurable."""

    # Source labels
    source_user: str = "source:user"
    source_opportunity_agent: str = "source:opportunity-agent"
    source_system_migration: str = "source:system-migration"

    # Surface labels
    surface_solutions: str = "surface:solutions"
    surface_app: str = "surface:app"
    surface_bridge: str = "surface:bridge"

    # Size labels
    size_small: str = "size:small"
    size_medium: str = "size:medium"
    size_large: str = "size:large"

    # Route labels
    route_copilot_agent: str = "route:copilot-agent"
    route_copilot_chat: str = "route:copilot-chat"
    route_manual: str = "route:manual"

    # Status labels (if using labels instead of workflow states)
    status_candidate: str = "status:candidate"
    status_shaped: str = "status:shaped"
    status_ready: str = "status:ready"
    status_parked: str = "status:parked"
    status_discarded: str = "status:discarded"

    @classmethod
    def from_env(cls) -> "LabelConfig":
        """Create from environment variables."""
        _load_env()
        opp_agent_label = os.getenv("LABEL_SOURCE_OPP_AGENT", "source:opportunity-agent")
        migration_label = os.getenv("LABEL_SOURCE_MIGRATION", "source:system-migration")
        return cls(
            source_user=os.getenv("LABEL_SOURCE_USER", "source:user"),
            source_opportunity_agent=opp_agent_label,
            source_system_migration=migration_label,
            surface_solutions=os.getenv("LABEL_SURFACE_SOLUTIONS", "surface:solutions"),
            surface_app=os.getenv("LABEL_SURFACE_APP", "surface:app"),
            surface_bridge=os.getenv("LABEL_SURFACE_BRIDGE", "surface:bridge"),
            size_small=os.getenv("LABEL_SIZE_SMALL", "size:small"),
            size_medium=os.getenv("LABEL_SIZE_MEDIUM", "size:medium"),
            size_large=os.getenv("LABEL_SIZE_LARGE", "size:large"),
            route_copilot_agent=os.getenv("LABEL_ROUTE_AGENT", "route:copilot-agent"),
            route_copilot_chat=os.getenv("LABEL_ROUTE_CHAT", "route:copilot-chat"),
            route_manual=os.getenv("LABEL_ROUTE_MANUAL", "route:manual"),
        )


@dataclass
class ClassificationKeywords:
    """Keywords for automatic classification."""

    # Keywords that suggest mapache.solutions
    solutions_keywords: list[str] = field(default_factory=lambda: [
        "solutions", "saas", "web app", "webapp", "dashboard",
        "forms", "tables", "crud", "micro-saas", "experiment",
    ])

    # Keywords that suggest mapache.app
    app_keywords: list[str] = field(default_factory=lambda: [
        "mapache.app", "conversational", "chat", "os", "mcp-gui",
        "business os", "smb", "operator",
    ])

    # Keywords that suggest bridge work
    bridge_keywords: list[str] = field(default_factory=lambda: [
        "bridge", "migrate", "mirror", "mcp-gui", "repurpose",
        "extract", "move to app", "promote", "consolidate",
    ])

    # Keywords that suggest large work
    large_work_keywords: list[str] = field(default_factory=lambda: [
        "refactor", "redesign", "architecture", "cross-cutting",
        "multiple services", "multi-repo", "breaking change",
    ])

    # Keywords that suggest small work
    small_work_keywords: list[str] = field(default_factory=lambda: [
        "fix", "typo", "single file", "localized", "quick",
        "minor", "tweak", "adjust",
    ])


@dataclass
class PrioritizationWeights:
    """Weights for prioritization scoring."""

    # Boost factors
    bridge_boost: float = 2.0  # Bridge work gets 2x priority
    opportunity_agent_boost: float = 1.5  # Good opportunity ideas
    app_boost: float = 1.3  # Direct app work

    # Demote factors
    stale_demote: float = 0.5  # Stale experiments
    maintenance_demote: float = 0.7  # Pure maintenance
    speculative_demote: float = 0.3  # Speculative ideas

    # Days thresholds
    stale_days_threshold: int = 30  # Issues older than this without updates


@dataclass
class AgentConfig:
    """Complete agent configuration."""

    linear: LinearConfig = field(default_factory=LinearConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    labels: LabelConfig = field(default_factory=LabelConfig)
    keywords: ClassificationKeywords = field(default_factory=ClassificationKeywords)
    weights: PrioritizationWeights = field(default_factory=PrioritizationWeights)

    # Agent behavior
    auto_leanify: bool = True
    auto_route: bool = True
    notify_on_severe_failure: bool = True
    log_improvements: bool = True

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create complete configuration from environment."""
        _load_env()
        return cls(
            linear=LinearConfig.from_env(),
            github=GitHubConfig.from_env(),
            labels=LabelConfig.from_env(),
            keywords=ClassificationKeywords(),
            weights=PrioritizationWeights(),
            auto_leanify=os.getenv("AGENT_AUTO_LEANIFY", "true").lower() == "true",
            auto_route=os.getenv("AGENT_AUTO_ROUTE", "true").lower() == "true",
            notify_on_severe_failure=os.getenv("AGENT_NOTIFY_FAILURES", "true").lower() == "true",
            log_improvements=os.getenv("AGENT_LOG_IMPROVEMENTS", "true").lower() == "true",
        )
