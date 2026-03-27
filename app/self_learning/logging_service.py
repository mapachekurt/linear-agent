"""
This module contains the service for logging agent actions to a persistent JSONL file.
"""
import json
from app.models.agent import ActionLog
from datetime import datetime

class LoggingService:
    def __init__(self, log_file: str = "agent_actions.jsonl"):
        self.log_file = log_file

    def _datetime_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def log_action(self, log: ActionLog):
        """Logs an agent action to a JSONL file."""
        try:
            log_dict = log.model_dump()
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_dict, default=self._datetime_serializer) + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

# Example usage:
# logger = LoggingService()
# log_entry = ActionLog(
#     agent_id="agent-1",
#     action="accept_issue",
#     parameters={"issue_id": "LIN-123"},
#     success=True
# )
# logger.log_action(log_entry)
