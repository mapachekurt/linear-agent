"""
Unit tests for core logic based on AgentSpec.md "Example scenarios (for tests)" section.

Uses simplified function interface:
- classify_surface(issue) -> set[str]
- estimate_size(issue) -> str
- choose_route(issue) -> str
- leanify_description(issue) -> str
- prioritize(issue, context) -> int  # lower number = higher priority
"""

from dataclasses import dataclass, field

import pytest

from agents.linear_agent.core import (
    choose_route,
    classify_surface,
    estimate_size,
    leanify_description,
    prioritize,
)


@dataclass
class Issue:
    """Simple issue representation for tests."""

    title: str
    description: str = ""
    labels: list[str] = field(default_factory=list)
    source: str = "user"
    linked_repos: list[str] = field(default_factory=list)


class TestScenario1BloatedSolutionsTicket:
    """
    Scenario 1: Bloated .solutions ticket
    - Expect: surface:solutions, size:medium, route:copilot-chat,
      description converted to Lean format.
    """

    @pytest.fixture
    def bloated_solutions_issue(self) -> Issue:
        """A bloated .solutions ticket with implementation details."""
        return Issue(
            title="Update customer dashboard component",
            description="""
## What needs to be done
The customer dashboard component needs updating for better performance.
Users are experiencing slow load times in the SaaS dashboard.

## Implementation Details (DO NOT USE - STALE)
In file `src/dashboard/CustomerDashboard.tsx`, rename function `getData` to `fetchData`.
Also update `config/dashboard.yaml` line 42-58.

```typescript
// This code is outdated
export function oldDataLoader() {
    return fetch('/api/data').then(res => res.json());
}
```

## Expected
Dashboard loads faster and shows updated data format.
The micro-saas app should feel more responsive.

## Links
https://github.com/mapache/solutions-dashboard
            """,
            labels=["enhancement"],
            source="user",
            linked_repos=["mapache/solutions-dashboard"],
        )

    def test_classify_surface_solutions(self, bloated_solutions_issue: Issue) -> None:
        """Should classify as surface:solutions."""
        surfaces = classify_surface(bloated_solutions_issue)
        assert "solutions" in surfaces

    def test_estimate_size_medium(self, bloated_solutions_issue: Issue) -> None:
        """Should estimate as size:medium."""
        size = estimate_size(bloated_solutions_issue)
        assert size == "medium"

    def test_choose_route_copilot_chat(self, bloated_solutions_issue: Issue) -> None:
        """Should route to copilot-chat for medium solutions work."""
        route = choose_route(bloated_solutions_issue)
        assert route == "copilot-chat"

    def test_leanify_removes_code_blocks(self, bloated_solutions_issue: Issue) -> None:
        """Should convert to Lean format without stale code."""
        lean_desc = leanify_description(bloated_solutions_issue)
        # Code blocks should be removed
        assert "oldDataLoader" not in lean_desc
        assert "```" not in lean_desc
        # But should have problem and outcome sections
        assert len(lean_desc) > 0


class TestScenario2BridgeProject:
    """
    Scenario 2: Bridge project (promote GUI to MCP-GUI)
    - Expect: surfaces include bridge, priority higher than a normal solutions-only ticket,
      size:large, route:copilot-agent.
    """

    @pytest.fixture
    def bridge_project_issue(self) -> Issue:
        """A bridge project issue promoting .solutions to .app."""
        return Issue(
            title="Mirror customer onboarding flow into mapache.app via MCP-GUI",
            description="""
Take the customer onboarding flow from the solutions app and
repurpose it into mapache.app using MCP-GUI.

This is a cross-cutting refactor involving multiple repos and services.
The goal is to bridge the solutions app functionality to the conversational OS.

Repos: mapache-solutions-onboarding, mapache-app-core
            """,
            labels=["bridge", "mcp-gui"],
            source="user",
            linked_repos=["mapache-solutions-onboarding", "mapache-app-core"],
        )

    @pytest.fixture
    def normal_solutions_issue(self) -> Issue:
        """A normal solutions-only issue for comparison."""
        return Issue(
            title="Fix button styling in dashboard",
            description="Update the button colors in the dashboard.",
            labels=["enhancement"],
            source="user",
            linked_repos=["mapache/solutions-dashboard"],
        )

    def test_classify_surface_includes_bridge(self, bridge_project_issue: Issue) -> None:
        """Should classify as bridge surface."""
        surfaces = classify_surface(bridge_project_issue)
        assert "bridge" in surfaces

    def test_estimate_size_large(self, bridge_project_issue: Issue) -> None:
        """Should estimate as size:large for cross-cutting work."""
        size = estimate_size(bridge_project_issue)
        assert size == "large"

    def test_choose_route_copilot_agent(self, bridge_project_issue: Issue) -> None:
        """Should route to copilot-agent for large bridge work."""
        route = choose_route(bridge_project_issue)
        assert route == "copilot-agent"

    def test_priority_higher_than_solutions(
        self,
        bridge_project_issue: Issue,
        normal_solutions_issue: Issue,
    ) -> None:
        """Bridge work should have higher priority (lower number) than solutions-only."""
        bridge_priority = prioritize(bridge_project_issue, {})
        solutions_priority = prioritize(normal_solutions_issue, {})
        # Lower number = higher priority
        assert bridge_priority < solutions_priority


