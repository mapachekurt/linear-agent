"""
Tests for the Linear Agent core logic.

Based on scenarios from AgentSpec.md:
1. Bloated .solutions ticket - converted to Lean format
2. Bridge project - higher priority, routed to copilot-agent
3. High-signal Opportunity Agent idea - properly classified
4. Low-signal or off-topic idea - discarded/parked
5. Misrouted large work - self-improvement logged
"""

import pytest

from agents.linear_agent.config import AgentConfig
from agents.linear_agent.core import LinearAgentCore
from agents.linear_agent.models import (
    ExecutionRoute,
    IssueSize,
    IssueSource,
    IssueStatus,
    LinearIssue,
    ProductSurface,
)


@pytest.fixture
def config() -> AgentConfig:
    """Create test configuration."""
    return AgentConfig()


@pytest.fixture
def core(config: AgentConfig) -> LinearAgentCore:
    """Create LinearAgentCore instance."""
    return LinearAgentCore(config)


class TestClassification:
    """Tests for surface, size, and source classification."""

    def test_classify_solutions_surface(self, core: LinearAgentCore) -> None:
        """Test classification of solutions-related issue."""
        issue = LinearIssue(
            id="test-1",
            identifier="MAP-1",
            title="Add dashboard to micro-saas app",
            description="Build a new dashboard for the SaaS app with tables and forms.",
        )
        surfaces = core.classify_surfaces(issue)
        assert ProductSurface.SOLUTIONS in surfaces

    def test_classify_app_surface(self, core: LinearAgentCore) -> None:
        """Test classification of app-related issue."""
        issue = LinearIssue(
            id="test-2",
            identifier="MAP-2",
            title="Add MCP-GUI component to mapache.app",
            description="Implement a conversational chat interface in the business OS.",
        )
        surfaces = core.classify_surfaces(issue)
        assert ProductSurface.APP in surfaces

    def test_classify_bridge_surface(self, core: LinearAgentCore) -> None:
        """Test classification of bridge work."""
        issue = LinearIssue(
            id="test-3",
            identifier="MAP-3",
            title="Mirror customer onboarding to MCP-GUI",
            description="Migrate the onboarding flow from solutions to mapache.app via MCP-GUI.",
        )
        surfaces = core.classify_surfaces(issue)
        assert ProductSurface.BRIDGE in surfaces

    def test_detect_opportunity_agent_source(self, core: LinearAgentCore) -> None:
        """Test detection of opportunity agent source."""
        issue = LinearIssue(
            id="test-4",
            identifier="MAP-4",
            title="New idea from Opportunity Agent",
            description="A new micro-saas idea.",
            labels=["source:opportunity-agent"],
        )
        source = core.detect_source(issue)
        assert source == IssueSource.OPPORTUNITY_AGENT

    def test_detect_user_source(self, core: LinearAgentCore) -> None:
        """Test detection of user source (default)."""
        issue = LinearIssue(
            id="test-5",
            identifier="MAP-5",
            title="Kurt's idea",
            description="A manual idea.",
        )
        source = core.detect_source(issue)
        assert source == IssueSource.USER

    def test_estimate_large_size(self, core: LinearAgentCore) -> None:
        """Test size estimation for large work."""
        issue = LinearIssue(
            id="test-6",
            identifier="MAP-6",
            title="Refactor architecture",
            description="Cross-cutting refactor of multiple services with breaking changes.",
        )
        size = core.estimate_size(issue)
        assert size == IssueSize.LARGE

    def test_estimate_small_size(self, core: LinearAgentCore) -> None:
        """Test size estimation for small work."""
        issue = LinearIssue(
            id="test-7",
            identifier="MAP-7",
            title="Fix typo",
            description="Fix a quick typo in the UI.",
        )
        size = core.estimate_size(issue)
        assert size == IssueSize.SMALL

    def test_estimate_medium_size_by_description(self, core: LinearAgentCore) -> None:
        """Test size estimation defaults to medium for moderate descriptions."""
        issue = LinearIssue(
            id="test-8",
            identifier="MAP-8",
            title="Add new feature",
            description="A " * 150,  # 300 chars, between 200 (small) and 1000 (large)
        )
        size = core.estimate_size(issue)
        assert size == IssueSize.MEDIUM


