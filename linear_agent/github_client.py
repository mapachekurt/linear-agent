"""
GitHub API client module.

This module provides an async client for interacting with GitHub's REST API,
supporting PR retrieval and linking to Linear issues.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from linear_agent.config import GitHubSettings

logger = logging.getLogger(__name__)


@dataclass
class PullRequest:
    """Represents a GitHub pull request."""

    id: int
    number: int
    title: str
    url: str
    html_url: str
    state: str
    user: str
    repo: str
    owner: str
    body: str | None = None
    merged: bool = False
    draft: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any], owner: str, repo: str) -> "PullRequest":
        """Create a PullRequest from API response data."""
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            url=data["url"],
            html_url=data["html_url"],
            state=data["state"],
            user=data["user"]["login"],
            repo=repo,
            owner=owner,
            body=data.get("body"),
            merged=data.get("merged", False),
            draft=data.get("draft", False),
        )


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""

    pass


class RateLimitError(GitHubClientError):
    """Raised when rate limit is exceeded."""

    pass


class GitHubClient:
    """Async client for GitHub REST API."""

    def __init__(self, settings: GitHubSettings | None = None):
        """
        Initialize the GitHub client.

        Args:
            settings: GitHub API settings. If not provided, loads from environment.
        """
        self.settings = settings or GitHubSettings.from_env()
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

    async def __aenter__(self) -> "GitHubClient":
        """Enter async context."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.settings.api_url,
            timeout=httpx.Timeout(self.settings.timeout),
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
        retries: int = 0,
    ) -> dict[str, Any] | list[Any]:
        """
        Make an HTTP request to GitHub API.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            retries: Current retry attempt.

        Returns:
            The JSON response.

        Raises:
            GitHubClientError: On API errors.
            RateLimitError: When rate limit is exceeded.
        """
        if not self._client:
            raise GitHubClientError("Client not initialized. Use 'async with' context.")

        try:
            response = await self._client.request(method, path, params=params)

            # Update rate limit info from headers
            remaining = response.headers.get("x-ratelimit-remaining")
            limit = response.headers.get("x-ratelimit-limit")
            if remaining:
                self._rate_limit_remaining = int(remaining)
            if limit:
                self._rate_limit_limit = int(limit)

            if response.status_code == 403 and "rate limit" in response.text.lower():
                if retries < self.settings.backoff.max_retries:
                    delay = self.settings.backoff.get_delay(retries)
                    logger.warning(f"Rate limited, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    return await self._request(method, path, params, retries + 1)
                raise RateLimitError("Rate limit exceeded after max retries")

            if response.status_code == 404:
                raise GitHubClientError(f"Resource not found: {path}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise GitHubClientError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise GitHubClientError(f"Request error: {e}") from e

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get a specific pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            The pull request.
        """
        path = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        data = await self._request("GET", path)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return PullRequest.from_dict(data, owner, repo)

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[PullRequest]:
        """
        List pull requests for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Filter by state ('open', 'closed', 'all').
            per_page: Number of results per page.

        Returns:
            List of pull requests.
        """
        path = f"/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": per_page}
        data = await self._request("GET", path, params)
        if not isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return [PullRequest.from_dict(pr, owner, repo) for pr in data]

    async def search_pull_requests(
        self,
        query: str,
        per_page: int = 30,
    ) -> list[PullRequest]:
        """
        Search for pull requests using GitHub search syntax.

        Args:
            query: Search query (e.g., 'is:pr repo:owner/repo author:username').
            per_page: Number of results per page.

        Returns:
            List of matching pull requests.
        """
        path = "/search/issues"
        params = {"q": f"is:pr {query}", "per_page": per_page}
        data = await self._request("GET", path, params)
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")

        results = []
        for item in data.get("items", []):
            # Extract owner/repo from repository_url
            repo_url = item.get("repository_url", "")
            parts = repo_url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1]
                # Get full PR details since search returns limited data
                try:
                    pr = await self.get_pull_request(owner, repo, item["number"])
                    results.append(pr)
                except GitHubClientError:
                    logger.warning(f"Could not fetch PR {item['number']} details")
        return results

    async def get_rate_limit(self) -> dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Rate limit information.
        """
        data = await self._request("GET", "/rate_limit")
        if isinstance(data, list):
            raise GitHubClientError("Unexpected response type")
        return data
