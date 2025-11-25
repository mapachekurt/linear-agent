# Autonomous Linear Agent

An autonomous agent for managing Linear issues with self-learning capabilities, deep GitHub integration, and multi-agent orchestration.

## Features

- **Complete Issue Lifecycle Management**: The agent can accept, analyze, monitor, update, and close Linear issues automatically.
- **Self-Learning System**: All agent actions are logged to a persistent JSONL file. Failures automatically generate feedback tickets in Linear for continuous improvement.
- **Agent Rotation**: The system can manage a pool of agents, rotating them based on API quota limits or errors, ensuring high availability.
- **GitHub Integration**:
    - **PR/Branch Linking**: Automatically links new branches and pull requests to Linear issues.
    - **Commit Magic Words**: Recognizes keywords like "closes", "fixes", and "resolves" in PR bodies to automatically close the corresponding Linear issue upon merge.
    - **Issue State Sync**: Keeps the state of Linear issues in sync with their corresponding GitHub pull requests.
- **OAuth & Webhook Handling**: Securely authenticates with the GitHub API and handles incoming webhooks from both Linear and GitHub.
- **Modular Architecture**: Built with a clean, modular architecture that separates concerns into distinct modules for issue management, GitHub sync, self-learning, and agent rotation.
- **FastAPI Server**: Includes a high-performance FastAPI server for handling webhooks and providing monitoring endpoints.

## Getting Started

### Prerequisites

- Python 3.10+
- A Linear account and API key
- A GitHub account and a GitHub App

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/linear-agent.git
    cd linear-agent
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the environment variables:**

    Create a `.env` file in the root of the project and add the following environment variables:

    ```env
    # .env
    GITHUB_APP_ID="your_github_app_id"
    GITHUB_PRIVATE_KEY="your_github_app_private_key"
    GITHUB_INSTALLATION_ID="your_github_app_installation_id"
    LINEAR_API_KEY="your_linear_api_key"
    LINEAR_TEAM_ID="your_linear_team_id" # The ID of the team to create feedback tickets in
    ```

### Running the Agent

To run the agent, use `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The agent will now be running and listening for incoming webhooks from Linear and GitHub.

## Testing

To run the test suite, use `pytest`:

```bash
python -m pytest
```

To run the tests with a coverage report:

```bash
python -m pytest --cov=app
```

## Architecture

The agent is built with a modular architecture, with each key feature separated into its own module:

-   `app/issue_management`: Handles the core logic for the issue lifecycle.
-   `app/github_sync`: Manages the synchronization between Linear and GitHub.
-   `app/self_learning`: Implements the JSONL logging and feedback ticket generation.
-   `app/agent_rotation`: Manages the pool of agents and handles rotation.
-   `app/models`: Contains the Pydantic data models for the application.
-   `app/main.py`: The main FastAPI application file.

## Current Status

This project provides a robust architectural foundation for an autonomous Linear agent. The core scaffolding, including the FastAPI server, webhook handling, security measures, and modular services, is in place. However, some of the advanced business logic for issue lifecycle management is not yet fully implemented.

The following features are fully functional:
- Webhook handling for Linear and GitHub
- Secure signature verification for all incoming webhooks
- Linking of GitHub branches and pull requests to Linear issues
- Automatic closing of Linear issues when a linked PR is merged with "magic words"
- Self-learning through persistent JSONL logging of all agent actions
- Automatic creation of feedback tickets in Linear when errors occur
- Agent rotation based on a configurable agent pool

The following features are currently placeholders and are planned for future development:
- **Issue Acceptance**: The `accept_issue` method is a placeholder.
- **Issue Analysis**: The `analyze_issue` method is a placeholder.
- **Issue Monitoring**: The `monitor_issue` method is a placeholder.
