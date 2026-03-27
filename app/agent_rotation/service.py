"""
This module contains the service for managing a pool of agents and handling agent rotation.
"""
from typing import List, Optional
from app.models.agent import Agent

class AgentRotationService:
    def __init__(self, agents: List[Agent]):
        if not agents:
            raise ValueError("Agent list cannot be empty.")
        self.agents = agents
        self.current_agent_index = 0

    def get_active_agent(self) -> Agent:
        """Returns the currently active agent."""
        return self.agents[self.current_agent_index]

    def rotate_agent(self) -> Optional[Agent]:
        """Rotates to the next available agent."""
        initial_index = self.current_agent_index
        for i in range(len(self.agents)):
            self.current_agent_index = (initial_index + i + 1) % len(self.agents)
            agent = self.get_active_agent()
            if agent.status == "active" and agent.remaining_quota > 0:
                print(f"Rotated to agent: {agent.name}")
                return agent
        print("No active agents available.")
        return None

    def record_usage(self, agent_id: str, cost: int = 1):
        """Records API usage for an agent and updates its remaining quota."""
        for agent in self.agents:
            if agent.id == agent_id:
                agent.remaining_quota -= cost
                if agent.remaining_quota <= 0:
                    agent.status = "inactive"
                    print(f"Agent {agent.name} has run out of quota.")
                break

    def report_error(self, agent_id: str):
        """Reports an error for an agent and sets its status to 'error'."""
        for agent in self.agents:
            if agent.id == agent_id:
                agent.status = "error"
                print(f"Agent {agent.name} reported an error.")
                break

# Example usage:
# agents = [
#     Agent(id="agent-1", name="Primary", api_key="key-1", quota=1000, remaining_quota=1000, status="active"),
#     Agent(id="agent-2", name="Backup", api_key="key-2", quota=500, remaining_quota=500, status="active"),
# ]
# rotation_service = AgentRotationService(agents)
# active_agent = rotation_service.get_active_agent()
# rotation_service.record_usage(active_agent.id)
# rotation_service.report_error(active_agent.id)
# next_agent = rotation_service.rotate_agent()