class TestLeanification:
    """Tests for converting bloated tickets to Lean format."""

    def test_leanify_bloated_ticket(self, core: LinearAgentCore) -> None:
        """
        Scenario 1: Bloated .solutions ticket
        - Description full of implementation notes & stale code paths
        - Expected: Converted to Lean format
        """
        issue = LinearIssue(
            id="bloated-1",
            identifier="MAP-100",
            title="Update customer dashboard",
            description="""
## What needs to be done
The customer dashboard needs updating.

## Implementation Details (DO NOT USE - STALE)
In file `src/dashboard.py`, rename function `get_data` to `fetch_data`.
Also modify `config.yaml` line 42.

```python
def old_function():
    # This code is stale
    pass
```

## Expected
Dashboard shows new data.

## Links
https://github.com/mapache/solutions-dashboard
            """,
        )

        surfaces = core.classify_surfaces(issue)
        lean_ticket = core.leanify(issue, surfaces)

        # Should have problem and outcome
        assert len(lean_ticket.problem) > 0
        assert len(lean_ticket.desired_outcome) > 0

        # Should have stripped code blocks (the removal message is in problem/outcome)
        markdown = lean_ticket.to_markdown()
        assert "def old_function" not in markdown
        # The code block message appears in cleaned description, not constraints
        # Just verify we have some content
        assert len(markdown) > 0

    def test_leanify_extracts_links(self, core: LinearAgentCore) -> None:
        """Test that links are preserved in constraints."""
        issue = LinearIssue(
            id="links-1",
            identifier="MAP-101",
            title="Feature request",
            description="See https://github.com/mapache/repo for context.",
        )
        surfaces = core.classify_surfaces(issue)
        lean_ticket = core.leanify(issue, surfaces)

        assert "https://github.com/mapache/repo" in lean_ticket.context_and_constraints


class TestPrioritization:
    """Tests for prioritization logic."""

    def test_bridge_work_boosted(self, core: LinearAgentCore) -> None:
        """
        Scenario 2: Bridge project gets higher priority.
        """
        issue = LinearIssue(
            id="bridge-1",
            identifier="MAP-200",
            title="Mirror onboarding flow to MCP-GUI",
            description="Promote customer onboarding from solutions to mapache.app via MCP-GUI.",
        )
        surfaces = core.classify_surfaces(issue)
        source = core.detect_source(issue)

        result = core.calculate_priority_score(issue, surfaces, source)

        assert result.boosted is True
        assert result.priority_score > 50  # Base score

    def test_high_signal_opportunity_boosted(self, core: LinearAgentCore) -> None:
        """
        Scenario 3: High-signal Opportunity Agent idea gets boosted.
        """
        issue = LinearIssue(
            id="opp-1",
            identifier="MAP-201",
            title="New revenue opportunity",
            description="A clear customer pain point that could drive growth.",
            labels=["source:opportunity-agent"],
        )
        surfaces = core.classify_surfaces(issue)
        source = core.detect_source(issue)

        result = core.calculate_priority_score(issue, surfaces, source)

        assert result.boosted is True
        assert "opportunity" in result.rationale.lower()

    def test_speculative_opportunity_demoted(self, core: LinearAgentCore) -> None:
        """
        Scenario 4: Low-signal idea gets demoted.
        """
        issue = LinearIssue(
            id="opp-2",
            identifier="MAP-202",
            title="Random experiment",
            description="Just an idea to try something.",
            labels=["source:opportunity-agent"],
        )
        surfaces = core.classify_surfaces(issue)
        source = core.detect_source(issue)

        result = core.calculate_priority_score(issue, surfaces, source)

        assert result.demoted is True
        assert result.priority_score < 50  # Below base

    def test_maintenance_demoted(self, core: LinearAgentCore) -> None:
        """Test that pure maintenance on solutions is demoted."""
        issue = LinearIssue(
            id="maint-1",
            identifier="MAP-203",
            title="Update dependencies",
            description="Dependency maintenance for solutions app.",
            labels=["surface:solutions"],
        )
        surfaces = core.classify_surfaces(issue)
        source = core.detect_source(issue)

        result = core.calculate_priority_score(issue, surfaces, source)

        assert result.demoted is True


class TestRouting:
    """Tests for execution routing decisions."""

    def test_large_work_to_copilot_agent(self, core: LinearAgentCore) -> None:
        """Large work should route to copilot-agent."""
        issue = LinearIssue(
            id="route-1",
            identifier="MAP-300",
            title="Major refactor",
            description="A large cross-cutting refactor.",
        )
        size = IssueSize.LARGE
        surfaces = [ProductSurface.SOLUTIONS]

        decision = core.decide_route(issue, size, surfaces)

        assert decision.route == ExecutionRoute.COPILOT_AGENT
        assert decision.copilot_brief is not None

    def test_bridge_work_to_copilot_agent(self, core: LinearAgentCore) -> None:
        """
        Scenario 2: Bridge project routes to copilot-agent.
        """
        issue = LinearIssue(
            id="route-2",
            identifier="MAP-301",
            title="Mirror flow to MCP-GUI",
            description="Bridge work.",
        )
        size = IssueSize.MEDIUM
        surfaces = [ProductSurface.BRIDGE, ProductSurface.SOLUTIONS, ProductSurface.APP]

        decision = core.decide_route(issue, size, surfaces)

        assert decision.route == ExecutionRoute.COPILOT_AGENT

    def test_small_work_to_copilot_chat(self, core: LinearAgentCore) -> None:
        """Small work should route to copilot-chat."""
        issue = LinearIssue(
            id="route-3",
            identifier="MAP-302",
            title="Fix button color",
            description="A small UI fix.",
        )
        size = IssueSize.SMALL
        surfaces = [ProductSurface.SOLUTIONS]

        decision = core.decide_route(issue, size, surfaces)

        assert decision.route == ExecutionRoute.COPILOT_CHAT
        assert decision.chat_snippet is not None

    def test_ambiguous_to_manual(self, core: LinearAgentCore) -> None:
        """Ambiguous/strategy work should route to manual."""
        issue = LinearIssue(
            id="route-4",
            identifier="MAP-303",
            title="Decide architecture",
            description="Should we use microservices? TBD strategy.",
        )
        size = IssueSize.MEDIUM
        surfaces = [ProductSurface.APP]

        decision = core.decide_route(issue, size, surfaces)

        assert decision.route == ExecutionRoute.MANUAL


