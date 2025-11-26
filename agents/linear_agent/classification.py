"""Ticket classification logic aligned with the Mapache funnel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Classification, LeanTicket, Surface, TicketContext, TicketSize, TicketSource


@dataclass
class ClassificationRule:
    """Simple heuristic rule to map keywords to surfaces."""

    keywords: Iterable[str]
    surface: Surface


class TicketClassifier:
    """Classify tickets by surface, size, and source."""

    SURFACE_RULES = [
        ClassificationRule(keywords=("solution", "solutions", "gui"), surface=Surface.SOLUTIONS),
        ClassificationRule(keywords=("mapache.app", "chat", "os"), surface=Surface.APP),
        ClassificationRule(keywords=("bridge", "integration", "mcp"), surface=Surface.BRIDGE),
    ]

    def classify(self, lean: LeanTicket, context: TicketContext) -> Classification:
        """Return classification derived from ticket content and context hints."""

        surface = context.surface_hint or self._infer_surface(lean)
        size = context.size_hint or self._infer_size(lean)
        source = context.source
        confidence = 0.8 if lean.is_crisp() else 0.55
        if context.surface_hint:
            confidence += 0.1
        return Classification(surface=surface, size=size, source=source, confidence=min(confidence, 0.95))

    def _infer_surface(self, lean: LeanTicket) -> Surface:
        """Infer surface from keywords in the lean ticket content."""

        title_description = f"{lean.title} {lean.problem} {lean.scope}".lower()
        for rule in self.SURFACE_RULES:
            if any(keyword in title_description for keyword in rule.keywords):
                return rule.surface
        return Surface.SOLUTIONS

    def _infer_size(self, lean: LeanTicket) -> TicketSize:
        """Infer relative size from acceptance criteria and scope length."""

        criteria_count = len(lean.acceptance_criteria)
        scope_length = len(lean.scope)
        if criteria_count <= 2 and scope_length < 140:
            return TicketSize.SMALL
        if criteria_count <= 4 and scope_length < 400:
            return TicketSize.MEDIUM
        return TicketSize.LARGE
