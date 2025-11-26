"""Utilities to convert raw Linear issues into Lean tickets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import LeanTicket, TicketContext, acceptance_from_lines, normalize_acceptance


@dataclass
class RawTicket:
    """Raw ticket payload pulled from Linear."""

    title: str
    description: str
    reporter: Optional[str] = None
    owner: Optional[str] = None


class LeanTicketShaper:
    """Shape incoming tickets to a Lean product format."""

    def shape(self, raw: RawTicket, context: TicketContext) -> LeanTicket:
        """Return a Lean ticket derived from raw Linear content and context."""

        problem, impact, scope = self._extract_sections(raw.description)
        acceptance = normalize_acceptance(acceptance_from_lines(raw.description))
        if not acceptance:
            acceptance = ["User can complete the intended flow without regression."]
        owner = raw.owner or context.reporter
        return LeanTicket(
            title=raw.title.strip(),
            problem=problem,
            impact=impact,
            scope=scope,
            acceptance_criteria=acceptance,
            owner=owner,
        )

    def _extract_sections(self, description: str) -> tuple[str, str, str]:
        """Extract problem, impact, and scope sections using simple heuristics."""

        lines = [line.strip() for line in description.splitlines() if line.strip()]
        problem = lines[0] if lines else "Problem not specified"
        impact = next((line for line in lines if "impact" in line.lower()), problem)
        scope = next((line for line in lines if "scope" in line.lower()), "Narrow to a single user scenario")
        return problem, impact, scope
