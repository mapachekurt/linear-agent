"""Coding agent configuration and capacity tracking utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Set

from .models import Classification


@dataclass
class AgentCapacity:
    """Track active workloads against an agent's concurrent capacity."""

    max_concurrent: int
    active_jobs: Set[str] = field(default_factory=set)

    def available_slots(self) -> int:
        """Return the number of remaining concurrent jobs allowed."""

        return max(self.max_concurrent - len(self.active_jobs), 0)

    def dispatch(self, job_id: str) -> bool:
        """Record a dispatched job if capacity allows."""

        if job_id in self.active_jobs:
            return True
        if self.available_slots() <= 0:
            return False
        self.active_jobs.add(job_id)
        return True

    def release(self, job_id: str) -> None:
        """Release a job slot when the work completes."""

        self.active_jobs.discard(job_id)


@dataclass
class AgentConfig:
    """Configuration for a Copilot coding agent."""

    name: str
    surfaces: Set[str]
    max_concurrent: int = 1
    capacity: AgentCapacity = field(init=False)

    def __post_init__(self) -> None:
        self.capacity = AgentCapacity(max_concurrent=self.max_concurrent)


def load_coding_agents(path: str | Path = "config/coding_agents.yaml") -> List[AgentConfig]:
    """Load coding agent definitions from YAML into :class:`AgentConfig` objects."""

    config_path = Path(path)
    if not config_path.exists():
        return []

    content = config_path.read_text(encoding="utf-8")
    if not content.strip():
        return []

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        try:
            import yaml
        except ModuleNotFoundError as exc:  # pragma: no cover - defensive import error handling
            raise RuntimeError("PyYAML is required to parse coding_agents.yaml") from exc
        payload = yaml.safe_load(content) or {}

    agents: List[AgentConfig] = []
    for raw in payload.get("agents", []):
        agents.append(
            AgentConfig(
                name=raw.get("name"),
                surfaces=set(raw.get("surfaces", [])),
                max_concurrent=int(raw.get("max_concurrent", 1)),
            )
        )
    return agents


def select_coding_agent(
    classification: Classification, agents: Iterable[AgentConfig], job_id: Optional[str] = None
) -> Optional[AgentConfig]:
    """Choose an available coding agent for the given classification, dispatching if possible."""

    surface = classification.surface.value
    ranked: List[AgentConfig] = []
    for agent in agents:
        if surface in agent.surfaces or not agent.surfaces:
            ranked.append(agent)
    if not ranked:
        ranked = list(agents)

    ranked.sort(key=lambda agent: agent.capacity.available_slots(), reverse=True)

    for agent in ranked:
        if agent.capacity.available_slots() <= 0:
            continue
        if job_id:
            if agent.capacity.dispatch(job_id):
                return agent
            continue
        return agent
    return None
