"""Tests for the orchestrator module."""

from pathlib import Path
from typing import Any
from unittest import mock

import httpx
import pytest

from linear_agent.config import AgentConfig, GitHubSettings, LinearSettings, StorageSettings
from linear_agent.health import HealthStatus
from linear_agent.orchestrator import Orchestrator


def make_linear_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Create a proper mock httpx response for Linear API."""
    request = httpx.Request("POST", "https://api.linear.app/graphql")
    return httpx.Response(
        status_code,
        json=json_data,
        headers=headers or {},
        request=request,
    )


def make_github_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Create a proper mock httpx response for GitHub API."""
    request = httpx.Request("GET", "https://api.github.com/test")
    return httpx.Response(
        status_code,
        json=json_data,
        headers=headers or {},
        request=request,
    )


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> AgentConfig:
        """Create test configuration."""
        return AgentConfig(
            linear=LinearSettings(api_key="test-linear-key"),
            github=GitHubSettings(api_key="test-github-key"),
            storage=StorageSettings(
                audit_log_path=tmp_path / "audit.jsonl",
                state_file_path=tmp_path / "state.json",
            ),
        )

    async def test_context_manager(self, config: AgentConfig) -> None:
        """Test async context manager."""
        async with Orchestrator(config) as orch:
            assert orch._initialized is True
        assert orch._initialized is False

    async def test_initialize_and_shutdown(self, config: AgentConfig) -> None:
        """Test manual initialization and shutdown."""
        orch = Orchestrator(config)
        await orch.initialize()
        assert orch._initialized is True
        assert orch._linear_client is not None
        assert orch._github_client is not None

        await orch.shutdown()
        assert orch._initialized is False

    async def test_ensure_initialized_fails(self, config: AgentConfig) -> None:
        """Test that operations fail without initialization."""
        orch = Orchestrator(config)
        with pytest.raises(RuntimeError, match="not initialized"):
            await orch.list_teams()

    async def test_list_teams(self, config: AgentConfig) -> None:
        """Test listing teams."""
        mock_teams_data = {
            "data": {
                "teams": {
                    "nodes": [
                        {"id": "team-1", "name": "Team 1", "key": "T1"},
                    ]
                }
            }
        }

        async with Orchestrator(config) as orch:
            with mock.patch.object(
                orch._linear_client._client,  # type: ignore
                "post",
                return_value=make_linear_response(
                    200,
                    mock_teams_data,
                    {
                        "x-ratelimit-requests-remaining": "99",
                        "x-ratelimit-requests-limit": "1000",
                    },
                ),
            ):
                teams = await orch.list_teams()
                assert len(teams) == 1
                assert teams[0].name == "Team 1"

    async def test_create_issue(self, config: AgentConfig) -> None:
        """Test creating an issue."""
        mock_data = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-new",
                        "identifier": "T1-1",
                        "title": "Test Issue",
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

        async with Orchestrator(config) as orch:
            with mock.patch.object(
                orch._linear_client._client,  # type: ignore
                "post",
                return_value=make_linear_response(
                    200,
                    mock_data,
                    {
                        "x-ratelimit-requests-remaining": "98",
                        "x-ratelimit-requests-limit": "1000",
                    },
                ),
            ):
                issue = await orch.create_issue(
                    team_id="team-1",
                    title="Test Issue",
                    description="Description",
                    priority=2,
                )
                assert issue.id == "issue-new"
                assert issue.title == "Test Issue"

    async def test_get_github_pr(self, config: AgentConfig) -> None:
        """Test getting a GitHub PR."""
        mock_pr_data = {
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

        async with Orchestrator(config) as orch:
            with mock.patch.object(
                orch._github_client._client,  # type: ignore
                "request",
                return_value=make_github_response(
                    200,
                    mock_pr_data,
                    {
                        "x-ratelimit-remaining": "4999",
                        "x-ratelimit-limit": "5000",
                    },
                ),
            ):
                pr = await orch.get_github_pr("owner", "repo", 42)
                assert pr.number == 42
                assert pr.title == "Test PR"

    async def test_check_health(self, config: AgentConfig) -> None:
        """Test health check."""
        async with Orchestrator(config) as orch:
            report = await orch.check_health()
            assert report.overall_status == HealthStatus.HEALTHY

    async def test_get_health_status(self, config: AgentConfig) -> None:
        """Test getting health status."""
        async with Orchestrator(config) as orch:
            status = orch.get_health_status()
            assert status == HealthStatus.HEALTHY

    async def test_is_healthy(self, config: AgentConfig) -> None:
        """Test is_healthy method."""
        async with Orchestrator(config) as orch:
            assert orch.is_healthy() is True

    async def test_get_learning_report(self, config: AgentConfig) -> None:
        """Test getting learning report."""
        async with Orchestrator(config) as orch:
            report = await orch.get_learning_report()
            # Should have at least one entry from initialization
            assert report.total_actions >= 1

    async def test_get_improvement_summary(self, config: AgentConfig) -> None:
        """Test getting improvement summary."""
        async with Orchestrator(config) as orch:
            summary = await orch.get_improvement_summary()
            assert "Self-Learning Summary" in summary

    async def test_save_and_load_state(self, config: AgentConfig) -> None:
        """Test saving and loading state."""
        async with Orchestrator(config) as orch:
            await orch.check_health()
            await orch.save_state()

            state = await orch.load_state()
            assert state.is_healthy is True
