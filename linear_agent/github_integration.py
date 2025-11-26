"""GitHub integration helpers for syncing with Linear."""
from __future__ import annotations

from typing import Any, Dict, Protocol

from .backoff import retry_with_backoff
from .config import GitHubSettings


class GitHubSession(Protocol):
    """Protocol describing GitHub HTTP session methods we rely on."""

    def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> Any:
        ...

    def patch(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> Any:
        ...


class GitHubIntegration:
    """Minimal GitHub API wrapper to link PRs and issues."""

    def __init__(self, settings: GitHubSettings, session: GitHubSession):
        self.settings = settings
        self.session = session

    def link_pull_request(self, repo: str, pull_number: int, linear_issue_id: str) -> None:
        """Add a Linear issue reference to the PR body."""

        url = f"{self.settings.api_url}/repos/{repo}/pulls/{pull_number}"
        payload = {"body": f"Linked to Linear issue {linear_issue_id}"}
        retry_with_backoff(
            lambda: self._patch(url, payload), (ConnectionError, TimeoutError), self.settings.backoff
        )

    def comment_on_issue(self, repo: str, issue_number: int, comment: str) -> None:
        """Post a comment to a GitHub issue."""

        url = f"{self.settings.api_url}/repos/{repo}/issues/{issue_number}/comments"
        payload = {"body": comment}
        retry_with_backoff(
            lambda: self._post(url, payload), (ConnectionError, TimeoutError), self.settings.backoff
        )

    def _post(self, url: str, payload: Dict[str, Any]) -> Any:
        headers = {"Authorization": f"Bearer {self.settings.token}"}
        response = self.session.post(url, json=payload, headers=headers)
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        return response

    def _patch(self, url: str, payload: Dict[str, Any]) -> Any:
        headers = {"Authorization": f"Bearer {self.settings.token}"}
        response = self.session.patch(url, json=payload, headers=headers)
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        return response
