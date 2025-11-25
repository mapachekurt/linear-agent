import pytest
import respx
import hmac
import hashlib
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from unittest.mock import patch
from app.main import app
import json

# Dummy secrets for testing
GITHUB_SECRET = "test_github_secret"
LINEAR_SECRET = "test_linear_secret"

def generate_test_private_key() -> str:
    """Generates a dummy RSA private key for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", generate_test_private_key())
    monkeypatch.setenv("GITHUB_INSTALLATION_ID", "67890")
    monkeypatch.setenv("LINEAR_API_KEY", "test_linear_key")
    monkeypatch.setenv("LINEAR_TEAM_ID", "test_team_id")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", GITHUB_SECRET)
    monkeypatch.setenv("LINEAR_WEBHOOK_SECRET", LINEAR_SECRET)
    monkeypatch.setenv("LINEAR_DONE_STATE_ID", "done-id")

    agents_config = [{"id": "test-agent", "name": "Test Agent", "api_key": "key", "quota": 100, "remaining_quota": 100, "status": "active"}]
    monkeypatch.setenv("AGENTS_CONFIG", json.dumps(agents_config))

    auth_router = respx.mock(base_url="https://api.github.com")
    auth_router.post("/app/installations/67890/access_tokens").respond(201, json={"token": "test_github_token"})

    with auth_router:
        with TestClient(app) as c:
            yield c

def get_github_signature(payload: bytes) -> str:
    return "sha256=" + hmac.new(GITHUB_SECRET.encode(), payload, hashlib.sha256).hexdigest()

def get_linear_signature(payload: bytes) -> str:
    return hmac.new(LINEAR_SECRET.encode(), payload, hashlib.sha256).hexdigest()

@patch("app.issue_management.service.IssueManagementService.accept_issue")
@patch("app.issue_management.service.IssueManagementService.analyze_issue")
def test_linear_webhook_create(mock_analyze, mock_accept, client):
    payload = {
        "action": "create", "type": "Issue", "created_at": "2023-01-01T12:00:00Z",
        "data": {
            "id": "123", "title": "Test Issue", "status": "Todo", "priority": "High",
            "creator": "Test User", "created_at": "2023-01-01T12:00:00Z", "updated_at": "2023-01-01T12:00:00Z",
        },
        "url": "http://example.com",
    }
    payload_bytes = json.dumps(payload).encode()
    headers = {"Linear-Signature": get_linear_signature(payload_bytes)}
    response = client.post("/webhooks/linear", content=payload_bytes, headers=headers)
    assert response.status_code == 200

@patch("app.github_sync.service.GitHubSyncService.link_pr_to_issue")
def test_github_webhook_pr(mock_link_pr, client):
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 1, "number": 1, "title": "LIN-123 Fix bug",
            "user": {"login": "testuser", "id": 1, "avatar_url": ""}, "state": "open",
            "created_at": "2023-01-01T12:00:00Z", "updated_at": "2023-01-01T12:00:00Z", "body": "Closes LIN-123",
        },
        "repository": {"name": "test-repo", "html_url": "https://github.com/test/repo"},
        "sender": {"login": "testuser", "id": 1, "avatar_url": ""}
    }
    payload_bytes = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": get_github_signature(payload_bytes)}
    response = client.post("/webhooks/github", content=payload_bytes, headers=headers)
    assert response.status_code == 200

def test_health_check(client):
    """Tests the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
