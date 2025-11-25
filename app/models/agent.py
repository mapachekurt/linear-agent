from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class Agent(BaseModel):
    """Represents an autonomous agent."""
    id: str
    name: str
    api_key: str
    quota: int
    remaining_quota: int
    status: str # "active", "inactive", "error"

import datetime as dt

class ActionLog(BaseModel):
    """Represents a log of an agent's action."""
    timestamp: datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))
    agent_id: str
    action: str
    parameters: Optional[Dict[str, Any]] = None
    success: bool
    error_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
