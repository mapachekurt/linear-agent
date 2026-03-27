"""
This module contains the service layer for managing the lifecycle of a Linear issue.
"""
import httpx
import os
from app.issue_management.linear_client import get_linear_client
from app.models.linear import LinearIssue

class IssueManagementService:
    def __init__(self):
        self.linear_client = get_linear_client()
        self.team_id = os.getenv("LINEAR_TEAM_ID")

    async def _execute_graphql_query(self, query: str, variables: dict = None):
        """Helper method to execute a GraphQL query."""
        response = await self.linear_client.post(
            "", json={"query": query, "variables": variables or {}}
        )
        response.raise_for_status()
        return response.json()

    async def accept_issue(self, issue: LinearIssue):
        """
        Accepts a new issue.
        In a real implementation, this could involve assigning the issue to the agent,
        adding a specific label, or posting a comment to acknowledge receipt.
        """
        print(f"Accepting issue: {issue.title}")
        # TODO: Implement full acceptance logic.

    async def analyze_issue(self, issue: LinearIssue):
        """
        Analyzes the issue to determine its nature, complexity, and priority.
        This could involve NLP to parse the title and description, applying labels,
        and estimating the effort required.
        """
        print(f"Analyzing issue: {issue.title}")
        # TODO: Implement full analysis logic.

    async def monitor_issue(self, issue: LinearIssue):
        """
        Monitors an issue for updates, such as new comments or changes in status.
        This could trigger other actions, like re-analysis or notifying the team.
        """
        print(f"Monitoring issue: {issue.title}")
        # TODO: Implement full monitoring logic.

    async def update_issue_status(self, issue_id: str, new_status_id: str):
        """Updates the status of a Linear issue."""
        print(f"Updating issue '{issue_id}' to status '{new_status_id}'")
        mutation = """
            mutation UpdateIssueStatus($issueId: String!, $stateId: String!) {
                issueUpdate(id: $issueId, input: { stateId: $stateId }) {
                    success
                    issue {
                        id
                        state {
                            id
                            name
                        }
                    }
                }
            }
        """
        variables = {"issueId": issue_id, "stateId": new_status_id}
        await self._execute_graphql_query(mutation, variables)

    async def close_issue(self, issue_id: str):
        """Closes a Linear issue by moving it to the 'Done' state."""
        print(f"Closing issue: {issue_id}")
        done_state_id = os.getenv("LINEAR_DONE_STATE_ID")
        if not done_state_id:
            raise ValueError("LINEAR_DONE_STATE_ID is not set.")
        await self.update_issue_status(issue_id, done_state_id)


    async def create_issue(self, title: str, description: str) -> str | None:
        """Creates a new issue in Linear."""
        print(f"Creating issue: {title}")
        mutation = """
            mutation CreateIssue($title: String!, $description: String, $teamId: String!) {
                issueCreate(input: { title: $title, description: $description, teamId: $teamId }) {
                    success
                    issue {
                        id
                    }
                }
            }
        """
        variables = {"title": title, "description": description, "teamId": self.team_id}
        response = await self._execute_graphql_query(mutation, variables)

        if response.get("data", {}).get("issueCreate", {}).get("success"):
            return response["data"]["issueCreate"]["issue"]["id"]
        return None

    async def create_attachment(self, issue_id: str, url: str, title: str):
        """Creates an attachment on a Linear issue."""
        print(f"Creating attachment on issue '{issue_id}': {title}")
        mutation = """
            mutation CreateAttachment($issueId: String!, $url: String!, $title: String!) {
                attachmentCreate(input: { issueId: $issueId, url: $url, title: $title }) {
                    success
                }
            }
        """
        variables = {"issueId": issue_id, "url": url, "title": title}
        await self._execute_graphql_query(mutation, variables)
