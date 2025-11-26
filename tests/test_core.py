"""Core logic scenario tests for the Mapache Linear agent."""
from __future__ import annotations

import pytest

from agents.linear_agent.core import Issue, choose_route, classify_surfaces, estimate_size, leanify_issue, prioritize_issue


def test_bloated_solutions_ticket_is_shaped_and_routed() -> None:
    issue = Issue(
        title="Revamp onboarding for mapache.solutions",
        description=(
            "Long-form brainstorm about onboarding with many paragraphs that need to be shaped.\n"
            "Currently unclear success metrics but mentions customers and GUI improvements."
        ),
        labels=["customer"],
    )

    surface = classify_surfaces(issue)
    assert surface == {"solutions"}

    assert estimate_size(issue) == "medium"

    lean = leanify_issue(issue)
    assert "Problem:" in lean and "Acceptance:" in lean

    assert choose_route(issue) == "route:copilot-chat"


def test_bridge_project_gets_higher_priority_and_agent_route() -> None:
    bridge_issue = Issue(
        title="Promote GUI to MCP-GUI bridge",
        description="Bridge existing solutions GUI into mapache.app via MCP GUI surfaces.",
        labels=["bridge", "epic"],
        linked_repos=["solutions-gui", "app-shell"],
    )
    baseline_solutions = Issue(
        title="Minor solutions ticket",
        description="Small cleanup for mapache.solutions UI.",
        labels=["solutions"],
    )

    bridge_surface = classify_surfaces(bridge_issue)
    assert "bridge" in bridge_surface

    assert estimate_size(bridge_issue) == "large"
    assert choose_route(bridge_issue) == "route:copilot-agent"

    bridge_priority = prioritize_issue(bridge_issue, context={})
    baseline_priority = prioritize_issue(baseline_solutions, context={})
    assert bridge_priority < baseline_priority


def test_opportunity_agent_high_signal_idea_is_shaped() -> None:
    idea = Issue(
        title="Opportunity: orchestrate app flows",
        description="High-signal idea to improve mapache.app orchestration with MCP-GUI reuse.",
        labels=["opportunity"],
        source="opportunity-agent",
    )

    surface = classify_surfaces(idea)
    assert "app" in surface

    lean = leanify_issue(idea)
    assert "Status: shaped" in lean

    priority = prioritize_issue(idea, context={})
    assert 0 < priority < 20


def test_low_signal_idea_is_parked() -> None:
    idea = Issue(
        title="Random idea unrelated to Mapache",
        description="Maybe we should open a coffee shop.",
        labels=["idea"],
    )

    surface = classify_surfaces(idea)
    assert surface == set()

    lean = leanify_issue(idea)
    assert "Status: parked" in lean or "discarded" in lean.lower()

    priority = prioritize_issue(idea, context={})
    assert priority >= 90


def test_misrouted_large_work_triggers_self_improvement_flag() -> None:
    issue = Issue(
        title="Massive refactor request",
        description="Large refactor across multiple services with unclear scope.",
        labels=["large", "support"],
    )

    route = choose_route(issue)
    assert route == "route:copilot-chat"
    assert issue.metadata.get("needs_self_improvement") is True