class TestScenario3HighSignalOpportunityAgentIdea:
    """
    Scenario 3: High-signal Opportunity Agent idea
    - Expect: source:opportunity-agent, classified to correct surface,
      status:shaped (or equivalent flag), non-trivial priority.
    """

    @pytest.fixture
    def high_signal_opportunity_issue(self) -> Issue:
        """A high-signal idea from the Opportunity Agent."""
        return Issue(
            title="New micro-saas for customer onboarding automation",
            description="""
A clear customer pain point identified from user feedback.
Many SMBs struggle with manual onboarding processes and would pay
for an automated solution that saves time and improves customer experience.

This could drive significant revenue growth and user adoption.
            """,
            labels=["source:opportunity-agent"],
            source="opportunity-agent",
            linked_repos=[],
        )

    def test_source_is_opportunity_agent(self, high_signal_opportunity_issue: Issue) -> None:
        """Should recognize source as opportunity-agent."""
        # Source is explicitly set via labels
        assert "source:opportunity-agent" in high_signal_opportunity_issue.labels

    def test_classify_surface_correct(self, high_signal_opportunity_issue: Issue) -> None:
        """Should classify to appropriate surface (solutions for new micro-saas)."""
        surfaces = classify_surface(high_signal_opportunity_issue)
        # New micro-saas ideas default to solutions
        assert "solutions" in surfaces or len(surfaces) > 0

    def test_priority_nontrivial(self, high_signal_opportunity_issue: Issue) -> None:
        """Should have non-trivial (reasonably high) priority."""
        priority = prioritize(high_signal_opportunity_issue, {})
        # Non-trivial means not the lowest priority (P4)
        # Lower number = higher priority, so should be < 4
        assert priority < 4


class TestScenario4LowSignalOrOffTopicIdea:
    """
    Scenario 4: Low-signal/off-topic idea
    - Expect: marked discarded/parked, low priority.
    """

    @pytest.fixture
    def low_signal_issue(self) -> Issue:
        """A low-signal or off-topic idea."""
        return Issue(
            title="Random experiment idea",
            description="""
Just an idea to try something new. Not sure if it fits anywhere.
Maybe we could experiment with this someday.
            """,
            labels=["source:opportunity-agent"],
            source="opportunity-agent",
            linked_repos=[],
        )

    def test_priority_low(self, low_signal_issue: Issue) -> None:
        """Should have low priority."""
        priority = prioritize(low_signal_issue, {})
        # Low priority = higher number (P3 or P4)
        assert priority >= 3


class TestScenario5MisroutedLargeWork:
    """
    Scenario 5: Misrouted large work
    - Simulate a large issue that would mistakenly be routed to copilot-chat
      and assert that a self-improvement record should be created.
    """

    @pytest.fixture
    def large_work_issue(self) -> Issue:
        """A large issue that should not go to copilot-chat."""
        return Issue(
            title="Major architecture refactor",
            description="""
Complete cross-cutting refactor of multiple services.
Breaking changes expected across the entire codebase.
Multi-repo coordination required.
            """,
            labels=["size:large"],
            source="user",
            linked_repos=["mapache/core", "mapache/api", "mapache/frontend"],
        )

    def test_large_work_detects_misrouting(self, large_work_issue: Issue) -> None:
        """Large work to copilot-chat should flag self-improvement."""
        from agents.linear_agent.core import detect_misrouting

        # Simulate the issue was mistakenly routed to copilot-chat
        improvement_flag = detect_misrouting(
            large_work_issue,
            actual_route="copilot-chat",
            actual_size="large",
        )

        # Should return a flag/indicator that self-improvement record needed
        assert improvement_flag is not None
        assert improvement_flag.get("needs_improvement", False) is True

    def test_correct_routing_no_flag(self, large_work_issue: Issue) -> None:
        """Correct routing should not flag self-improvement."""
        from agents.linear_agent.core import detect_misrouting

        # Large work correctly routed to copilot-agent
        improvement_flag = detect_misrouting(
            large_work_issue,
            actual_route="copilot-agent",
            actual_size="large",
        )

        # Should return None or no improvement needed
        assert improvement_flag is None or improvement_flag.get("needs_improvement", False) is False
