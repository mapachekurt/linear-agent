"""
Core logic for the Linear Product Management Agent.

Contains:
- Classification (surface, size, source detection)
- Leanification (converting bloated tickets to Lean format)
- Prioritization (scoring and ranking issues)
- Routing (deciding execution path)
"""

import logging
import re
from datetime import datetime, timezone

from agents.linear_agent.config import AgentConfig
from agents.linear_agent.models import (
    ChatPromptSnippet,
    CopilotBrief,
    ExecutionRoute,
    IssueSize,
    IssueSource,
    IssueStatus,
    LeanTicket,
    LinearIssue,
    PrioritizationResult,
    ProductSurface,
    RoutingDecision,
    SelfImprovementTicket,
    TriageResult,
)

logger = logging.getLogger(__name__)


class LinearAgentCore:
    """
    Core logic for the Linear Product Management Agent.

    Pure business logic with no I/O - designed for testability.
    """

    def __init__(self, config: AgentConfig | None = None):
        """Initialize with configuration."""
        self.config = config or AgentConfig.from_env()

    # =========================================================================
    # Classification
    # =========================================================================

    def detect_source(self, issue: LinearIssue) -> IssueSource:
        """Detect the source of an issue based on labels or metadata."""
        labels_lower = [label.lower() for label in issue.labels]

        if self.config.labels.source_opportunity_agent.lower() in labels_lower:
            return IssueSource.OPPORTUNITY_AGENT
        if self.config.labels.source_system_migration.lower() in labels_lower:
            return IssueSource.SYSTEM_MIGRATION

        return IssueSource.USER

    def classify_surfaces(self, issue: LinearIssue) -> list[ProductSurface]:
        """
        Classify issue by product surface.

        Uses:
        - Title & description keywords
        - Linked repos patterns
        - Existing labels
        """
        surfaces: set[ProductSurface] = set()
        text = f"{issue.title} {issue.description or ''}".lower()
        labels_lower = [label.lower() for label in issue.labels]

        # Check existing labels first
        if self.config.labels.surface_bridge.lower() in labels_lower:
            surfaces.add(ProductSurface.BRIDGE)
        if self.config.labels.surface_app.lower() in labels_lower:
            surfaces.add(ProductSurface.APP)
        if self.config.labels.surface_solutions.lower() in labels_lower:
            surfaces.add(ProductSurface.SOLUTIONS)

        # Check keywords
        for keyword in self.config.keywords.bridge_keywords:
            if keyword.lower() in text:
                surfaces.add(ProductSurface.BRIDGE)
                break

        for keyword in self.config.keywords.app_keywords:
            if keyword.lower() in text:
                surfaces.add(ProductSurface.APP)
                break

        for keyword in self.config.keywords.solutions_keywords:
            if keyword.lower() in text:
                surfaces.add(ProductSurface.SOLUTIONS)
                break

        # Check repo patterns in description (links)
        if self.config.github.solutions_repo_pattern.lower() in text:
            surfaces.add(ProductSurface.SOLUTIONS)
        if self.config.github.app_repo_pattern.lower() in text:
            surfaces.add(ProductSurface.APP)

        # Default to solutions if nothing detected
        if not surfaces:
            surfaces.add(ProductSurface.SOLUTIONS)

        return list(surfaces)

    def estimate_size(self, issue: LinearIssue) -> IssueSize:
        """
        Estimate issue size for routing.

        Heuristic:
        - Single-file or localized → small
        - Multi-component but straightforward → medium
        - Cross-cutting, multiple services, redesign → large
        """
        text = f"{issue.title} {issue.description or ''}".lower()
        labels_lower = [label.lower() for label in issue.labels]

        # Check existing size labels
        if self.config.labels.size_large.lower() in labels_lower:
            return IssueSize.LARGE
        if self.config.labels.size_small.lower() in labels_lower:
            return IssueSize.SMALL
        if self.config.labels.size_medium.lower() in labels_lower:
            return IssueSize.MEDIUM

        # Check keywords for large work
        for keyword in self.config.keywords.large_work_keywords:
            if keyword.lower() in text:
                return IssueSize.LARGE

        # Check keywords for small work
        for keyword in self.config.keywords.small_work_keywords:
            if keyword.lower() in text:
                return IssueSize.SMALL

        # Default based on description length (rough heuristic)
        desc_len = len(issue.description or "")
        if desc_len < 200:
            return IssueSize.SMALL
        if desc_len > 1000:
            return IssueSize.LARGE

        return IssueSize.MEDIUM

    def check_relevance(self, issue: LinearIssue) -> tuple[bool, str]:
        """
        Check if an issue is relevant to Mapache.

        Returns: (is_relevant, reason)
        """
        text = f"{issue.title} {issue.description or ''}".lower()

        # Check for Mapache-related terms
        mapache_terms = ["mapache", "solutions", "app", "mcp", "gui", "saas", "smb"]
        has_mapache_term = any(term in text for term in mapache_terms)

        if not has_mapache_term:
            # Could be a generic issue - needs human review
            return True, "No explicit Mapache terms, but may still be relevant"

        return True, "Contains Mapache-related terms"

    # =========================================================================
    # Leanification
    # =========================================================================

    def extract_problem_from_description(self, description: str) -> str:
        """Extract or infer problem statement from description."""
        if not description:
            return "Problem not specified"

        # Look for explicit problem section
        problem_match = re.search(
            r"(?:^|\n)(?:##?\s*)?(?:problem|issue|bug|pain point)[:\s]*\n?(.*?)(?:\n##|\n\n|$)",
            description,
            re.IGNORECASE | re.DOTALL,
        )
        if problem_match:
            return problem_match.group(1).strip()[:500]

        # Take first paragraph as problem
        paragraphs = description.split("\n\n")
        if paragraphs:
            return paragraphs[0].strip()[:500]

        return description[:500]

    def extract_outcome_from_description(self, description: str) -> str:
        """Extract or infer desired outcome from description."""
        if not description:
            return "Outcome not specified"

        # Look for explicit outcome/goal section
        outcome_match = re.search(
            r"(?:^|\n)(?:##?\s*)?(?:outcome|goal|expected|desired|acceptance)[:\s]*\n?(.*?)(?:\n##|\n\n|$)",
            description,
            re.IGNORECASE | re.DOTALL,
        )
        if outcome_match:
            return outcome_match.group(1).strip()[:500]

        return "Define clear success criteria"

    def extract_constraints(self, description: str) -> str:
        """Extract context and constraints from description."""
        if not description:
            return ""

        constraints: list[str] = []

        # Look for links
        links = re.findall(r"https?://[^\s]+", description)
        if links:
            constraints.append("Links: " + ", ".join(links[:5]))

        # Look for repo references
        repos = re.findall(r"(?:repo|repository)[:\s]*([^\s,]+)", description, re.IGNORECASE)
        if repos:
            constraints.append("Repos: " + ", ".join(repos))

        # Look for explicit constraints section
        constraint_match = re.search(
            r"(?:^|\n)(?:##?\s*)?(?:constraint|requirement|must|don't)[:\s]*\n?(.*?)(?:\n##|\n\n|$)",
            description,
            re.IGNORECASE | re.DOTALL,
        )
        if constraint_match:
            constraints.append(constraint_match.group(1).strip()[:300])

        default_msg = "Let Copilot plan from the current codebase"
        return "\n".join(constraints) if constraints else default_msg

    def strip_implementation_details(self, description: str) -> str:
        """Remove code blobs and implementation details that will get stale."""
        if not description:
            return ""

        # Remove code blocks
        code_block_msg = "[Code block removed - let Copilot analyze current code]"
        cleaned = re.sub(r"```[\s\S]*?```", code_block_msg, description)

        # Remove inline code that looks like file paths or function names
        cleaned = re.sub(
            r"(?:in file|rename|change|modify)\s+`[^`]+`\s+(?:to|from)\s+`[^`]+`",
            "[Implementation detail removed]",
            cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned

    def leanify(self, issue: LinearIssue, surfaces: list[ProductSurface]) -> LeanTicket:
        """
        Convert a bloated issue to Lean format.

        Strips:
        - Implementation details like "in file X, rename function Y to Z"
        - Large code blobs
        """
        description = issue.description or ""
        cleaned_desc = self.strip_implementation_details(description)

        problem = self.extract_problem_from_description(cleaned_desc)
        outcome = self.extract_outcome_from_description(cleaned_desc)
        constraints = self.extract_constraints(description)

        # Determine route hint
        size = self.estimate_size(issue)
        route_hint = self._get_route_hint(size, surfaces)

        return LeanTicket(
            problem=problem,
            desired_outcome=outcome,
            product_surfaces=surfaces,
            context_and_constraints=constraints,
            execution_route_hint=route_hint,
        )

    def _get_route_hint(self, size: IssueSize, surfaces: list[ProductSurface]) -> str:
        """Generate route hint based on size and surfaces."""
        if size == IssueSize.LARGE or ProductSurface.BRIDGE in surfaces:
            return "copilot-agent - Large or cross-cutting work benefits from agent mode"
        if size == IssueSize.SMALL:
            return "copilot-chat - Small, focused change suitable for chat"
        return "copilot-chat - Medium work, consider agent mode if complex"

    # =========================================================================
    # Prioritization
    # =========================================================================

    def calculate_priority_score(
        self,
        issue: LinearIssue,
        surfaces: list[ProductSurface],
        source: IssueSource,
    ) -> PrioritizationResult:
        """
        Calculate priority score for an issue.

        Rules:
        - Bias toward bridge work
        - Lift items that simplify .solutions → .app funnel
        - Push down maintenance of low-signal experiments
        """
        base_score = 50.0
        rationale_parts: list[str] = []
        boosted = False
        demoted = False

        # Surface-based adjustments
        if ProductSurface.BRIDGE in surfaces:
            base_score *= self.config.weights.bridge_boost
            rationale_parts.append(f"Bridge work boost ({self.config.weights.bridge_boost}x)")
            boosted = True

        if ProductSurface.APP in surfaces:
            base_score *= self.config.weights.app_boost
            rationale_parts.append(f"App work boost ({self.config.weights.app_boost}x)")
            boosted = True

        # Source-based adjustments
        if source == IssueSource.OPPORTUNITY_AGENT:
            # Check if it's a high-signal opportunity
            text = f"{issue.title} {issue.description or ''}".lower()
            if any(term in text for term in ["pain", "user", "customer", "revenue", "growth"]):
                base_score *= self.config.weights.opportunity_agent_boost
                rationale_parts.append("High-signal opportunity agent idea")
                boosted = True
            else:
                base_score *= self.config.weights.speculative_demote
                rationale_parts.append("Speculative opportunity - needs validation")
                demoted = True

        # Check for maintenance-only work
        text = f"{issue.title} {issue.description or ''}".lower()
        maintenance_terms = ["maintenance", "upkeep", "dependency", "update", "version"]
        if any(term in text for term in maintenance_terms) and ProductSurface.SOLUTIONS in surfaces:
            if ProductSurface.APP not in surfaces and ProductSurface.BRIDGE not in surfaces:
                base_score *= self.config.weights.maintenance_demote
                rationale_parts.append("Pure maintenance on solutions - lower priority")
                demoted = True

        # Map score to priority rank (P1-P4)
        if base_score >= 100:
            priority_rank = 1
        elif base_score >= 60:
            priority_rank = 2
        elif base_score >= 30:
            priority_rank = 3
        else:
            priority_rank = 4

        return PrioritizationResult(
            issue_id=issue.id,
            priority_score=base_score,
            priority_rank=priority_rank,
            rationale=" | ".join(rationale_parts) if rationale_parts else "Standard priority",
            boosted=boosted,
            demoted=demoted,
        )

    # =========================================================================
    # Routing
    # =========================================================================

    def decide_route(
        self,
        issue: LinearIssue,
        size: IssueSize,
        surfaces: list[ProductSurface],
    ) -> RoutingDecision:
        """
        Decide execution route for an issue.

        Rules:
        - copilot-agent: large work, multi-repo, bridge work
        - copilot-chat: small/medium, focused work
        - manual: strategy/architecture, ambiguous scope
        """
        rationale_parts: list[str] = []

        # Check for manual routing needs
        text = f"{issue.title} {issue.description or ''}".lower()
        ambiguous_terms = ["unclear", "tbd", "decide", "strategy", "architecture", "should we"]
        if any(term in text for term in ambiguous_terms):
            return RoutingDecision(
                issue_id=issue.id,
                route=ExecutionRoute.MANUAL,
                rationale="Ambiguous scope or strategy decision - needs human input",
            )

        # Route based on size and surface
        if size == IssueSize.LARGE:
            route = ExecutionRoute.COPILOT_AGENT
            rationale_parts.append("Large work")
        elif ProductSurface.BRIDGE in surfaces:
            route = ExecutionRoute.COPILOT_AGENT
            rationale_parts.append("Bridge work (cross-cutting)")
        elif size == IssueSize.SMALL:
            route = ExecutionRoute.COPILOT_CHAT
            rationale_parts.append("Small, focused work")
        else:
            route = ExecutionRoute.COPILOT_CHAT
            rationale_parts.append("Medium work - chat is sufficient")

        decision = RoutingDecision(
            issue_id=issue.id,
            route=route,
            rationale=" | ".join(rationale_parts),
        )

        # Prepare appropriate brief/snippet
        if route == ExecutionRoute.COPILOT_AGENT:
            decision.copilot_brief = self._create_copilot_brief(issue, surfaces)
        elif route == ExecutionRoute.COPILOT_CHAT:
            decision.chat_snippet = self._create_chat_snippet(issue)

        return decision

    def _create_copilot_brief(
        self,
        issue: LinearIssue,
        surfaces: list[ProductSurface],
    ) -> CopilotBrief:
        """Create a machine-readable brief for Copilot agent."""
        description = issue.description or ""

        # Extract repos from description
        repos: list[str] = []
        repo_matches = re.findall(r"github\.com/([^/\s]+/[^/\s]+)", description)
        repos.extend(repo_matches)

        # Infer repos from surface
        if ProductSurface.SOLUTIONS in surfaces:
            repos.append("mapache-solutions-* (inferred)")
        if ProductSurface.APP in surfaces:
            repos.append("mapache-app-* (inferred)")

        return CopilotBrief(
            problem=self.extract_problem_from_description(description),
            outcome=self.extract_outcome_from_description(description),
            constraints=self.extract_constraints(description).split("\n"),
            repos=repos,
            suggested_steps=["Analyze current codebase", "Plan implementation", "Execute changes"],
            linear_issue_id=issue.id,
            linear_issue_url=issue.url,
        )

    def _create_chat_snippet(self, issue: LinearIssue) -> ChatPromptSnippet:
        """Create a prompt snippet for Copilot Chat."""
        description = issue.description or ""

        return ChatPromptSnippet(
            context=f"Working on Linear issue {issue.identifier}: {issue.title}",
            problem=self.extract_problem_from_description(description),
            constraints=self.extract_constraints(description),
            acceptance_criteria=self.extract_outcome_from_description(description),
        )

    # =========================================================================
    # Triage (combines all steps)
    # =========================================================================

    def triage(self, issue: LinearIssue) -> TriageResult:
        """
        Full triage of an issue.

        Steps:
        1. Relevance check
        2. Surface classification
        3. Source detection
        4. Size estimation
        5. Leanification
        6. Prioritization
        7. Routing
        """
        # 1. Relevance check
        is_relevant, relevance_reason = self.check_relevance(issue)
        if not is_relevant:
            return TriageResult(
                issue_id=issue.id,
                original_title=issue.title,
                is_relevant=False,
                status=IssueStatus.DISCARDED,
                rationale=relevance_reason,
            )

        # 2-4. Classification
        surfaces = self.classify_surfaces(issue)
        source = self.detect_source(issue)
        size = self.estimate_size(issue)

        # 5. Leanification
        lean_ticket = None
        if self.config.auto_leanify:
            lean_ticket = self.leanify(issue, surfaces)

        # 6. Prioritization
        priority_result = self.calculate_priority_score(issue, surfaces, source)

        # 7. Routing
        routing = None
        route = None
        if self.config.auto_route:
            routing = self.decide_route(issue, size, surfaces)
            route = routing.route

        return TriageResult(
            issue_id=issue.id,
            original_title=issue.title,
            is_relevant=True,
            surfaces=surfaces,
            size=size,
            route=route,
            status=IssueStatus.SHAPED,
            lean_ticket=lean_ticket,
            priority_score=priority_result.priority_score,
            rationale=f"{relevance_reason} | Priority: {priority_result.rationale}",
            needs_human_review=route == ExecutionRoute.MANUAL if route else False,
        )

    # =========================================================================
    # Self-Improvement
    # =========================================================================

    def create_improvement_ticket(
        self,
        input_summary: str,
        decision_made: str,
        why_wrong: str,
        suggested_adjustment: str,
        severity: str = "low",
        original_issue_id: str | None = None,
    ) -> SelfImprovementTicket:
        """Create a self-improvement ticket for logging failures."""
        return SelfImprovementTicket(
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_summary=input_summary,
            decision_made=decision_made,
            why_wrong=why_wrong,
            suggested_adjustment=suggested_adjustment,
            severity=severity,
            original_issue_id=original_issue_id,
        )

    def detect_misrouting(
        self,
        issue: LinearIssue,
        actual_route: ExecutionRoute,
        actual_size: IssueSize,
    ) -> SelfImprovementTicket | None:
        """
        Detect if routing was likely wrong.

        E.g., large cross-cutting refactor given copilot-chat route.
        """
        # Check if large work was sent to chat
        if actual_size == IssueSize.LARGE and actual_route == ExecutionRoute.COPILOT_CHAT:
            adjustment = "Consider adding check: if size=large, default to copilot-agent"
            return self.create_improvement_ticket(
                input_summary=f"Issue {issue.identifier}: {issue.title}",
                decision_made=f"Routed to {actual_route.value} with size {actual_size.value}",
                why_wrong="Large work should go to copilot-agent for better handling",
                suggested_adjustment=adjustment,
                severity="medium",
                original_issue_id=issue.id,
            )

        return None


# =============================================================================
# Simplified Interface Functions
# =============================================================================
# These functions provide a simpler interface for testing per AgentSpec.md


def _issue_to_linear_issue(issue: dict | object) -> LinearIssue:
    """Convert a dict or simple dataclass to LinearIssue."""
    if isinstance(issue, dict):
        title = issue.get("title", "")
        description = issue.get("description", "")
        labels = issue.get("labels", [])
        linked_repos = issue.get("linked_repos", [])
    else:
        # Assume it's a dataclass or object with attributes
        title = getattr(issue, "title", "")
        description = getattr(issue, "description", "")
        labels = getattr(issue, "labels", [])
        linked_repos = getattr(issue, "linked_repos", [])

    # Append linked repos to description for surface classification
    if linked_repos:
        repos_text = "\nLinked repos: " + ", ".join(linked_repos)
        description = description + repos_text

    return LinearIssue(
        id="test-issue",
        identifier="TEST-1",
        title=title,
        description=description,
        labels=labels,
    )


def classify_surface(issue: dict | object) -> set[str]:
    """
    Classify issue by product surface.

    Args:
        issue: Dict or dataclass with title, description, labels, source, linked_repos

    Returns:
        Set of surface names: "solutions", "app", "bridge"
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)
    surfaces = core.classify_surfaces(linear_issue)
    return {s.value.replace("surface:", "") for s in surfaces}


def estimate_size(issue: dict | object) -> str:
    """
    Estimate issue size for routing.

    Args:
        issue: Dict or dataclass with title, description, labels

    Returns:
        Size string: "small", "medium", "large"
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)
    size = core.estimate_size(linear_issue)
    return size.value.replace("size:", "")


