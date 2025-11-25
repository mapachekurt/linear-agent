"""
This module contains the service layer for syncing issue state between Linear and GitHub.
"""
import re
import httpx
from app.issue_management.service import IssueManagementService
from app.models.github import GitHubPullRequest, GitHubBranch
from app.models.linear import LinearIssue

class GitHubSyncService:
    def __init__(self, issue_management_service: IssueManagementService):
        self.issue_management_service = issue_management_service

    def extract_linear_issue_id(self, text: str) -> str | None:
        """Extracts a Linear issue ID (e.g., 'LIN-123') from a string."""
        match = re.search(r"\b([A-Z]+-\d+)\b", text)
        return match.group(1) if match else None

    async def link_branch_to_issue(self, branch: GitHubBranch, repository_url: str):
        """Links a GitHub branch to a Linear issue."""
        issue_id = self.extract_linear_issue_id(branch.ref)
        if issue_id:
            branch_url = f"{repository_url}/tree/{branch.ref}"
            title = f"Branch: {branch.ref}"
            await self.issue_management_service.create_attachment(issue_id, branch_url, title)

    async def link_pr_to_issue(self, pr: GitHubPullRequest, repository_url: str):
        """Links a GitHub PR to a Linear issue and updates the issue status."""
        issue_id = self.extract_linear_issue_id(pr.title) or self.extract_linear_issue_id(pr.body or "")
        if issue_id:
            pr_url = f"{repository_url}/pull/{pr.number}"
            title = f"PR #{pr.number}: {pr.title}"
            await self.issue_management_service.create_attachment(issue_id, pr_url, title)

            # Check for magic words to close the issue
            if pr.merged_at and any(keyword in (pr.body or "").lower() for keyword in ["closes", "fixes", "resolves"]):
                 await self.issue_management_service.close_issue(issue_id)
