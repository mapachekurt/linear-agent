"""
GitHub API client for the Linear Product Management Agent.

Wraps both GitHub MCP and REST/GraphQL API calls.
Used for:
- Repo discovery
- Linking Linear issues to GitHub issues/PRs
- Starting Copilot agent sessions (via MCP)
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from agents.linear_agent.config import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""

    pass


@dataclass
class GitHubRepo:
    """Representation of a GitHub repository."""

    owner: str
    name: str
    full_name: str
    description: str | None = None
    url: str | None = None
    default_branch: str = "main"


@dataclass
class GitHubIssue:
    """Representation of a GitHub issue."""

    id: int
    number: int
    title: str
    body: str | None = None
    state: str = "open"
    url: str | None = None


@dataclass
class GitHubPullRequest:
    """Representation of a GitHub pull request."""

    id: int
    number: int
    title: str
    body: str | None = None
    state: str = "open"
    url: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None


class GitHubClient:
    """
    Client for GitHub API operations.

    Provides methods for:
    - Repository operations
    - Issue/PR linking
    - Metadata reading
    """

    def __init__(self, config: GitHubConfig | None = None):
        """Initialize the GitHub client."""
        self.config = config or GitHubConfig.from_env()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        """Enter async context."""
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        self._client = httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers=headers,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an HTTP request to GitHub API."""
        if not self._client:
            raise GitHubClientError("Client not initialized. Use 'async with' context.")

        try:
            response = await self._client.request(method, path, params=params, json=json)

            if response.status_code == 404:
                raise GitHubClientError(f"Resource not found: {path}")

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise GitHubClientError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise GitHubClientError(f"Request error: {e}") from e

    # =========================================================================
    # Repository Operations
    # =========================================================================

    async def get_repo(self, owner: str, repo: str) -> GitHubRepo:
        """Get repository information."""
        path = f"/repos/{owner}/{repo}"
        data = await self._request("GET", path)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return GitHubRepo(
            owner=data["owner"]["login"],
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            url=data.get("html_url"),
            default_branch=data.get("default_branch", "main"),
        )

    async def list_repos(self, org: str) -> list[GitHubRepo]:
        """List repositories in an organization."""
        path = f"/orgs/{org}/repos"
        data = await self._request("GET", path, params={"per_page": 100})
        if not isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return [
            GitHubRepo(
                owner=repo["owner"]["login"],
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                url=repo.get("html_url"),
            )
            for repo in data
        ]

    async def detect_surface_from_repo(self, owner: str, repo: str) -> str | None:
        """
        Detect product surface from repository name.

        Returns 'solutions', 'app', or None.
        """
        repo_lower = repo.lower()
        if self.config.solutions_repo_pattern.lower() in repo_lower:
            return "solutions"
        if self.config.app_repo_pattern.lower() in repo_lower:
            return "app"
        return None

    # =========================================================================
    # Issue Operations
    # =========================================================================

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
    ) -> GitHubIssue:
        """Create a GitHub issue."""
        path = f"/repos/{owner}/{repo}/issues"
        payload: dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels

        data = await self._request("POST", path, json=payload)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            url=data.get("html_url"),
        )

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> GitHubIssue:
        """Get a GitHub issue."""
        path = f"/repos/{owner}/{repo}/issues/{issue_number}"
        data = await self._request("GET", path)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            url=data.get("html_url"),
        )

    async def add_comment(self, owner: str, repo: str, issue_number: int, body: str) -> int:
        """Add a comment to a GitHub issue. Returns comment ID."""
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = await self._request("POST", path, json={"body": body})
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return data["id"]

    # =========================================================================
    # PR Operations
    # =========================================================================

    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> GitHubPullRequest:
        """Get a pull request."""
        path = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        data = await self._request("GET", path)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return GitHubPullRequest(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            url=data.get("html_url"),
            head_ref=data.get("head", {}).get("ref"),
            base_ref=data.get("base", {}).get("ref"),
        )

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
    ) -> list[GitHubPullRequest]:
        """List pull requests."""
        path = f"/repos/{owner}/{repo}/pulls"
        data = await self._request("GET", path, params={"state": state, "per_page": 100})
        if not isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return [
            GitHubPullRequest(
                id=pr["id"],
                number=pr["number"],
                title=pr["title"],
                body=pr.get("body"),
                state=pr["state"],
                url=pr.get("html_url"),
                head_ref=pr.get("head", {}).get("ref"),
                base_ref=pr.get("base", {}).get("ref"),
            )
            for pr in data
        ]


# =========================================================================
# GitHub MCP Client (for Copilot integration)
# =========================================================================


class GitHubMCPClient:
    """
    Wrapper for GitHub MCP server calls.

    Used specifically for:
    - Starting/monitoring Copilot coding agent sessions
    - Code analysis/summarization requests
    """

    def __init__(self, mcp_server_url: str | None = None):
        """Initialize MCP client."""
        self.mcp_server_url = mcp_server_url
        logger.info("GitHubMCPClient initialized (MCP not yet implemented)")

    async def start_copilot_agent_session(
        self,
        repo: str,
        brief: str,
        files: list[str] | None = None,
    ) -> str:
        """
        Start a Copilot coding agent session.

        Args:
            repo: Repository to work on (owner/name format)
            brief: Task brief for the agent
            files: Optional list of files to focus on

        Returns:
            Session ID for tracking
        """
        # MCP tool call would go here
        raise NotImplementedError("MCP Copilot integration pending")

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Get status of a Copilot agent session."""
        raise NotImplementedError("MCP Copilot integration pending")

    async def request_code_analysis(
        self,
        repo: str,
        files: list[str],
        query: str,
    ) -> str:
        """Request code analysis/summarization."""
        raise NotImplementedError("MCP Copilot integration pending")