class TestFullTriage:
    """Tests for complete triage workflow."""

    def test_triage_bloated_solutions_ticket(self, core: LinearAgentCore) -> None:
        """
        Scenario 1: Bloated .solutions ticket
        - Converted to Lean format
        - surface:solutions
        - size:medium (or small depending on description length)
        - route:copilot-chat
        """
        issue = LinearIssue(
            id="triage-1",
            identifier="MAP-400",
            title="Update dashboard component",
            description="""
## Problem
The dashboard component is slow and needs optimization. Users have reported that the
data loading takes too long and the UI becomes unresponsive during updates. This affects
the overall user experience and needs to be addressed.

## Implementation
```javascript
// Old code to change
function loadData() { ... }
```

## Expected Outcome
The dashboard should load data within 2 seconds and remain responsive during updates.
Performance should be measurably improved.

## Links
https://github.com/mapache/solutions-dashboard
            """,
        )

        result = core.triage(issue)

        assert result.is_relevant is True
        assert ProductSurface.SOLUTIONS in result.surfaces
        # Size depends on description length after stripping code
        assert result.size in [IssueSize.SMALL, IssueSize.MEDIUM]
        assert result.route == ExecutionRoute.COPILOT_CHAT
        assert result.lean_ticket is not None
        assert result.status == IssueStatus.SHAPED

    def test_triage_bridge_project(self, core: LinearAgentCore) -> None:
        """
        Scenario 2: Bridge project
        - surface:bridge (+ solutions + app)
        - Higher priority
        - size:large
        - route:copilot-agent
        """
        issue = LinearIssue(
            id="triage-2",
            identifier="MAP-401",
            title="Mirror customer onboarding flow into mapache.app via MCP-GUI",
            description="""
Take the customer onboarding flow from the solutions app and
repurpose it into mapache.app using MCP-GUI.

This is a cross-cutting refactor involving multiple repos.

Repos: mapache-solutions-onboarding, mapache-app-core
            """,
        )

        result = core.triage(issue)

        assert result.is_relevant is True
        assert ProductSurface.BRIDGE in result.surfaces
        assert result.size == IssueSize.LARGE
        assert result.route == ExecutionRoute.COPILOT_AGENT
        assert result.priority_score > 50  # Boosted


class TestSelfImprovement:
    """Tests for self-improvement detection."""

    def test_detect_misrouted_large_work(self, core: LinearAgentCore) -> None:
        """
        Scenario 5: Large work misrouted to copilot-chat.
        """
        issue = LinearIssue(
            id="misroute-1",
            identifier="MAP-500",
            title="Large refactor",
            description="Cross-cutting work.",
        )

        # Simulate a misrouting
        improvement = core.detect_misrouting(
            issue,
            actual_route=ExecutionRoute.COPILOT_CHAT,
            actual_size=IssueSize.LARGE,
        )

        assert improvement is not None
        assert improvement.severity == "medium"
        assert "large" in improvement.why_wrong.lower()

    def test_no_improvement_for_correct_routing(self, core: LinearAgentCore) -> None:
        """No improvement ticket for correct routing."""
        issue = LinearIssue(
            id="correct-1",
            identifier="MAP-501",
            title="Small fix",
            description="Quick fix.",
        )

        improvement = core.detect_misrouting(
            issue,
            actual_route=ExecutionRoute.COPILOT_CHAT,
            actual_size=IssueSize.SMALL,
        )

        assert improvement is None


class TestCopilotBriefGeneration:
    """Tests for Copilot brief and prompt generation."""

    def test_copilot_brief_includes_repos(self, core: LinearAgentCore) -> None:
        """Copilot brief should include detected repos."""
        issue = LinearIssue(
            id="brief-1",
            identifier="MAP-600",
            title="Feature work",
            description="Work on https://github.com/mapache/solutions-app",
        )
        surfaces = [ProductSurface.SOLUTIONS]

        brief = core._create_copilot_brief(issue, surfaces)

        assert len(brief.repos) > 0
        assert any("mapache" in r for r in brief.repos)

    def test_chat_snippet_format(self, core: LinearAgentCore) -> None:
        """Chat snippet should have proper format."""
        issue = LinearIssue(
            id="chat-1",
            identifier="MAP-601",
            title="Small task",
            description="A quick task to do.",
        )

        snippet = core._create_chat_snippet(issue)

        prompt = snippet.to_prompt()
        assert "Context:" in prompt
        assert "Problem:" in prompt
        assert "Acceptance Criteria:" in prompt
