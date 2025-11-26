# Linear Product Management Agent

The product/backlog brain for Mapache. This agent runs on Google Vertex AI Agent Engine using ADK and manages Linear issues with intelligent classification, prioritization, and routing.

## Overview

The Linear Agent:
- Keeps Linear projects/issues **lean and up to date**
- Reflects the **Mapache business model**: `mapache.solutions` → `mapache.app`
- Orchestrates **execution routing** to GitHub Copilot (agent vs chat)
- Acts as glue between Slack, Linear, and GitHub

The agent does **not** write code; it shapes work and routes it to the right tools.

## Architecture

### Package Structure

```
agents/linear_agent/
├── __init__.py           # Package exports
├── app.py                # ADK app entrypoint for Vertex AI Agent Engine
├── core.py               # Core logic: classification, Leanification, prioritization, routing
├── config.py             # Configurable labels, statuses, settings
├── models.py             # Dataclasses for tickets, routes, surfaces
├── linear_client.py      # Linear MCP + REST API wrapper
└── github_client.py      # GitHub MCP + REST API wrapper

linear_agent/             # Legacy module (original CRUD implementation)
└── ...
```

### Key Concepts

#### Product Surfaces
- `surface:solutions` - mapache.solutions web apps
- `surface:app` - mapache.app conversational OS
- `surface:bridge` - Work moving flows from .solutions → .app via MCP-GUI

#### Issue Size
- `size:small` - Single-file or localized
- `size:medium` - Multi-component but straightforward
- `size:large` - Cross-cutting, multiple services, redesign

#### Execution Routes
- `route:copilot-agent` - Large work, multi-repo (Copilot coding agent)
- `route:copilot-chat` - Small/medium work (Copilot Chat)
- `route:manual` - Strategy/architecture decisions

## Features

### Backlog Shaping
- **Classification**: Detects product surface, size, and source automatically
- **Leanification**: Converts bloated tickets to a standard Lean format:
  - Problem (user-centered)
  - Desired Outcome
  - Product Surface
  - Context & Constraints
  - Execution Route Hint

### Prioritization
- **Bridge work boost**: Work moving flows to mapache.app gets priority
- **High-signal opportunity boost**: Ideas with clear user/revenue fit
- **Maintenance demote**: Pure maintenance on legacy solutions
- **Speculative demote**: Ideas without validation

### Routing
- Automatically decides between Copilot agent, Copilot chat, or manual review
- Generates appropriate briefs/prompts for each route

### Self-Improvement
- Logs misclassifications and failures
- Creates improvement tickets in a dedicated Linear project

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file:

```env
# Linear API
LINEAR_API_KEY=your-linear-api-key
LINEAR_IMPROVEMENTS_PROJECT_ID=your-improvements-project-id

# GitHub API
GITHUB_TOKEN=your-github-token

# Label Configuration (all configurable)
LABEL_SOURCE_USER=source:user
LABEL_SOURCE_OPP_AGENT=source:opportunity-agent
LABEL_SURFACE_SOLUTIONS=surface:solutions
LABEL_SURFACE_APP=surface:app
LABEL_SURFACE_BRIDGE=surface:bridge
```

## Usage

### As a Library

```python
from agents.linear_agent import LinearAgentCore, AgentConfig
from agents.linear_agent.models import LinearIssue

# Initialize
config = AgentConfig.from_env()
core = LinearAgentCore(config)

# Triage an issue
issue = LinearIssue(
    id="issue-123",
    identifier="MAP-123",
    title="Mirror onboarding to MCP-GUI",
    description="Bridge work to move flow to mapache.app",
)

result = core.triage(issue)
print(f"Surface: {result.surfaces}")
print(f"Size: {result.size}")
print(f"Route: {result.route}")
print(f"Priority: {result.priority_score}")
```

### With the Full Agent (ADK)

```python
from agents.linear_agent.app import LinearProductManagementAgent

async with LinearProductManagementAgent() as agent:
    # Triage all candidates
    results = await agent.triage()
    
    # Get top recommended items
    next_items = await agent.next_items(count=5)
    
    # Inspect a specific issue
    details = await agent.inspect("MAP-123")
    
    # Prepare Copilot task
    brief = await agent.prepare_copilot_task("issue-id")
```

### Slack Bot Interface

The agent exposes methods for Slack bot integration:

- `/linear-agent triage` - Triage all candidate issues
- `/linear-agent next` - Get top N recommended issues
- `/linear-agent inspect <issue-key>` - Inspect a specific issue
- `/linear-agent clean-project <project-key>` - Clean and prioritize a project

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run only new agent tests
pytest tests/agents/ -v

# With coverage
pytest tests/ --cov=agents --cov=linear_agent
```

## Deployment

Deploy to Google Vertex AI Agent Engine:

1. Configure `app.yaml` for Cloud Run
2. Deploy using gcloud:
   ```bash
   gcloud run deploy linear-agent --source .
   ```

## License

MIT License - see LICENSE file for details.
