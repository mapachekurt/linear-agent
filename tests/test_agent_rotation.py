import pytest
from app.models.agent import Agent
from app.agent_rotation.service import AgentRotationService

@pytest.fixture
def agents():
    return [
        Agent(id="agent-1", name="Primary", api_key="key-1", quota=100, remaining_quota=100, status="active"),
        Agent(id="agent-2", name="Backup", api_key="key-2", quota=50, remaining_quota=50, status="active"),
        Agent(id="agent-3", name="Tertiary", api_key="key-3", quota=10, remaining_quota=0, status="inactive"),
    ]

def test_get_active_agent(agents):
    service = AgentRotationService(agents)
    assert service.get_active_agent().id == "agent-1"

def test_rotate_agent(agents):
    service = AgentRotationService(agents)
    service.rotate_agent()
    assert service.get_active_agent().id == "agent-2"
    service.rotate_agent()
    assert service.get_active_agent().id == "agent-1" # Skips the inactive agent

def test_record_usage(agents):
    service = AgentRotationService(agents)
    service.record_usage("agent-1", 10)
    assert service.agents[0].remaining_quota == 90
    service.record_usage("agent-1", 90)
    assert service.agents[0].remaining_quota == 0
    assert service.agents[0].status == "inactive"

def test_report_error(agents):
    service = AgentRotationService(agents)
    service.report_error("agent-1")
    assert service.agents[0].status == "error"

def test_no_active_agents(agents):
    for agent in agents:
        agent.status = "inactive"
    service = AgentRotationService(agents)
    assert service.rotate_agent() is None
