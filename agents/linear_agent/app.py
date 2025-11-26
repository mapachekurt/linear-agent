"""
ADK Application entrypoint for the Linear Product Management Agent.

Designed for deployment on Vertex AI Agent Engine.
"""

import logging
from typing import Any

from agents.linear_agent.config import AgentConfig
from agents.linear_agent.core import LinearAgentCore
from agents.linear_agent.github_client import GitHubClient
from agents.linear_agent.linear_client import LinearClient
from agents.linear_agent.models import (
    ExecutionRoute,
    LinearIssue,
    TriageResult,
)

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure structured logging for Vertex AI."""
    logging.basicConfig(
        level=logging.INFO,
        format='{"severity": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
    )


class LinearProductManagementAgent:
    """
    Linear Product Management Agent.

    The product/backlog brain for Mapache that:
    - Keeps Linear projects/issues lean and up to date
    - Reflects the Mapache business model (solutions → app)
    - Orchestrates execution routing to GitHub Copilot
    - Acts as glue between Slack, Linear, and GitHub
    """

    def __init__(self, config: AgentConfig | None = None):
        """Initialize the agent."""
        self.config = config or AgentConfig.from_env()
        self.core = LinearAgentCore(self.config)
        self._linear_client: LinearClient | None = None
        self._github_client: GitHubClient | None = None

    async def __aenter__(self) -> "LinearProductManagementAgent":
        """Enter async context and initialize clients."""
        self._linear_client = LinearClient(self.config.linear)
        await self._linear_client.__aenter__()

        self._github_client = GitHubClient(self.config.github)
        await self._github_client.__aenter__()

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context and cleanup."""
        if self._linear_client:
            await self._linear_client.__aexit__(exc_type, exc_val, exc_tb)
        if self._github_client:
            await self._github_client.__aexit__(exc_type, exc_val, exc_tb)

    # =========================================================================
    # Slack Bot Interface Methods (called via HTTP/A2A)
    # =========================================================================

    async def triage(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        Triage all candidate issues.

        Slack command: /linear-agent triage

        Args:
            project_id: Optional project to filter by.

        Returns:
            List of triage results.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        results: list[dict[str, Any]] = []
        candidates = await self._linear_client.list_candidates()

        for issue in candidates:
            triage_result = self.core.triage(issue)

            # Update the issue in Linear
            if triage_result.lean_ticket and self.config.auto_leanify:
                await self._update_issue_from_triage(issue, triage_result)

            results.append({
                "issue_id": triage_result.issue_id,
                "title": triage_result.original_title,
                "surfaces": [s.value for s in triage_result.surfaces],
                "size": triage_result.size.value if triage_result.size else None,
                "route": triage_result.route.value if triage_result.route else None,
                "status": triage_result.status.value,
                "priority_score": triage_result.priority_score,
                "rationale": triage_result.rationale,
            })

        logger.info(f"Triaged {len(results)} issues")
        return results

    async def next_items(self, count: int = 5) -> list[dict[str, Any]]:
        """
        Get top N recommended issues to work on.

        Slack command: /linear-agent next

        Args:
            count: Number of items to return.

        Returns:
            List of top issues with route and rationale.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        # Get all shaped/ready issues
        candidates = await self._linear_client.list_candidates()

        # Triage and score them
        scored_items: list[tuple[float, LinearIssue, TriageResult]] = []
        for issue in candidates:
            triage_result = self.core.triage(issue)
            if triage_result.is_relevant:
                scored_items.append((triage_result.priority_score, issue, triage_result))

        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Return top N
        results: list[dict[str, Any]] = []
        for score, issue, triage in scored_items[:count]:
            results.append({
                "issue_id": issue.id,
                "identifier": issue.identifier,
                "title": issue.title,
                "priority_score": score,
                "route": triage.route.value if triage.route else None,
                "rationale": triage.rationale,
                "url": issue.url,
            })

        return results

    async def inspect(self, issue_key: str) -> dict[str, Any]:
        """
        Inspect a specific issue.

        Slack command: /linear-agent inspect <issue-key>

        Args:
            issue_key: Issue ID or identifier (e.g., "MAP-123").

        Returns:
            Issue details with surfaces, size, route, and rationale.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        issue = await self._linear_client.get_issue(issue_key)
        if not issue:
            return {"error": f"Issue {issue_key} not found"}

        triage_result = self.core.triage(issue)

        return {
            "issue_id": issue.id,
            "identifier": issue.identifier,
            "title": issue.title,
            "description_preview": (issue.description or "")[:500],
            "surfaces": [s.value for s in triage_result.surfaces],
            "size": triage_result.size.value if triage_result.size else None,
            "route": triage_result.route.value if triage_result.route else None,
            "status": triage_result.status.value,
            "priority_score": triage_result.priority_score,
            "rationale": triage_result.rationale,
            "lean_ticket": (
                triage_result.lean_ticket.to_markdown()
                if triage_result.lean_ticket else None
            ),
            "url": issue.url,
        }

    async def clean_project(self, project_key: str) -> dict[str, Any]:
        """
        Clean and prioritize all issues in a project.

        Slack command: /linear-agent clean-project <project-key>

        Args:
            project_key: Project ID.

        Returns:
            Summary of cleaned issues.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        # Get project issues
        candidates = await self._linear_client.list_candidates()
        project_issues = [i for i in candidates if i.project_id == project_key]

        cleaned = 0
        prioritized = 0

        for issue in project_issues:
            triage_result = self.core.triage(issue)

            if triage_result.lean_ticket:
                await self._update_issue_from_triage(issue, triage_result)
                cleaned += 1

            if triage_result.priority_score > 0:
                prioritized += 1

        return {
            "project_id": project_key,
            "issues_found": len(project_issues),
            "issues_cleaned": cleaned,
            "issues_prioritized": prioritized,
        }

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _update_issue_from_triage(
        self,
        issue: LinearIssue,
        triage: TriageResult,
    ) -> None:
        """Update a Linear issue based on triage results."""
        if not self._linear_client:
            return

        # Update description to Lean format
        new_description = None
        if triage.lean_ticket:
            new_description = triage.lean_ticket.to_markdown()

        # Add rationale as comment
        if triage.rationale:
            comment = f"**Agent Rationale:** {triage.rationale}"
            await self._linear_client.comment_issue(issue.id, comment)

        # Update the issue
        if new_description:
            await self._linear_client.update_issue(
                issue.id,
                description=new_description,
            )

        logger.info(f"Updated issue {issue.identifier} from triage")

    async def _log_self_improvement(
        self,
        input_summary: str,
        decision_made: str,
        why_wrong: str,
        suggested_adjustment: str,
        severity: str = "low",
        original_issue_id: str | None = None,
    ) -> None:
        """Log a self-improvement issue."""
        if not self._linear_client or not self.config.log_improvements:
            return

        ticket = self.core.create_improvement_ticket(
            input_summary=input_summary,
            decision_made=decision_made,
            why_wrong=why_wrong,
            suggested_adjustment=suggested_adjustment,
            severity=severity,
            original_issue_id=original_issue_id,
        )

        # Would create issue in improvements project
        # await self._linear_client.create_improvement_issue(...)
        logger.warning(f"Self-improvement logged: {ticket.why_wrong}")

    # =========================================================================
    # Copilot Integration
    # =========================================================================

    async def prepare_copilot_task(
        self,
        issue_id: str,
    ) -> dict[str, Any]:
        """
        Prepare a task brief for Copilot agent.

        Used when route=copilot-agent.

        Returns:
            Copilot brief with problem, outcome, repos, constraints.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        issue = await self._linear_client.get_issue(issue_id)
        if not issue:
            return {"error": f"Issue {issue_id} not found"}

        triage = self.core.triage(issue)
        routing = self.core.decide_route(issue, triage.size, triage.surfaces)

        if routing.route != ExecutionRoute.COPILOT_AGENT:
            return {
                "warning": f"Issue routed to {routing.route.value}, not copilot-agent",
                "route": routing.route.value,
            }

        if routing.copilot_brief:
            return {
                "brief": routing.copilot_brief.to_prompt(),
                "linear_issue_id": issue.id,
                "linear_issue_url": issue.url,
            }

        return {"error": "Could not generate Copilot brief"}

    async def prepare_chat_prompt(
        self,
        issue_id: str,
    ) -> dict[str, Any]:
        """
        Prepare a prompt snippet for Copilot Chat.

        Used when route=copilot-chat.

        Returns:
            Chat prompt snippet for pasting into Copilot Chat.
        """
        if not self._linear_client:
            raise RuntimeError("Agent not initialized. Use 'async with' context.")

        issue = await self._linear_client.get_issue(issue_id)
        if not issue:
            return {"error": f"Issue {issue_id} not found"}

        triage = self.core.triage(issue)
        routing = self.core.decide_route(issue, triage.size, triage.surfaces)

        if routing.route != ExecutionRoute.COPILOT_CHAT:
            return {
                "warning": f"Issue routed to {routing.route.value}, not copilot-chat",
                "route": routing.route.value,
            }

        if routing.chat_snippet:
            return {
                "prompt": routing.chat_snippet.to_prompt(),
                "linear_issue_id": issue.id,
                "linear_issue_url": issue.url,
            }

        return {"error": "Could not generate Chat prompt"}


# =========================================================================
# ADK Tool Definitions (for Vertex AI Agent Engine)
# =========================================================================

# These would be defined using Google ADK decorators
# Example structure for reference:
#
# from google.adk import tool
#
# @tool
# async def triage_issues(project_id: str | None = None) -> list[dict]:
#     """Triage all candidate issues in Linear."""
#     async with LinearProductManagementAgent() as agent:
#         return await agent.triage(project_id)
#
# @tool
# async def get_next_items(count: int = 5) -> list[dict]:
#     """Get top recommended issues to work on."""
#     async with LinearProductManagementAgent() as agent:
#         return await agent.next_items(count)
#
# @tool
# async def inspect_issue(issue_key: str) -> dict:
#     """Inspect a specific Linear issue."""
#     async with LinearProductManagementAgent() as agent:
#         return await agent.inspect(issue_key)
#
# @tool
# async def clean_project(project_key: str) -> dict:
#     """Clean and prioritize all issues in a project."""
#     async with LinearProductManagementAgent() as agent:
#         return await agent.clean_project(project_key)


def create_agent() -> LinearProductManagementAgent:
    """Factory function for creating the agent."""
    return LinearProductManagementAgent()
