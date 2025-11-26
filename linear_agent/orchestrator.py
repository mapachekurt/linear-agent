"""
Orchestrator module for Linear Agent.

This module coordinates all agent components including
the Linear client, GitHub client, health monitor, and self-learning.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from linear_agent.client import (
    Attachment,
    Comment,
    Issue,
    LinearClient,
    LinearClientError,
    RateLimitError,
    Team,
)
from linear_agent.config import AgentConfig
from linear_agent.github_client import GitHubClient, GitHubClientError, PullRequest
from linear_agent.health import HealthMonitor, HealthReport, HealthStatus
from linear_agent.self_learning import LearningReport, SelfLearning
from linear_agent.storage import AgentState, AuditStorage, StateStorage

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator for the Linear Agent.

    Coordinates all components and provides a unified interface
    for agent operations.
    """

    def __init__(self, config: AgentConfig | None = None):
        """
        Initialize the orchestrator.

        Args:
            config: Agent configuration. If not provided, loads from environment.
        """
        self.config = config or AgentConfig.from_env()
        self._linear_client: LinearClient | None = None
        self._github_client: GitHubClient | None = None
        self._health_monitor: HealthMonitor | None = None
        self._self_learning: SelfLearning | None = None
        self._audit_storage: AuditStorage | None = None
        self._state_storage: StateStorage | None = None
        self._initialized = False

    async def __aenter__(self) -> "Orchestrator":
        """Enter async context and initialize all components."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context and cleanup."""
        await self.shutdown()

    async def initialize(self) -> None:
        """Initialize all agent components."""
        if self._initialized:
            return

        # Initialize storage
        self._audit_storage = AuditStorage(
            self.config.storage.audit_log_path,
            self.config.storage.max_audit_entries,
        )
        self._state_storage = StateStorage(self.config.storage.state_file_path)

        # Initialize self-learning
        self._self_learning = SelfLearning(self._audit_storage)

        # Initialize clients
        self._linear_client = LinearClient(self.config.linear)
        await self._linear_client.__aenter__()

        self._github_client = GitHubClient(self.config.github)
        await self._github_client.__aenter__()

        # Initialize health monitor
        self._health_monitor = HealthMonitor(
            self._linear_client,
            self._github_client,
        )

        self._initialized = True
        logger.info("Orchestrator initialized")

        # Record successful initialization
        await self._self_learning.record_success(
            "orchestrator.initialize",
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )

    async def shutdown(self) -> None:
        """Shutdown all agent components."""
        if not self._initialized:
            return

        if self._linear_client:
            await self._linear_client.__aexit__(None, None, None)
        if self._github_client:
            await self._github_client.__aexit__(None, None, None)

        self._initialized = False
        logger.info("Orchestrator shutdown")

    def _ensure_initialized(self) -> None:
        """Ensure the orchestrator is initialized."""
        if not self._initialized:
            msg = "Orchestrator not initialized. Use 'async with' or call initialize()"
            raise RuntimeError(msg)

    async def _update_health_from_linear(self) -> None:
        """Update health monitor with Linear client quota info."""
        if self._health_monitor and self._linear_client:
            self._health_monitor.update_linear_quota(
                self._linear_client.rate_limit_remaining,
                self._linear_client.rate_limit_limit,
            )

    async def _update_health_from_github(self) -> None:
        """Update health monitor with GitHub client quota info."""
        if self._health_monitor and self._github_client:
            self._health_monitor.update_github_quota(
                self._github_client.rate_limit_remaining,
                self._github_client.rate_limit_limit,
            )

    # Team Operations

    async def list_teams(self) -> list[Team]:
        """
        List all teams in the workspace.

        Returns:
            List of teams.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            teams = await self._linear_client.list_teams()
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "list_teams",
                {"count": len(teams)},
            )
            return teams
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure("list_teams", str(e))
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    # Issue Operations

    async def list_issues(
        self,
        team_id: str | None = None,
        first: int = 50,
        include_archived: bool = False,
    ) -> list[Issue]:
        """
        List issues, optionally filtered by team.

        Args:
            team_id: Optional team ID to filter by.
            first: Number of issues to fetch.
            include_archived: Whether to include archived issues.

        Returns:
            List of issues.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            issues = await self._linear_client.list_issues(team_id, first, include_archived)
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "list_issues",
                {"count": len(issues), "team_id": team_id},
            )
            return issues
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "list_issues",
                str(e),
                {"team_id": team_id},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    async def get_issue(self, issue_id: str) -> Issue | None:
        """
        Get a specific issue by ID.

        Args:
            issue_id: The issue ID.

        Returns:
            The issue, or None if not found.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            issue = await self._linear_client.get_issue(issue_id)
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "get_issue",
                {"issue_id": issue_id, "found": issue is not None},
            )
            return issue
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "get_issue",
                str(e),
                {"issue_id": issue_id},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            team_id: The team ID for the issue.
            title: Issue title.
            description: Optional issue description.
            priority: Optional priority (0-4).

        Returns:
            The created issue.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            issue = await self._linear_client.create_issue(
                team_id, title, description, priority
            )
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "create_issue",
                {"issue_id": issue.id, "team_id": team_id, "title": title},
            )
            return issue
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "create_issue",
                str(e),
                {"team_id": team_id, "title": title},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    async def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        assignee_id: str | None = None,
    ) -> Issue:
        """
        Update an existing issue.

        Args:
            issue_id: The issue ID to update.
            title: New title.
            description: New description.
            priority: New priority.
            state_id: New state ID.
            assignee_id: New assignee ID.

        Returns:
            The updated issue.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            issue = await self._linear_client.update_issue(
                issue_id, title, description, priority, state_id, assignee_id
            )
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "update_issue",
                {"issue_id": issue_id},
            )
            return issue
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "update_issue",
                str(e),
                {"issue_id": issue_id},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    async def create_sub_issue(
        self,
        parent_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
    ) -> Issue:
        """
        Create a sub-issue under a parent issue.

        Args:
            parent_id: The parent issue ID.
            title: Sub-issue title.
            description: Optional description.
            priority: Optional priority.

        Returns:
            The created sub-issue.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            issue = await self._linear_client.create_sub_issue(
                parent_id, title, description, priority
            )
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "create_sub_issue",
                {"parent_id": parent_id, "issue_id": issue.id, "title": title},
            )
            return issue
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "create_sub_issue",
                str(e),
                {"parent_id": parent_id, "title": title},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    # Comment Operations

    async def add_comment(self, issue_id: str, body: str) -> Comment:
        """
        Add a comment to an issue.

        Args:
            issue_id: The issue ID.
            body: Comment body.

        Returns:
            The created comment.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            comment = await self._linear_client.add_comment(issue_id, body)
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "add_comment",
                {"issue_id": issue_id, "comment_id": comment.id},
            )
            return comment
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "add_comment",
                str(e),
                {"issue_id": issue_id},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    # Reaction Operations

    async def add_reaction(self, issue_id: str, emoji: str) -> bool:
        """
        Add an emoji reaction to an issue.

        Args:
            issue_id: The issue ID.
            emoji: Emoji name.

        Returns:
            True if successful.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            success = await self._linear_client.add_reaction(issue_id, emoji)
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "add_reaction",
                {"issue_id": issue_id, "emoji": emoji, "success": success},
            )
            return success
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "add_reaction",
                str(e),
                {"issue_id": issue_id, "emoji": emoji},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    # Attachment Operations

    async def add_attachment(
        self,
        issue_id: str,
        title: str,
        url: str,
        subtitle: str | None = None,
    ) -> Attachment:
        """
        Add an attachment to an issue.

        Args:
            issue_id: The issue ID.
            title: Attachment title.
            url: Attachment URL.
            subtitle: Optional subtitle.

        Returns:
            The created attachment.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._self_learning is not None

        try:
            attachment = await self._linear_client.add_attachment(
                issue_id, title, url, subtitle
            )
            await self._update_health_from_linear()
            await self._self_learning.record_success(
                "add_attachment",
                {"issue_id": issue_id, "attachment_id": attachment.id, "url": url},
            )
            return attachment
        except (LinearClientError, RateLimitError) as e:
            await self._self_learning.record_failure(
                "add_attachment",
                str(e),
                {"issue_id": issue_id, "url": url},
            )
            if self._health_monitor:
                self._health_monitor.record_linear_error(str(e))
            raise

    # GitHub Integration

    async def get_github_pr(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get a GitHub pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            The pull request.
        """
        self._ensure_initialized()
        assert self._github_client is not None
        assert self._self_learning is not None

        try:
            pr = await self._github_client.get_pull_request(owner, repo, pr_number)
            await self._update_health_from_github()
            await self._self_learning.record_success(
                "get_github_pr",
                {"owner": owner, "repo": repo, "pr_number": pr_number},
            )
            return pr
        except GitHubClientError as e:
            await self._self_learning.record_failure(
                "get_github_pr",
                str(e),
                {"owner": owner, "repo": repo, "pr_number": pr_number},
            )
            if self._health_monitor:
                self._health_monitor.record_github_error(str(e))
            raise

    async def link_github_pr_to_issue(
        self,
        issue_id: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> Attachment:
        """
        Link a GitHub PR to a Linear issue.

        Args:
            issue_id: The Linear issue ID.
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            The created attachment.
        """
        self._ensure_initialized()
        assert self._linear_client is not None
        assert self._github_client is not None
        assert self._self_learning is not None

        try:
            # Get PR details
            pr = await self._github_client.get_pull_request(owner, repo, pr_number)
            await self._update_health_from_github()

            # Link to Linear issue
            attachment = await self._linear_client.link_github_pr(
                issue_id=issue_id,
                pr_url=pr.html_url,
                pr_title=pr.title,
                pr_number=pr.number,
                repo_name=f"{owner}/{repo}",
            )
            await self._update_health_from_linear()

            await self._self_learning.record_success(
                "link_github_pr_to_issue",
                {
                    "issue_id": issue_id,
                    "pr_url": pr.html_url,
                    "attachment_id": attachment.id,
                },
            )
            return attachment
        except (LinearClientError, GitHubClientError) as e:
            await self._self_learning.record_failure(
                "link_github_pr_to_issue",
                str(e),
                {"issue_id": issue_id, "owner": owner, "repo": repo, "pr_number": pr_number},
            )
            if self._health_monitor:
                if isinstance(e, LinearClientError):
                    self._health_monitor.record_linear_error(str(e))
                else:
                    self._health_monitor.record_github_error(str(e))
            raise

    # Health Operations

    async def check_health(self) -> HealthReport:
        """
        Perform a health check.

        Returns:
            The health report.
        """
        self._ensure_initialized()
        assert self._health_monitor is not None
        return await self._health_monitor.check_health()

    def get_health_status(self) -> HealthStatus:
        """
        Get the current health status.

        Returns:
            Current health status.
        """
        self._ensure_initialized()
        assert self._health_monitor is not None
        return self._health_monitor.get_status()

    def is_healthy(self) -> bool:
        """
        Check if the agent is healthy.

        Returns:
            True if healthy.
        """
        return self.get_health_status() == HealthStatus.HEALTHY

    # Self-Learning Operations

    async def get_learning_report(self) -> LearningReport:
        """
        Get a self-learning report.

        Returns:
            The learning report.
        """
        self._ensure_initialized()
        assert self._self_learning is not None
        return await self._self_learning.generate_report()

    async def get_improvement_summary(self) -> str:
        """
        Get a human-readable improvement summary.

        Returns:
            Summary string.
        """
        self._ensure_initialized()
        assert self._self_learning is not None
        return await self._self_learning.get_improvement_summary()

    # State Operations

    async def save_state(self) -> None:
        """Save current agent state."""
        self._ensure_initialized()
        assert self._state_storage is not None
        assert self._health_monitor is not None

        report = self._health_monitor.last_report
        state = AgentState(
            last_health_check=report.timestamp if report else None,
            is_healthy=self.is_healthy(),
            quota_remaining=report.linear.quota.remaining if report else None,
            quota_limit=report.linear.quota.limit if report else None,
        )
        await self._state_storage.save(state)

    async def load_state(self) -> AgentState:
        """
        Load saved agent state.

        Returns:
            The loaded state.
        """
        self._ensure_initialized()
        assert self._state_storage is not None
        return await self._state_storage.load()
