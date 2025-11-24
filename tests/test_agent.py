"""Unit tests for the Linear agent components."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from linear_agent.backoff import backoff_delays
from linear_agent.config import AgentSettings, GitHubSettings, LinearSettings
from linear_agent.github_integration import GitHubIntegration
from linear_agent.health import HealthMonitor
from linear_agent.linear_client import LinearClient
from linear_agent.logging_utils import LogContext
from linear_agent.orchestrator import AgentOrchestrator
from linear_agent.self_learning import SelfLearningRecorder
from linear_agent.storage import AuditEntry, FileStorage


class FakeResponse:
    def __init__(self, payload: dict | None = None):
        self._payload = payload or {"ok": True}

    def raise_for_status(self) -> None:  # pragma: no cover - trivial
        return None

    def json(self) -> Any:  # pragma: no cover - trivial
        return self._payload


class FakeLinearSession:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url: str, json: dict, headers: dict) -> FakeResponse:  # type: ignore[override]
        self.calls.append({"url": url, "json": json, "headers": headers})
        issue = {
            "id": "ISSUE-1",
            "title": json["variables"]["input"]["title"],
            "description": json["variables"]["input"].get("description", ""),
            "state": {"name": "Triaged"},
            "team": {"key": "ENG"},
        }
        if "issueCreate" in json["query"]:
            return FakeResponse({"data": {"issueCreate": {"issue": issue}}})
        return FakeResponse({"data": {"issueUpdate": {"issue": issue}}})


class FakeGitHubSession:
    def __init__(self) -> None:
        self.patches: list[dict] = []
        self.posts: list[dict] = []

    def post(self, url: str, json: dict, headers: dict) -> FakeResponse:  # type: ignore[override]
        self.posts.append({"url": url, "json": json, "headers": headers})
        return FakeResponse()

    def patch(self, url: str, json: dict, headers: dict) -> FakeResponse:  # type: ignore[override]
        self.patches.append({"url": url, "json": json, "headers": headers})
        return FakeResponse()


def temp_storage(tmp_path: Path) -> FileStorage:
    settings = AgentSettings(
        linear=LinearSettings(api_key="linear-key"),
        github=GitHubSettings(token="gh-token"),
    ).storage
    settings.audit_log_path = tmp_path / "audit.jsonl"  # type: ignore[assignment]
    settings.state_path = tmp_path / "state.json"  # type: ignore[assignment]
    return FileStorage(settings)


def test_backoff_delays_are_exponential() -> None:
    delays = list(backoff_delays(policy=LinearSettings(api_key="x").backoff, attempts=4))
    assert delays[:3] == sorted(delays[:3])
    assert delays[3] <= LinearSettings(api_key="x").backoff.max_delay


def test_storage_roundtrip(tmp_path: Path) -> None:
    storage = temp_storage(tmp_path)
    entries = [AuditEntry(event="alpha", details={"outcome": "success"})]
    storage.append_audit_entries(entries)
    loaded = storage.load_audit_entries()
    assert loaded == entries
    storage.save_state({"counter": 1})
    assert storage.load_state()["counter"] == 1


def test_orchestrator_creates_issue_and_links_pr(tmp_path: Path) -> None:
    storage = temp_storage(tmp_path)
    recorder = SelfLearningRecorder(storage)
    linear_session = FakeLinearSession()
    github_session = FakeGitHubSession()
    settings = AgentSettings(
        linear=LinearSettings(api_key="linear-key"),
        github=GitHubSettings(token="gh-token", default_repo="example/repo"),
    )
    linear_client = LinearClient(settings.linear, linear_session)
    github_client = GitHubIntegration(settings.github, github_session)
    orchestrator = AgentOrchestrator(
        settings=settings,
        linear_client=linear_client,
        github=github_client,
        learning=recorder,
        health_monitor=HealthMonitor(quota_limit=5),
    )

    result = orchestrator.create_issue_and_link_pr(
        team_id="team-1", title="Bug", description="Something broke", repo="example/repo", pull_number=1
    )

    assert result["status"] == "linked"
    assert linear_session.calls
    assert github_session.patches


def test_webhook_validation_records_failures(tmp_path: Path) -> None:
    storage = temp_storage(tmp_path)
    recorder = SelfLearningRecorder(storage)
    orchestrator = AgentOrchestrator(
        settings=AgentSettings(
            linear=LinearSettings(api_key="linear-key", webhook_secret="secret"),
            github=GitHubSettings(token="gh-token"),
        ),
        linear_client=LinearClient(LinearSettings(api_key="linear-key", webhook_secret="secret"), FakeLinearSession()),
        github=GitHubIntegration(GitHubSettings(token="gh-token"), FakeGitHubSession()),
        learning=recorder,
        health_monitor=HealthMonitor(quota_limit=1),
    )

    response = orchestrator.handle_webhook(payload={"type": "issue"}, signature=None)
    assert response["status"] == "rejected"
    entries = storage.load_audit_entries()
    assert any(entry.details.get("outcome") == "failure" for entry in entries)


def test_generate_improvement_suggestions(tmp_path: Path) -> None:
    storage = temp_storage(tmp_path)
    recorder = SelfLearningRecorder(storage)
    recorder.record_failure("transition", {"outcome": "failure"})
    orchestrator = AgentOrchestrator(
        settings=AgentSettings(
            linear=LinearSettings(api_key="linear-key"), github=GitHubSettings(token="gh-token")
        ),
        linear_client=LinearClient(LinearSettings(api_key="linear-key"), FakeLinearSession()),
        github=GitHubIntegration(GitHubSettings(token="gh-token"), FakeGitHubSession()),
        learning=recorder,
    )

    suggestions = recorder.emit_suggestions(logger=orchestrator.logger, context=LogContext())
    assert suggestions
    assert suggestions[0].summary.startswith("Stabilize action")
