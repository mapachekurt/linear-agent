from fastapi import FastAPI, Request, Depends
from app.models.linear import LinearWebhookPayload
from app.models.github import GitHubWebhookPayload, GitHubBranch
from app.github_sync.auth import get_installation_access_token
from app.issue_management.service import IssueManagementService
from app.github_sync.service import GitHubSyncService
from app.self_learning.logging_service import LoggingService
from app.self_learning.feedback_service import FeedbackService
from app.agent_rotation.service import AgentRotationService
from app.config import AGENTS
from app.security import verify_github_signature, verify_linear_signature
from app.models.agent import ActionLog
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.github_token = await get_installation_access_token()
    app.state.github_client = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {app.state.github_token}"}
    )
    issue_service = IssueManagementService()
    logging_service = LoggingService()
    agent_rotation_service = AgentRotationService(AGENTS)
    app.state.issue_management_service = issue_service
    app.state.github_sync_service = GitHubSyncService(issue_service)
    app.state.feedback_service = FeedbackService(logging_service, issue_service)
    app.state.agent_rotation_service = agent_rotation_service
    yield
    # Shutdown
    await app.state.github_client.aclose()
    await app.state.issue_management_service.linear_client.aclose()

app = FastAPI(lifespan=lifespan)

# Dependency Getters
def get_issue_management_service(request: Request) -> IssueManagementService:
    return request.app.state.issue_management_service

def get_github_sync_service(request: Request) -> GitHubSyncService:
    return request.app.state.github_sync_service

def get_feedback_service(request: Request) -> FeedbackService:
    return request.app.state.feedback_service

def get_agent_rotation_service(request: Request) -> AgentRotationService:
    return request.app.state.agent_rotation_service

@app.get("/")
async def root():
    return {"message": "Linear Agent is running"}

@app.post("/webhooks/linear", dependencies=[Depends(verify_linear_signature)])
async def linear_webhook(
    payload: LinearWebhookPayload,
    service: IssueManagementService = Depends(get_issue_management_service),
    feedback: FeedbackService = Depends(get_feedback_service),
    rotation: AgentRotationService = Depends(get_agent_rotation_service)
):
    agent = rotation.get_active_agent()
    log = ActionLog(agent_id=agent.id, action=f"linear:{payload.action}", success=True)
    try:
        rotation.record_usage(agent.id)
        if payload.action == "create":
            await service.accept_issue(payload.data)
            await service.analyze_issue(payload.data)
        elif payload.action == "update":
            await service.monitor_issue(payload.data)
    except Exception as e:
        log.success = False
        log.error_message = str(e)
        rotation.report_error(agent.id)
        rotation.rotate_agent()
    await feedback.record_action(log)
    return {"status": "success"}

@app.post("/webhooks/github", dependencies=[Depends(verify_github_signature)])
async def github_webhook(
    payload: GitHubWebhookPayload,
    github_sync_service: GitHubSyncService = Depends(get_github_sync_service),
    feedback: FeedbackService = Depends(get_feedback_service),
    rotation: AgentRotationService = Depends(get_agent_rotation_service)
):
    agent = rotation.get_active_agent()
    log = ActionLog(agent_id=agent.id, action=f"github:{payload.action}", success=True)
    try:
        rotation.record_usage(agent.id)
        repo_url = payload.repository.get("html_url")
        if not repo_url:
            raise ValueError("Repository URL not found in payload.")

        if payload.pull_request:
            await github_sync_service.link_pr_to_issue(payload.pull_request, repo_url)
        elif payload.action == "create" and hasattr(payload, 'ref_type') and payload.ref_type == "branch":
            branch = GitHubBranch(ref=payload.ref)
            await github_sync_service.link_branch_to_issue(branch, repo_url)
    except Exception as e:
        log.success = False
        log.error_message = str(e)
        rotation.report_error(agent.id)
        rotation.rotate_agent()
    await feedback.record_action(log)
    return {"status": "success"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
