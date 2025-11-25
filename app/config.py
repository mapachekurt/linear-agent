"""
This module contains the configuration for the application, including the agent pool.
"""
import json
import os
from app.models.agent import Agent

def load_agents_from_env() -> list[Agent]:
    """
    Loads the agent configuration from the AGENTS_CONFIG environment variable.
    The environment variable is expected to be a JSON string representing a list
    of agent configurations.
    """
    agents_json = os.getenv("AGENTS_CONFIG")
    if not agents_json:
        # Return a default agent for development/testing if the env var is not set
        return [
            Agent(
                id="default-agent",
                name="Default Agent",
                api_key="default-key",
                quota=1000,
                remaining_quota=1000,
                status="active",
            )
        ]

    try:
        agents_data = json.loads(agents_json)
        return [Agent(**data) for data in agents_data]
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error loading agent configuration: {e}")
        # Fallback to a default agent in case of parsing errors
        return [
            Agent(
                id="error-agent",
                name="Error Agent",
                api_key="error-key",
                quota=0,
                remaining_quota=0,
                status="inactive",
            )
        ]

AGENTS = load_agents_from_env()
