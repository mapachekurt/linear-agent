"""Core logic helpers for the Mapache Linear agent.

# Core API (finalized)
# - Issue: normalized issue payload used by the core helpers
# - classify_surfaces(issue) -> set[str]
# - estimate_size(issue) -> str
# - leanify_issue(issue) -> str
# - choose_route(issue) -> str
# - prioritize_issue(issue, context) -> int
# - flag_self_improvement(issue) -> None
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, MutableMapping, Optional, Set

__all__ = [
    "Issue",
    "classify_surfaces",
    "estimate_size",
    "leanify_issue",
    "choose_route",
    "prioritize_issue",
    "flag_self_improvement",
]


@dataclass
class Issue:
    """Simplified issue representation for core logic flows."""

    title: str
    description: str
    labels: List[str]
    source: Optional[str] = None
    linked_repos: Optional[List[str]] = None
    metadata: MutableMapping[str, object] = field(default_factory=dict)


def _coerce_lower(text: Optional[str]) -> str:
    return text.lower() if text else ""


def _get_attr(issue: object, key: str, default: Optional[object] = None) -> object:
    if isinstance(issue, MutableMapping):
        return issue.get(key, default)
    return getattr(issue, key, default)


def classify_surfaces(issue: object) -> Set[str]:
    """Infer surfaces from title, labels, or linked repositories."""
    title = _coerce_lower(_get_attr(issue, "title", ""))
    labels: Iterable[str] = _get_attr(issue, "labels", []) or []
    linked_repos: Iterable[str] = _get_attr(issue, "linked_repos", []) or []

    surfaces: Set[str] = set()

    tokens = " ".join([title, " ".join(labels), " ".join(linked_repos)]).lower()
    if "bridge" in tokens or "mcp" in tokens:
        surfaces.add("bridge")
    if "app" in tokens:
        surfaces.add("app")
    if "solutions" in tokens:
        surfaces.add("solutions")

    return surfaces


def estimate_size(issue: object) -> str:
    """Estimate size based on labels and description length."""
    description = _coerce_lower(_get_attr(issue, "description", ""))
    labels: Iterable[str] = _get_attr(issue, "labels", []) or []

    label_text = " ".join(labels).lower()
    if "large" in label_text or "epic" in label_text or len(description) > 180:
        return "large"
    if len(description) < 80 and "small" in label_text:
        return "small"
    if len(description) < 80:
        return "small"
    return "medium"


def leanify_issue(issue: object) -> str:
    """Convert a loose description into a Lean format string."""
    description = _coerce_lower(_get_attr(issue, "description", ""))
    source = _coerce_lower(_get_attr(issue, "source", ""))

    problem = description.split(".")[0] or "TBD problem"
    impact = "impact" if "impact" in description else "TBD impact"
    scope = "scope" if "scope" in description else "TBD scope"
    acceptance = "Acceptance: TBD"

    surfaces = classify_surfaces(issue)
    status: str
    if source == "opportunity-agent":
        status = "Status: shaped"
    elif not surfaces:
        status = "Status: parked"
    elif not description:
        status = "Status: parked"
    else:
        status = "Status: shaped"

    lean_sections = [
        f"Problem: {problem.strip().capitalize()}",
        f"Impact: {impact}",
        f"Scope: {scope}",
        acceptance,
        status,
    ]

    return "\n".join(lean_sections)


def prioritize_issue(issue: object, context: object) -> int:  # noqa: ARG001
    """Return a numeric priority (lower is higher)."""
    surfaces = classify_surfaces(issue)
    source = _coerce_lower(_get_attr(issue, "source", ""))

    if not surfaces:
        return 99

    possible_weights = [
        weight
        for weight in [
            1 if "bridge" in surfaces else None,
            2 if "app" in surfaces else None,
            3 if "solutions" in surfaces else None,
        ]
        if weight is not None
    ]
    surface_weight = min(possible_weights)

    base = surface_weight * 10
    if source == "opportunity-agent":
        base -= 5

    size = estimate_size(issue)
    if size == "large":
        base += 2
    elif size == "small":
        base -= 1

    return max(base, 1)


def choose_route(issue: object) -> str:
    """Pick a routing destination based on size and clarity."""
    size = estimate_size(issue)
    description = _coerce_lower(_get_attr(issue, "description", ""))
    labels: Iterable[str] = _get_attr(issue, "labels", []) or []

    if not description:
        flag_self_improvement(issue)
        return "route:manual"

    if "support" in " ".join(labels).lower() and size == "large":
        flag_self_improvement(issue)
        return "route:copilot-chat"

    if size == "large":
        return "route:copilot-agent"
    if "unclear" in description or len(description) > 160:
        return "route:copilot-chat"
    return "route:copilot-agent"


def _flag_self_improvement(issue: object) -> None:
    metadata = _get_attr(issue, "metadata", None)
    if isinstance(metadata, MutableMapping):
        metadata["needs_self_improvement"] = True


# Self-improvement hook is public to allow orchestrators to log and react.
def flag_self_improvement(issue: object) -> None:
    """Mark the issue as needing self-improvement follow-up."""
    _flag_self_improvement(issue)

