import pytest
from unittest.mock import AsyncMock, MagicMock
from app.github_sync.service import GitHubSyncService
from app.models.github import GitHubPullRequest, GitHubBranch

@pytest.fixture
def mock_issue_service():
    """Fixture to create a mock IssueManagementService."""
    service = MagicMock()
    service.create_attachment = AsyncMock()
    service.close_issue = AsyncMock()
    return service

@pytest.fixture
def github_sync_service(mock_issue_service):
    """Fixture to create a GitHubSyncService with a mocked issue service."""
    return GitHubSyncService(mock_issue_service)

@pytest.mark.asyncio
async def test_link_branch_to_issue(github_sync_service, mock_issue_service):
    """Tests that a branch is correctly linked to a Linear issue."""
    branch = GitHubBranch(ref="feature/LIN-123-new-feature")
    repo_url = "https://github.com/test/repo"

    await github_sync_service.link_branch_to_issue(branch, repo_url)

    mock_issue_service.create_attachment.assert_called_once_with(
        "LIN-123",
        "https://github.com/test/repo/tree/feature/LIN-123-new-feature",
        "Branch: feature/LIN-123-new-feature"
    )

@pytest.mark.asyncio
async def test_link_pr_to_issue(github_sync_service, mock_issue_service):
    """Tests that a PR is correctly linked to a Linear issue."""
    pr = GitHubPullRequest(
        id=1, number=1, title="LIN-456 Fix login bug",
        user={"login": "user", "id": 1, "avatar_url": ""}, state="open",
        created_at="2023-01-01T12:00:00Z", updated_at="2023-01-01T12:00:00Z",
        body="This PR fixes the login bug.", merged_at=None
    )
    repo_url = "https://github.com/test/repo"

    await github_sync_service.link_pr_to_issue(pr, repo_url)

    mock_issue_service.create_attachment.assert_called_once_with(
        "LIN-456",
        "https://github.com/test/repo/pull/1",
        "PR #1: LIN-456 Fix login bug"
    )
    mock_issue_service.close_issue.assert_not_called()

@pytest.mark.asyncio
async def test_link_pr_closes_issue(github_sync_service, mock_issue_service):
    """Tests that a merged PR with magic words closes the linked Linear issue."""
    pr = GitHubPullRequest(
        id=1, number=1, title="Fixes LIN-789",
        user={"login": "user", "id": 1, "avatar_url": ""}, state="closed",
        created_at="2023-01-01T12:00:00Z", updated_at="2023-01-01T12:00:00Z",
        body="This PR closes the issue.", merged_at="2023-01-02T12:00:00Z"
    )
    repo_url = "https://github.com/test/repo"

    await github_sync_service.link_pr_to_issue(pr, repo_url)

    mock_issue_service.create_attachment.assert_called_once()
    mock_issue_service.close_issue.assert_called_once_with("LIN-789")