def choose_route(issue: dict | object) -> str:
    """
    Choose execution route for an issue.

    Args:
        issue: Dict or dataclass with title, description, labels

    Returns:
        Route string: "copilot-agent", "copilot-chat", "manual"
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)
    surfaces = core.classify_surfaces(linear_issue)
    size = core.estimate_size(linear_issue)
    decision = core.decide_route(linear_issue, size, surfaces)
    return decision.route.value.replace("route:", "")


def leanify_description(issue: dict | object) -> str:
    """
    Convert bloated description to Lean format.

    Args:
        issue: Dict or dataclass with title, description

    Returns:
        Lean-formatted description as markdown string
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)
    surfaces = core.classify_surfaces(linear_issue)
    lean_ticket = core.leanify(linear_issue, surfaces)
    return lean_ticket.to_markdown()


def prioritize(issue: dict | object, context: dict | None = None) -> int:
    """
    Calculate priority for an issue.

    Args:
        issue: Dict or dataclass with title, description, labels, source
        context: Optional context dict (unused for now)

    Returns:
        Priority rank: 1 (highest) to 4 (lowest)
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)
    surfaces = core.classify_surfaces(linear_issue)
    source = core.detect_source(linear_issue)
    result = core.calculate_priority_score(linear_issue, surfaces, source)
    return result.priority_rank or 4


def detect_misrouting(
    issue: dict | object,
    actual_route: str,
    actual_size: str,
) -> dict | None:
    """
    Detect if routing was likely wrong.

    Args:
        issue: Dict or dataclass with title, description, labels
        actual_route: The route that was chosen ("copilot-agent", "copilot-chat", "manual")
        actual_size: The size that was estimated ("small", "medium", "large")

    Returns:
        Dict with needs_improvement=True if misrouted, None otherwise
    """
    core = LinearAgentCore()
    linear_issue = _issue_to_linear_issue(issue)

    # Convert string to enum
    route_map = {
        "copilot-agent": ExecutionRoute.COPILOT_AGENT,
        "copilot-chat": ExecutionRoute.COPILOT_CHAT,
        "manual": ExecutionRoute.MANUAL,
    }
    size_map = {
        "small": IssueSize.SMALL,
        "medium": IssueSize.MEDIUM,
        "large": IssueSize.LARGE,
    }

    route_enum = route_map.get(actual_route)
    size_enum = size_map.get(actual_size)

    if not route_enum or not size_enum:
        return None

    improvement = core.detect_misrouting(linear_issue, route_enum, size_enum)

    if improvement:
        return {
            "needs_improvement": True,
            "severity": improvement.severity,
            "why_wrong": improvement.why_wrong,
            "suggested_adjustment": improvement.suggested_adjustment,
        }

    return None
