
"""Tests for the Mapache Linear Product Management Agent."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest

from agents.linear_agent import (
    LeanTicketShaper,
    LinearConnector,
    LinearProductAgent,
    TicketClassifier,
    TicketPrioritizer,
    RoutingDecider,
    TicketContext,
    TicketSource,
)
from agents.linear_agent.models import LeanTicket
from agents.linear_agent.shaping import RawTicket


@pytest.fixture()
def webhook_payload() -> dict[str, Any]:
    return {
        "data": {
            "issue": {
                "title": "Improve mapache.app onboarding",
                "description": "Problem: onboarding friction\nImpact: drop-offs\n- track completion\n- link to GUI",
                "creator": {"name": "Jess"},
                "assignee": {"name": "Sam"},
            }
        },
        "slackThread": "T123",
    }


def test_shaper_creates_crisp_lean_ticket(webhook_payload: dict[str, Any]) -> None:
    raw = RawTicket(
        title=webhook_payload["data"]["issue"]["title"],
        description=webhook_payload["data"]["issue"]["description"],
    )
    context = TicketContext(source=TicketSource.CUSTOMER, surface_hint=None, size_hint=None)
    lean = LeanTicketShaper().shape(raw, context)
    assert lean.title == "Improve mapache.app onboarding"
    assert lean.acceptance_criteria
    assert lean.is_crisp()


def test_classifier_prefers_surface_hints() -> None:
    lean = LeanTicket(
        title="Bridge MCP GUI",
        problem="Need MCP bridge",
        impact="Unblocks partners",
        scope="Bridge for GUIs",
        acceptance_criteria=["Bridge works"],
    )
    classifier = TicketClassifier()
    context = TicketContext(source=TicketSource.INTERNAL, surface_hint=None, size_hint=None)
    classification = classifier.classify(lean, context)
    assert classification.surface.value in {"bridge", "solutions", "app"}
    hinted_context = TicketContext(source=TicketSource.INTERNAL, surface_hint=classification.surface, size_hint=None)
    hinted = classifier.classify(lean, hinted_context)
    assert hinted.confidence > classification.confidence


def test_prioritizer_emphasizes_solutions() -> None:
    lean = LeanTicket(
        title="GUI fix",
        problem="Button broken",
        impact="Blocks revenue",
        scope="Single button",
        acceptance_criteria=["Button works"],
    )
    classifier = TicketClassifier()
    context = TicketContext(source=TicketSource.CUSTOMER, surface_hint=None, size_hint=None)
    classification = classifier.classify(lean, context)
    score = TicketPrioritizer().score(classification, lean)
    assert score.priority_score >= 3.0


def test_router_directs_small_crisp_work_to_copilot_agent() -> None:
    lean = LeanTicket(
        title="GUI fix",
        problem="Button broken",
        impact="Blocks revenue",
        scope="Single button",
        acceptance_criteria=["Button works"],
    )
    classification = TicketClassifier().classify(
        lean, TicketContext(source=TicketSource.INTERNAL, surface_hint=None, size_hint=None)
    )
    prioritized = TicketPrioritizer().score(classification, lean)
    routing = RoutingDecider().route(prioritized)
    assert routing.destination == "route:copilot-agent"


def test_orchestrator_builds_action_plan(webhook_payload: dict[str, Any]) -> None:
    connector = LinearConnector(webhook_secret=None)
    agent = LinearProductAgent(linear=connector, github=None)  # type: ignore[arg-type]
    plan = agent.process_webhook(payload=webhook_payload, signature=None)
    assert plan.routing.destination in {"route:copilot-agent", "route:copilot-chat", "route:manual"}
    assert plan.classification.surface.value
    assert plan.next_steps


def test_webhook_validation_rejects_wrong_signature(webhook_payload: dict[str, Any]) -> None:
    connector = LinearConnector(webhook_secret="secret")
    signature = "deadbeef"
    with pytest.raises(ValueError):
        if not connector.validate_webhook(webhook_payload, signature):
            raise ValueError("Invalid webhook")
        LinearProductAgent(linear=connector, github=None).process_webhook(
            payload=webhook_payload, signature=signature
        )  # type: ignore[arg-type]


def test_webhook_validation_accepts_correct_signature(webhook_payload: dict[str, Any]) -> None:
    connector = LinearConnector(webhook_secret="secret")
    body = json.dumps(webhook_payload, separators=(",", ":")).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert connector.validate_webhook(webhook_payload, signature)


def test_ready_status_routes_to_available_coding_agent() -> None:
    payload = {
        "data": {
            "issue": {
                "id": "ISS-123",
                "title": "Bridge MCP GUI for mapache.app",
                "description": "Problem: build bridge\nImpact: unblock MCP GUI\n- acceptance one\n- acceptance two",
                "status": "ready",
            }
        }
    }
    connector = LinearConnector(webhook_secret=None)
    agent = LinearProductAgent(linear=connector, github=None)  # type: ignore[arg-type]
    plan = agent.process_webhook(payload=payload, signature=None)
    assert plan.routing.destination == "route:copilot-agent"
    assert plan.routing.selected_agent is not None
