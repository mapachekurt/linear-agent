"""
Linear API client module.

This module provides async client for interacting with Linear's GraphQL API,
supporting CRUD operations for issues, teams, comments, and more.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from linear_agent.config import LinearSettings

logger = logging.getLogger(__name__)


@dataclass
class Team:
    """Represents a Linear team."""

    id: str
    name: str
    key: str
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Team":
        """Create a Team from API response data."""
        return cls(
            id=data["id"],
            name=data["name"],
            key=data["key"],
            description=data.get("description"),
        )


@dataclass
class Issue:
    """Represents a Linear issue."""

    id: str
    identifier: str
    title: str
    description: str | None = None
    state: dict[str, Any] | None = None
    priority: int = 0
    team_id: str | None = None
    parent_id: str | None = None
    labels: list[dict[str, Any]] = field(default_factory=list)
    assignee: dict[str, Any] | None = None
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create an Issue from API response data."""
        return cls(
            id=data["id"],
            identifier=data["identifier"],
            title=data["title"],
            description=data.get("description"),
            state=data.get("state"),
            priority=data.get("priority", 0),
            team_id=data.get("team", {}).get("id") if data.get("team") else None,
            parent_id=data.get("parent", {}).get("id") if data.get("parent") else None,
            labels=[label for label in data.get("labels", {}).get("nodes", [])],
            assignee=data.get("assignee"),
            url=data.get("url"),
        )


@dataclass
class Comment:
    """Represents a Linear comment."""

    id: str
    body: str
    user: dict[str, Any] | None = None
    created_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Comment":
        """Create a Comment from API response data."""
        return cls(
            id=data["id"],
            body=data["body"],
            user=data.get("user"),
            created_at=data.get("createdAt"),
        )


@dataclass
class Attachment:
    """Represents a Linear attachment."""

    id: str
    title: str
    url: str
    subtitle: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Attachment":
        """Create an Attachment from API response data."""
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            subtitle=data.get("subtitle"),
        )


class LinearClientError(Exception):
    """Base exception for Linear client errors."""

    pass


class RateLimitError(LinearClientError):
    """Raised when rate limit is exceeded."""

    pass


