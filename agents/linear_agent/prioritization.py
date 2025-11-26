"""Prioritize tickets according to the Mapache funnel."""
from __future__ import annotations

from .models import Classification, PrioritizedTicket


class TicketPrioritizer:
    """Assign priority scores that emphasize the solutions → app → bridge funnel."""

    SURFACE_WEIGHT = {"solutions": 3.0, "app": 2.0, "bridge": 1.0}
    SIZE_WEIGHT = {"s": 1.0, "m": 0.75, "l": 0.5}

    def score(self, classification: Classification, lean_ticket) -> PrioritizedTicket:
        """Return a prioritized ticket with rationale."""

        surface_score = self.SURFACE_WEIGHT[classification.surface.value]
        size_score = self.SIZE_WEIGHT[classification.size.value]
        base = surface_score * size_score
        rationale = (
            f"Surface {classification.surface.value} weighted {surface_score}; "
            f"size {classification.size.value} weighted {size_score}."
        )
        if classification.source == classification.source.CUSTOMER:
            base += 0.5
            rationale += " Customer-sourced work nudged upward."
        return PrioritizedTicket(
            classification=classification,
            lean_ticket=lean_ticket,
            priority_score=round(base, 2),
            rationale=rationale,
        )
