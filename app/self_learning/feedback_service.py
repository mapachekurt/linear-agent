"""
This module contains the service for generating feedback tickets in Linear when an agent
action fails.
"""
from app.self_learning.logging_service import LoggingService
from app.issue_management.service import IssueManagementService
from app.models.agent import ActionLog

class FeedbackService:
    def __init__(
        self,
        logging_service: LoggingService,
        issue_management_service: IssueManagementService
    ):
        self.logging_service = logging_service
        self.issue_management_service = issue_management_service

    async def record_action(self, log: ActionLog):
        """Records an agent action and creates a feedback ticket if it failed."""
        self.logging_service.log_action(log)

        if not log.success:
            title = f"Agent Action Failed: {log.action}"
            description = (
                f"**Agent:** {log.agent_id}\n"
                f"**Action:** {log.action}\n"
                f"**Parameters:** {log.parameters}\n"
                f"**Error:** {log.error_message}\n"
                f"**Context:** {log.context}"
            )
            await self.issue_management_service.create_issue(title, description)

# Example usage:
# logger = LoggingService()
# issue_service = IssueManagementService()
# feedback_service = FeedbackService(logger, issue_service)
#
# failed_log = ActionLog(
#     agent_id="agent-1",
#     action="update_issue_status",
#     parameters={"issue_id": "LIN-123", "new_status": "Done"},
#     success=False,
#     error_message="API rate limit exceeded"
# )
# await feedback_service.record_action(failed_log)
