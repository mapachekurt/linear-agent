"""Deploy the Linear Product Management Agent to Vertex AI Agent Engine."""
from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Dict

try:  # Prefer preview namespace when available
    from vertexai import Client
    from vertexai.preview import agent_engine
except ImportError:  # pragma: no cover - fallback for alternate installation layouts
    from google.cloud.aiplatform.preview import agent_engine  # type: ignore
    from vertexai import Client  # type: ignore


DISPLAY_NAME = "linear-product-management-agent"
DESCRIPTION = "Linear Product Management Agent for Mapache."
ENTRYPOINT_MODULE = "agents.linear_agent.agent_entrypoint"
ENTRYPOINT_OBJECT = "root_agent"
REQUIREMENTS_FILE = "requirements.txt"
SOURCE_PACKAGES = ["agents", "config", REQUIREMENTS_FILE]


def main() -> None:
    project_id = os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")
    location = os.environ.get("LOCATION", "YOUR_LOCATION")

    client = Client(project=project_id, location=location)

    source = agent_engine.LocalPythonPackageSource(
        source_packages=SOURCE_PACKAGES,
        requirements_file=REQUIREMENTS_FILE,
    )

    entrypoint = agent_engine.Entrypoint(
        module=ENTRYPOINT_MODULE,
        agent_class=ENTRYPOINT_OBJECT,
    )

    class_methods = [
        agent_engine.ClassMethod(
            name="query",
            request=agent_engine.Schema(
                type=agent_engine.Type.OBJECT,
                properties={
                    "input": agent_engine.Schema(
                        type=agent_engine.Type.STRING,
                        description="Natural language prompt for the Linear agent.",
                    )
                },
                required=["input"],
            ),
            response=agent_engine.Schema(type=agent_engine.Type.STRING),
        )
    ]

    agent = agent_engine.Agent(
        display_name=DISPLAY_NAME,
        description=DESCRIPTION,
        entrypoint=entrypoint,
        source=source,
        agent_framework="google-adk",
        class_methods=class_methods,
    )

    operation = client.preview_agent_deploy(agent=agent)
    operation.result()
    created = operation.metadata.get("agent", {}) if hasattr(operation, "metadata") else {}

    print("Created agent:", getattr(operation, "name", None) or created)
    print("Class methods:")
    for method in class_methods:
        print(asdict(method))


if __name__ == "__main__":
    main()
