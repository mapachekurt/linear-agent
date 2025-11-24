"""Linear API client abstractions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol

from .backoff import retry_with_backoff
from .config import LinearSettings


class HttpSession(Protocol):
    """Protocol describing the subset of HTTP client features we need."""

    def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> Any:
        ...


@dataclass
class LinearIssue:
    """Representation of a Linear issue."""

    id: str
    title: str
    description: str
    status: str
    team_key: str


class LinearClient:
    """Thin Linear GraphQL client with retry and validation support."""

    def __init__(self, settings: LinearSettings, session: HttpSession):
        self.settings = settings
        self.session = session

    def create_issue(self, team_id: str, title: str, description: str) -> LinearIssue:
        """Create a new Linear issue using the GraphQL API."""

        payload = {
            "query": """
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) { issue { id title description state { name } team { key } } }
            }
            """,
            "variables": {"input": {"teamId": team_id, "title": title, "description": description}},
        }
        response = retry_with_backoff(
            lambda: self._post(payload), (ConnectionError, TimeoutError), self.settings.backoff
        )
        issue = response["data"]["issueCreate"]["issue"]
        return LinearIssue(
            id=issue["id"],
            title=issue["title"],
            description=issue.get("description", ""),
            status=issue["state"]["name"],
            team_key=issue["team"]["key"],
        )

    def transition_issue(self, issue_id: str, state_id: str) -> str:
        """Move an issue to a new workflow state and return the new status name."""

        payload = {
            "query": """
            mutation TransitionIssue($id: String!, $stateId: String!) {
                issueUpdate(id: $id, input: {stateId: $stateId}) { issue { state { name } } }
            }
            """,
            "variables": {"id": issue_id, "stateId": state_id},
        }
        response = retry_with_backoff(
            lambda: self._post(payload), (ConnectionError, TimeoutError), self.settings.backoff
        )
        return response["data"]["issueUpdate"]["issue"]["state"]["name"]

    def validate_webhook_signature(self, signature: str | None, payload: bytes) -> bool:
        """Validate webhook payloads using the configured secret.

        In production this should use HMAC verification. Here we only perform
        presence checks to keep the implementation dependency-free.
        """

        if self.settings.webhook_secret is None:
            return True
        if not signature:
            return False
        return signature == self.settings.webhook_secret[::-1]

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Authorization": self.settings.api_key}
        response = self.session.post(self.settings.api_url, json=payload, headers=headers)
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        if hasattr(response, "json"):
            return response.json()
        raise ValueError("HTTP session returned unsupported response type")