class LinearClient:
    """Async client for Linear GraphQL API."""

    def __init__(self, settings: LinearSettings | None = None):
        """
        Initialize the Linear client.

        Args:
            settings: Linear API settings. If not provided, loads from environment.
        """
        self.settings = settings or LinearSettings.from_env()
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_remaining: int | None = None
        self._rate_limit_limit: int | None = None

    @property
    def rate_limit_remaining(self) -> int | None:
        """Get the remaining rate limit quota."""
        return self._rate_limit_remaining

    @property
    def rate_limit_limit(self) -> int | None:
        """Get the rate limit maximum."""
        return self._rate_limit_limit

    async def __aenter__(self) -> "LinearClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.timeout),
            headers={
                "Authorization": self.settings.api_key,
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        retries: int = 0,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query against Linear API.

        Args:
            query: GraphQL query string.
            variables: Query variables.
            retries: Current retry attempt.

        Returns:
            The data portion of the GraphQL response.

        Raises:
            LinearClientError: On API errors.
            RateLimitError: When rate limit is exceeded.
        """
        if not self._client:
            raise LinearClientError("Client not initialized. Use 'async with' context.")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = await self._client.post(self.settings.api_url, json=payload)

            # Update rate limit info from headers
            self._rate_limit_remaining = int(
                response.headers.get("x-ratelimit-requests-remaining", -1)
            )
            self._rate_limit_limit = int(
                response.headers.get("x-ratelimit-requests-limit", -1)
            )

            if response.status_code == 429:
                if retries < self.settings.backoff.max_retries:
                    delay = self.settings.backoff.get_delay(retries)
                    logger.warning(f"Rate limited, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    return await self._execute(query, variables, retries + 1)
                raise RateLimitError("Rate limit exceeded after max retries")

            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
                raise LinearClientError(f"GraphQL error: {error_msg}")

            return result.get("data", {})

        except httpx.HTTPStatusError as e:
            raise LinearClientError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise LinearClientError(f"Request error: {e}") from e

    # Team Operations

    async def list_teams(self) -> list[Team]:
        """
        List all teams in the workspace.

        Returns:
            List of teams.
        """
        query = """
        query ListTeams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        data = await self._execute(query)
        nodes = data.get("teams", {}).get("nodes", [])
        return [Team.from_dict(node) for node in nodes]

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
        query = """
        query ListIssues($teamId: ID, $first: Int!, $includeArchived: Boolean) {
            issues(
                first: $first
                filter: { team: { id: { eq: $teamId } } }
                includeArchived: $includeArchived
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    state {
                        id
                        name
                    }
                    team {
                        id
                    }
                    parent {
                        id
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    assignee {
                        id
                        name
                    }
                }
            }
        }
        """
        variables: dict[str, Any] = {
            "first": first,
            "includeArchived": include_archived,
        }
        if team_id:
            variables["teamId"] = team_id

        data = await self._execute(query, variables)
        nodes = data.get("issues", {}).get("nodes", [])
        return [Issue.from_dict(node) for node in nodes]

    async def get_issue(self, issue_id: str) -> Issue | None:
        """
        Get a specific issue by ID.

        Args:
            issue_id: The issue ID.

        Returns:
            The issue, or None if not found.
        """
        query = """
        query GetIssue($issueId: String!) {
            issue(id: $issueId) {
                id
                identifier
                title
                description
                priority
                url
                state {
                    id
                    name
                }
                team {
                    id
                }
                parent {
                    id
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                assignee {
                    id
                    name
                }
            }
        }
        """
        data = await self._execute(query, {"issueId": issue_id})
        issue_data = data.get("issue")
        return Issue.from_dict(issue_data) if issue_data else None

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        parent_id: str | None = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            team_id: The team ID for the issue.
            title: Issue title.
            description: Optional issue description.
            priority: Optional priority (0-4).
            parent_id: Optional parent issue ID for sub-issues.

        Returns:
            The created issue.
        """
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    state {
                        id
                        name
                    }
                    team {
                        id
                    }
                    parent {
                        id
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    assignee {
                        id
                        name
                    }
                }
            }
        }
        """
        input_data: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
        }
        if description:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if parent_id:
            input_data["parentId"] = parent_id

        data = await self._execute(mutation, {"input": input_data})
        issue_data = data.get("issueCreate", {}).get("issue")
        if not issue_data:
            raise LinearClientError("Failed to create issue")
        return Issue.from_dict(issue_data)

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
        mutation = """
        mutation UpdateIssue($issueId: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $issueId, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    state {
                        id
                        name
                    }
                    team {
                        id
                    }
                    parent {
                        id
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    assignee {
                        id
                        name
                    }
                }
            }
        }
        """
        input_data: dict[str, Any] = {}
        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if state_id is not None:
            input_data["stateId"] = state_id
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id

        data = await self._execute(mutation, {"issueId": issue_id, "input": input_data})
        issue_data = data.get("issueUpdate", {}).get("issue")
        if not issue_data:
            raise LinearClientError("Failed to update issue")
        return Issue.from_dict(issue_data)

    async def create_sub_issue(
        self,
        parent_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
    ) -> Issue:
        """
        Create a sub-issue (child issue) under a parent issue.

        Args:
            parent_id: The parent issue ID.
            title: Sub-issue title.
            description: Optional description.
            priority: Optional priority.

        Returns:
            The created sub-issue.
        """
        # First get the parent issue to determine the team
        parent = await self.get_issue(parent_id)
        if not parent or not parent.team_id:
            raise LinearClientError(f"Parent issue {parent_id} not found or has no team")

        return await self.create_issue(
            team_id=parent.team_id,
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
        )

    # Comment Operations

    async def add_comment(self, issue_id: str, body: str) -> Comment:
        """
        Add a comment to an issue.

        Args:
            issue_id: The issue ID.
            body: Comment body (markdown supported).

        Returns:
            The created comment.
        """
        mutation = """
        mutation AddComment($issueId: String!, $body: String!) {
            commentCreate(input: { issueId: $issueId, body: $body }) {
                success
                comment {
                    id
                    body
                    createdAt
                    user {
                        id
                        name
                    }
                }
            }
        }
        """
        data = await self._execute(mutation, {"issueId": issue_id, "body": body})
        comment_data = data.get("commentCreate", {}).get("comment")
        if not comment_data:
            raise LinearClientError("Failed to add comment")
        return Comment.from_dict(comment_data)

    # Reaction Operations

    async def add_reaction(self, issue_id: str, emoji: str) -> bool:
        """
        Add an emoji reaction to an issue.

        Args:
            issue_id: The issue ID.
            emoji: Emoji name (e.g., 'thumbsup', '+1', 'heart').

        Returns:
            True if successful.
        """
        # Linear uses createReaction mutation
        mutation = """
        mutation AddReaction($issueId: String!, $emoji: String!) {
            reactionCreate(input: { issueId: $issueId, emoji: $emoji }) {
                success
            }
        }
        """
        data = await self._execute(mutation, {"issueId": issue_id, "emoji": emoji})
        return data.get("reactionCreate", {}).get("success", False)

    # Attachment Operations

    async def add_attachment(
        self,
        issue_id: str,
        title: str,
        url: str,
        subtitle: str | None = None,
    ) -> Attachment:
        """
        Add an attachment/resource link to an issue.

        Args:
            issue_id: The issue ID.
            title: Attachment title.
            url: URL of the resource.
            subtitle: Optional subtitle/description.

        Returns:
            The created attachment.
        """
        mutation = """
        mutation AddAttachment(
            $issueId: String!,
            $title: String!,
            $url: String!,
            $subtitle: String
        ) {
            attachmentCreate(input: {
                issueId: $issueId,
                title: $title,
                url: $url,
                subtitle: $subtitle
            }) {
                success
                attachment {
                    id
                    title
                    url
                    subtitle
                }
            }
        }
        """
        variables = {
            "issueId": issue_id,
            "title": title,
            "url": url,
        }
        if subtitle:
            variables["subtitle"] = subtitle

        data = await self._execute(mutation, variables)
        attachment_data = data.get("attachmentCreate", {}).get("attachment")
        if not attachment_data:
            raise LinearClientError("Failed to add attachment")
        return Attachment.from_dict(attachment_data)

    async def link_github_pr(
        self,
        issue_id: str,
        pr_url: str,
        pr_title: str,
        pr_number: int,
        repo_name: str,
    ) -> Attachment:
        """
        Link a GitHub PR to a Linear issue as an attachment.

        Args:
            issue_id: The Linear issue ID.
            pr_url: The GitHub PR URL.
            pr_title: The PR title.
            pr_number: The PR number.
            repo_name: The repository name.

        Returns:
            The created attachment.
        """
        subtitle = f"PR #{pr_number} in {repo_name}"
        return await self.add_attachment(
            issue_id=issue_id,
            title=pr_title,
            url=pr_url,
            subtitle=subtitle,
        )
