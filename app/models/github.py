from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GitHubUser(BaseModel):
    login: str
    id: int
    avatar_url: str

class GitHubPullRequest(BaseModel):
    id: int
    number: int
    title: str
    user: GitHubUser
    state: str # "open", "closed", "merged"
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    body: Optional[str] = None

class GitHubBranch(BaseModel):
    ref: str

class GitHubWebhookPayload(BaseModel):
    action: str
    repository: dict
    sender: GitHubUser
    pull_request: Optional[GitHubPullRequest] = None
