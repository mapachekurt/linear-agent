"""
Linear API client for the Linear Product Management Agent.

Wraps both Linear MCP and REST API calls behind a unified interface.
"""

import logging
from typing import Any

import httpx

from agents.linear_agent.config import LinearConfig
from agents.linear_agent.models import LinearIssue, LinearProject

logger = logging.getLogger(__name__)


class LinearClientError(Exception):
    """Base exception for Linear client errors."""

    pass


class LinearClient:
    """
    Client for Linear API operations.

    Provides methods for:
    - Listing candidates
    - Getting/updating issues
    - Commenting on issues
    - Project operations
    """

    def __init__(self, config: LinearConfig | None = None):
        """Initialize the Linear client."""
        self.config = config or LinearConfig.from_env()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LinearClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers={
                "Authorization": self.config.api_key,
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute_graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        if not self._client:
            raise LinearClientError("Client not initialized. Use 'async with' context.")

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = await self._client.post(self.config.api_url, json=payload)
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

    # =========================================================================
    # Issue Operations
    # =========================================================================

    async def list_candidates(self, team_id: str | None = None) -> list[LinearIssue]:
        """
        List candidate issues (in Backlog/Candidate state).

        Args:
            team_id: Optional team filter.

        Returns:
            List of candidate issues.
        """
        query = """
        query ListCandidates($teamId: ID, $stateName: String) {
            issues(
                first: 100
                filter: {
                    team: { id: { eq: $teamId } }
                    state: { name: { eq: $stateName } }
                }
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    createdAt
                    updatedAt
                    state { name }
                    project { id }
                    labels { nodes { name } }
                }
            }
        }
        """
        variables: dict[str, Any] = {"stateName": self.config.state_candidate}
        if team_id:
            variables["teamId"] = team_id

        data = await self._execute_graphql(query, variables)
        nodes = data.get("issues", {}).get("nodes", [])
        return [LinearIssue.from_api_response(node) for node in nodes]

    async def get_issue(self, issue_id: str) -> LinearIssue | None:
        """Get a specific issue by ID."""
        query = """
        query GetIssue($issueId: String!) {
            issue(id: $issueId) {
                id
                identifier
                title
                description
                priority
                url
                createdAt
                updatedAt
                state { name }
                project { id }
                labels { nodes { name } }
            }
        }
        """
        data = await self._execute_graphql(query, {"issueId": issue_id})
        issue_data = data.get("issue")
        return LinearIssue.from_api_response(issue_data) if issue_data else None

    async def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        state_id: str | None = None,
        priority: int | None = None,
        label_ids: list[str] | None = None,
    ) -> LinearIssue:
        """Update an issue."""
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
                    state { name }
                    project { id }
                    labels { nodes { name } }
                }
            }
        }
        """
        input_data: dict[str, Any] = {}
        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if state_id is not None:
            input_data["stateId"] = state_id
        if priority is not None:
            input_data["priority"] = priority
        if label_ids is not None:
            input_data["labelIds"] = label_ids

        data = await self._execute_graphql(mutation, {"issueId": issue_id, "input": input_data})
        issue_data = data.get("issueUpdate", {}).get("issue")
        if not issue_data:
            raise LinearClientError("Failed to update issue")
        return LinearIssue.from_api_response(issue_data)

    async def comment_issue(self, issue_id: str, body: str) -> str:
        """Add a comment to an issue. Returns comment ID."""
        mutation = """
        mutation CommentIssue($issueId: String!, $body: String!) {
            commentCreate(input: { issueId: $issueId, body: $body }) {
                success
                comment { id }
            }
        }
        """
        data = await self._execute_graphql(mutation, {"issueId": issue_id, "body": body})
        comment_data = data.get("commentCreate", {}).get("comment")
        if not comment_data:
            raise LinearClientError("Failed to create comment")
        return comment_data["id"]

    async def add_labels(self, issue_id: str, label_names: list[str]) -> None:
        """Add labels to an issue by name."""
        # First, get or create label IDs
        # For simplicity, we'll use the label sync mutation
        # In production, you'd look up label IDs first
        # This is a simplified version - in production you'd resolve label names to IDs
        _ = issue_id, label_names  # Placeholder
        logger.warning("Label addition by name requires label ID lookup - not fully implemented")

    # =========================================================================
    # Project Operations
    # =========================================================================

    async def list_projects(self) -> list[LinearProject]:
        """List all projects."""
        query = """
        query ListProjects {
            projects(first: 100) {
                nodes {
                    id
                    name
                    description
                    state
                    url
                }
            }
        }
        """
        data = await self._execute_graphql(query)
        nodes = data.get("projects", {}).get("nodes", [])
        return [LinearProject.from_api_response(node) for node in nodes]

    async def get_project(self, project_id: str) -> LinearProject | None:
        """Get a specific project."""
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
                id
                name
                description
                state
                url
            }
        }
        """
        data = await self._execute_graphql(query, {"projectId": project_id})
        project_data = data.get("project")
        return LinearProject.from_api_response(project_data) if project_data else None

    async def create_improvement_issue(
        self,
        title: str,
        description: str,
        team_id: str,
    ) -> LinearIssue:
        """
        Create an issue in the improvements project.

        Used for self-improvement logging.
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
                    url
                    state { name }
                    labels { nodes { name } }
                }
            }
        }
        """
        input_data: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "description": description,
        }
        if self.config.improvements_project_id:
            input_data["projectId"] = self.config.improvements_project_id

        data = await self._execute_graphql(mutation, {"input": input_data})
        issue_data = data.get("issueCreate", {}).get("issue")
        if not issue_data:
            raise LinearClientError("Failed to create improvement issue")
        return LinearIssue.from_api_response(issue_data)


# =========================================================================
# MCP Wrapper (for when Linear MCP server is available)
# =========================================================================


class LinearMCPClient:
    """
    Wrapper for Linear MCP server calls.

    When the Linear MCP server is available, this provides the same
    interface but routes through MCP instead of direct REST.
    """

    def __init__(self, mcp_server_url: str | None = None):
        """Initialize MCP client."""
        self.mcp_server_url = mcp_server_url
        # MCP client initialization would go here
        logger.info("LinearMCPClient initialized (MCP not yet implemented)")

    async def list_candidates(self) -> list[LinearIssue]:
        """List candidates via MCP."""
        # MCP tool call would go here
        raise NotImplementedError("MCP integration pending")

    async def get_issue(self, issue_id: str) -> LinearIssue | None:
        """Get issue via MCP."""
        raise NotImplementedError("MCP integration pending")

    async def update_issue(self, issue_id: str, **fields: Any) -> LinearIssue:
        """Update issue via MCP."""
        raise NotImplementedError("MCP integration pending")

    async def comment_issue(self, issue_id: str, body: str) -> str:
        """Comment on issue via MCP."""
        raise NotImplementedError("MCP integration pending")
