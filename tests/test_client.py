"""Tests for the client module."""

from typing import Any
from unittest import mock

import httpx
import pytest

from linear_agent.client import (
    Attachment,
    Comment,
    Issue,
    LinearClient,
    LinearClientError,
    RateLimitError,
    Team,
)
from linear_agent.config import LinearSettings


def make_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Create a proper mock httpx response."""
    request = httpx.Request("POST", "https://api.linear.app/graphql")
    response = httpx.Response(
        status_code,
        json=json_data,
        headers=headers or {},
        request=request,
    )
    return response


class TestTeam:
    """Tests for Team dataclass."""

    def test_from_dict(self) -> None:
        """Test creating Team from dictionary."""
        data = {
            "id": "team-123",
            "name": "Engineering",
            "key": "ENG",
            "description": "Engineering team",
        }
        team = Team.from_dict(data)
        assert team.id == "team-123"
        assert team.name == "Engineering"
        assert team.key == "ENG"
        assert team.description == "Engineering team"

    def test_from_dict_minimal(self) -> None:
        """Test creating Team with minimal data."""
        data = {"id": "team-123", "name": "Team", "key": "TM"}
        team = Team.from_dict(data)
        assert team.description is None


class TestIssue:
    """Tests for Issue dataclass."""

    def test_from_dict(self) -> None:
        """Test creating Issue from dictionary."""
        data = {
            "id": "issue-123",
            "identifier": "ENG-1",
            "title": "Test Issue",
            "description": "A test issue",
            "priority": 2,
            "url": "https://linear.app/test/issue/ENG-1",
            "state": {"id": "state-1", "name": "Todo"},
            "team": {"id": "team-1"},
            "parent": None,
            "labels": {"nodes": [{"id": "label-1", "name": "bug", "color": "#ff0000"}]},
            "assignee": {"id": "user-1", "name": "Test User"},
        }
        issue = Issue.from_dict(data)
        assert issue.id == "issue-123"
        assert issue.identifier == "ENG-1"
        assert issue.title == "Test Issue"
        assert issue.priority == 2
        assert issue.team_id == "team-1"
        assert len(issue.labels) == 1

    def test_from_dict_minimal(self) -> None:
        """Test creating Issue with minimal data."""
        data = {
            "id": "issue-123",
            "identifier": "ENG-1",
            "title": "Test Issue",
        }
        issue = Issue.from_dict(data)
        assert issue.description is None
        assert issue.parent_id is None
        assert issue.labels == []


class TestComment:
    """Tests for Comment dataclass."""

    def test_from_dict(self) -> None:
        """Test creating Comment from dictionary."""
        data = {
            "id": "comment-123",
            "body": "This is a comment",
            "createdAt": "2024-01-01T00:00:00Z",
            "user": {"id": "user-1", "name": "Test User"},
        }
        comment = Comment.from_dict(data)
        assert comment.id == "comment-123"
        assert comment.body == "This is a comment"
        assert comment.created_at == "2024-01-01T00:00:00Z"


class TestAttachment:
    """Tests for Attachment dataclass."""

    def test_from_dict(self) -> None:
        """Test creating Attachment from dictionary."""
        data = {
            "id": "attachment-123",
            "title": "PR #42",
            "url": "https://github.com/org/repo/pull/42",
            "subtitle": "Fix bug",
        }
        attachment = Attachment.from_dict(data)
        assert attachment.id == "attachment-123"
        assert attachment.title == "PR #42"
        assert attachment.url == "https://github.com/org/repo/pull/42"


class TestLinearClient:
    """Tests for LinearClient."""

    @pytest.fixture
    def settings(self) -> LinearSettings:
        """Create test settings."""
        return LinearSettings(api_key="test-api-key")

    @pytest.fixture
    def mock_response(self) -> httpx.Response:
        """Create a mock successful response."""
        return httpx.Response(
            200,
            json={"data": {}},
            headers={
                "x-ratelimit-requests-remaining": "100",
                "x-ratelimit-requests-limit": "1000",
            },
        )

    def test_init(self, settings: LinearSettings) -> None:
        """Test client initialization."""
        client = LinearClient(settings)
        assert client.settings == settings
        assert client.rate_limit_remaining is None

    async def test_context_manager(self, settings: LinearSettings) -> None:
        """Test async context manager."""
        async with LinearClient(settings) as client:
            assert client._client is not None
        assert client._client is None

    async def test_execute_without_init(self, settings: LinearSettings) -> None:
        """Test that execute fails without initialization."""
        client = LinearClient(settings)
        with pytest.raises(LinearClientError, match="not initialized"):
            await client._execute("query { viewer { id } }")

    async def test_list_teams(self, settings: LinearSettings) -> None:
        """Test listing teams."""
        mock_data = {
            "data": {
                "teams": {
                    "nodes": [
                        {"id": "team-1", "name": "Team 1", "key": "T1"},
                        {"id": "team-2", "name": "Team 2", "key": "T2"},
                    ]
                }
            }
        }

        async with LinearClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "post",
                return_value=make_response(
                    200,
                    mock_data,
                    {
                        "x-ratelimit-requests-remaining": "99",
                        "x-ratelimit-requests-limit": "1000",
                    },
                ),
            ):
                teams = await client.list_teams()
                assert len(teams) == 2
                assert teams[0].name == "Team 1"
                assert client.rate_limit_remaining == 99

    async def test_create_issue(self, settings: LinearSettings) -> None:
        """Test creating an issue."""
        mock_data = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-new",
                        "identifier": "T1-1",
                        "title": "New Issue",
                        "description": "Description",
                        "priority": 2,
                        "url": "https://linear.app/test/issue/T1-1",
                        "state": {"id": "state-1", "name": "Todo"},
                        "team": {"id": "team-1"},
                        "parent": None,
                        "labels": {"nodes": []},
                        "assignee": None,
                    },
                }
            }
        }

        async with LinearClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "post",
                return_value=make_response(
                    200,
                    mock_data,
                    {
                        "x-ratelimit-requests-remaining": "98",
                        "x-ratelimit-requests-limit": "1000",
                    },
                ),
            ):
                issue = await client.create_issue(
                    team_id="team-1",
                    title="New Issue",
                    description="Description",
                    priority=2,
                )
                assert issue.id == "issue-new"
                assert issue.title == "New Issue"

    async def test_graphql_error(self, settings: LinearSettings) -> None:
        """Test handling of GraphQL errors."""
        mock_data = {"errors": [{"message": "Not authorized"}]}

        async with LinearClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "post",
                return_value=make_response(200, mock_data),
            ):
                with pytest.raises(LinearClientError, match="Not authorized"):
                    await client.list_teams()

    async def test_rate_limit_retry(self, settings: LinearSettings) -> None:
        """Test rate limit retry behavior."""
        settings.backoff.max_retries = 1
        settings.backoff.initial_delay = 0.01  # Fast retry for tests

        call_count = 0

        async def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_response(429, {})
            return make_response(
                200,
                {"data": {"teams": {"nodes": []}}},
                {
                    "x-ratelimit-requests-remaining": "1",
                    "x-ratelimit-requests-limit": "1000",
                },
            )

        async with LinearClient(settings) as client:
            with mock.patch.object(client._client, "post", side_effect=mock_post):  # type: ignore
                teams = await client.list_teams()
                assert teams == []
                assert call_count == 2

    async def test_rate_limit_exhausted(self, settings: LinearSettings) -> None:
        """Test rate limit exhaustion after max retries."""
        settings.backoff.max_retries = 1
        settings.backoff.initial_delay = 0.01

        async with LinearClient(settings) as client:
            with mock.patch.object(
                client._client,  # type: ignore
                "post",
                return_value=make_response(429, {}),
            ):
                with pytest.raises(RateLimitError):
                    await client.list_teams()
