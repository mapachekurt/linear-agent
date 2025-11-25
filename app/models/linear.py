from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class LinearIssue(BaseModel):
    """Represents a Linear issue."""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    creator: str
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LinearWebhookPayload(BaseModel):
    """Represents the payload of a Linear webhook."""
    action: str
    data: LinearIssue
    updated_from: Optional[dict] = None
    url: str
    type: str
    created_at: datetime
