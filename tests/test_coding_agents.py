"""Tests for coding agent configuration loading and selection."""
from __future__ import annotations

from pathlib import Path

import pytest

from agents.linear_agent import (
    AgentCapacity,
    AgentConfig,
    Classification,
    Surface,
    TicketSize,
    TicketSource,
    load_coding_agents,
    select_coding_agent,
)


def test_load_coding_agents_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "coding_agents.yaml"
    config_path.write_text(
        """
        {
          "agents": [
            {"name": "alpha", "surfaces": ["solutions", "app"], "max_concurrent": 2},
            {"name": "bridge", "surfaces": ["bridge"], "max_concurrent": 1}
          ]
        }
        """,
        encoding="utf-8",
    )

    agents = load_coding_agents(config_path)
    assert len(agents) == 2
    assert {agent.name for agent in agents} == {"alpha", "bridge"}
    assert agents[0].capacity.available_slots() == 2


def test_agent_capacity_dispatch_and_release() -> None:
    capacity = AgentCapacity(max_concurrent=1)
    assert capacity.available_slots() == 1
    assert capacity.dispatch("job-1")
    assert capacity.available_slots() == 0
    assert not capacity.dispatch("job-2")
    capacity.release("job-1")
    assert capacity.available_slots() == 1


def test_select_coding_agent_prefers_surface_and_capacity() -> None:
    classification = Classification(
        surface=Surface.BRIDGE,
        size=TicketSize.SMALL,
        source=TicketSource.INTERNAL,
        confidence=0.8,
    )
    agents = [
        AgentConfig(name="general", surfaces={"solutions"}, max_concurrent=1),
        AgentConfig(name="bridge", surfaces={"bridge"}, max_concurrent=1),
    ]

    selected = select_coding_agent(classification, agents, job_id="job-bridge")
    assert selected is not None
    assert selected.name == "bridge"
    assert selected.capacity.available_slots() == 0

    # With bridge capacity exhausted, fallback should avoid dispatch.
    selected.capacity.dispatch("job-other")
    second_selection = select_coding_agent(classification, agents, job_id="job-2")
    assert second_selection is None
