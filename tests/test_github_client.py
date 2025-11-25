"""Tests for the GitHub client module."""

from typing import Any
from unittest import mock

import httpx
import pytest

from linear_agent.config import GitHubSettings
from linear_agent.github_client import (
    GitHubClient,
    GitHubClientError,
    PullRequest,
    RateLimitError,
)


def make_response(
    status_code: int = 200,
    json_data: dict[str, Any] | list[Any] | None = None,
    headers: dict[str, str] | None = None,
    text: str = "",
) -> httpx.Response:
    """Create a proper mock httpx response."""
    request = httpx.Request("GET", "https://api.github.com/test")
    if json_data is not None:
        response = httpx.Response(
            status_code,
            json=json_data,
            headers=headers or {},
            request=request,
        )
    else:
        response = httpx.Response(
            status_code,
            text=text,
            headers=headers or {},
            request=request,
        )
    return response


class TestPullRequest:
    """Tests for PullRequest dataclass."""

    def test_from_dict(self) -> None:
        """Test creating PullRequest from dictionary."""
        data = {
            "id": 123456,
            "number": 42,
            "title": "Fix bug in feature",
            "url": "https://api.github.com/repos/owner/repo/pulls/42",
            "html_url": "https://github.com/owner/repo/pull/42",
            "state": "open",
            "user": {"login": "testuser"},
            "body": "This PR fixes a bug",
            "merged": False,
            "draft": False,
        }
        pr = PullRequest.from_dict(data, "owner", "repo")
        assert pr.id == 123456
        assert pr.number == 42
        assert pr.title == "Fix bug in feature"
        assert pr.html_url == "https://github.com/owner/repo/pull/42"
        assert pr.state == "open"
        assert pr.user == "testuser"
        assert pr.owner == "owner"
        assert pr.repo == "repo"

    def test_from_dict_minimal(self) -> None:
        """Test creating PullRequest with minimal data."""
        data = {
            "id": 123,
            "number": 1,
            "title": "Test PR",
            "url": "https://api.github.com/repos/o/r/pulls/1",
            "html_url": "https://github.com/o/r/pull/1",
            "state": "open",
            "user": {"login": "user"},
        }
        pr = PullRequest.from_dict(data, "o", "r")
        assert pr.body is None
        assert pr.merged is False
        assert pr.draft is False


class TestGitHubClient:
    """Tests for GitHubClient."""

    @pytest.fixture
    def settings(self) -> GitHubSettings:
        """Create test settings."""
        return GitHubSettings(api_key="test-token")

    def test_init(self, settings: GitHubSettings) -> None:
        """Test client initialization."""
        client = GitHubClient(settings)
        assert client.settings == settings
        assert client.rate_limit_remaining is None

    async def test_context_manager(self, settings: GitHubSettings) -> None:
        """Test async context manager."""
        async with GitHubClient(settings) as client:
            assert client._client is not None
        assert client._client is None

    async def test_request_without_init(self, settings: GitHubSettings) -> None:
        """Test that request fails without initialization."""
        client = GitHubClient(settings)
        with pytest.raises(GitHubClientError, match="not initialized"):
            await client._request("GET", "/repos/owner/repo")

    async def test_get_pull_request(self, settings: GitHubSettings) -> None:
        """Test getting a pull request."""
        mock_data = {
            "id": 12345,
            "number": 42,
            "title": "Test PR",
            "url": "https://api.github.com/repos/owner/repo/pulls/42",
            "html_url": "https://github.com/owner/repo/pull/42",
            "state": "open",
            "user": {"login": "testuser"},
            "body": "PR body",
            "merged": False,
            "draft": False,
        }

        async with GitHubClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "request",
                return_value=make_response(
                    200,
                    mock_data,
                    {
                        "x-ratelimit-remaining": "4999",
                        "x-ratelimit-limit": "5000",
                    },
                ),
            ):
                pr = await client.get_pull_request("owner", "repo", 42)
                assert pr.number == 42
                assert pr.title == "Test PR"
                assert client.rate_limit_remaining == 4999

    async def test_list_pull_requests(self, settings: GitHubSettings) -> None:
        """Test listing pull requests."""
        mock_data = [
            {
                "id": 1,
                "number": 1,
                "title": "PR 1",
                "url": "https://api.github.com/repos/o/r/pulls/1",
                "html_url": "https://github.com/o/r/pull/1",
                "state": "open",
                "user": {"login": "user1"},
            },
            {
                "id": 2,
                "number": 2,
                "title": "PR 2",
                "url": "https://api.github.com/repos/o/r/pulls/2",
                "html_url": "https://github.com/o/r/pull/2",
                "state": "open",
                "user": {"login": "user2"},
            },
        ]

        async with GitHubClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "request",
                return_value=make_response(200, mock_data),
            ):
                prs = await client.list_pull_requests("owner", "repo")
                assert len(prs) == 2
                assert prs[0].number == 1
                assert prs[1].number == 2

    async def test_not_found_error(self, settings: GitHubSettings) -> None:
        """Test handling of 404 errors."""
        async with GitHubClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "request",
                return_value=make_response(404, {"message": "Not Found"}),
            ):
                with pytest.raises(GitHubClientError, match="not found"):
                    await client.get_pull_request("owner", "repo", 999)

    async def test_rate_limit_retry(self, settings: GitHubSettings) -> None:
        """Test rate limit retry behavior."""
        settings.backoff.max_retries = 1
        settings.backoff.initial_delay = 0.01

        call_count = 0

        async def mock_request(*args: Any, **kwargs: Any) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_response(403, text="rate limit exceeded")
            return make_response(
                200,
                [],
                {
                    "x-ratelimit-remaining": "1",
                    "x-ratelimit-limit": "5000",
                },
            )

        async with GitHubClient(settings) as client:
            with mock.patch.object(client._client, "request", side_effect=mock_request):  # type: ignore
                prs = await client.list_pull_requests("owner", "repo")
                assert prs == []
                assert call_count == 2

    async def test_rate_limit_exhausted(self, settings: GitHubSettings) -> None:
        """Test rate limit exhaustion."""
        settings.backoff.max_retries = 1
        settings.backoff.initial_delay = 0.01

        async with GitHubClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "request",
                return_value=make_response(403, text="rate limit exceeded"),
            ):
                with pytest.raises(RateLimitError):
                    await client.get_pull_request("owner", "repo", 1)

    async def test_get_rate_limit(self, settings: GitHubSettings) -> None:
        """Test getting rate limit status."""
        mock_data = {
            "resources": {
                "core": {"limit": 5000, "remaining": 4999, "reset": 1234567890}
            }
        }

        async with GitHubClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "request",
                return_value=make_response(200, mock_data),
            ):
                rate_limit = await client.get_rate_limit()
                assert "resources" in rate_limit
