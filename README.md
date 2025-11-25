# Linear Agent

Autonomous Linear agent for issue management with self-learning, GitHub integration, and multi-agent orchestration.

## Features

### Core CRUD Operations
- List teams in your Linear workspace
- List, create, update, and read issues
- Create sub-issues (child issues)
- Add comments to issues
- Add emoji reactions to issues
- Add attachments/resource links to issues

### GitHub Integration
- Connect to GitHub API
- Retrieve pull request information
- Link GitHub PRs to Linear issues as attachments

### Health Monitoring
- Track API quota consumption
- Detect when quota is exhausted
- Report health status (healthy/degraded/unhealthy)

### Self-Learning Module
- Record successful actions to audit log (JSONL format)
- Record failures with auto-generated improvement suggestions
- Analyze failure patterns and generate recommendations
- Generate comprehensive learning reports

### Configuration
- Dataclass-based settings (LinearSettings, GitHubSettings, StorageSettings)
- Environment variable support via `.env` file
- Configurable backoff policies for rate limiting

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root:

```env
# Linear API
LINEAR_API_KEY=your-linear-api-key
LINEAR_API_URL=https://api.linear.app/graphql
LINEAR_TIMEOUT=30.0

# GitHub API
GITHUB_TOKEN=your-github-token
GITHUB_API_URL=https://api.github.com
GITHUB_TIMEOUT=30.0

# Storage
AUDIT_LOG_PATH=audit.jsonl
STATE_FILE_PATH=agent_state.json
MAX_AUDIT_ENTRIES=10000
```

## Usage

### As a Library

```python
import asyncio
from linear_agent import Orchestrator, AgentConfig

async def main():
    config = AgentConfig.from_env()
    
    async with Orchestrator(config) as agent:
        # List teams
        teams = await agent.list_teams()
        for team in teams:
            print(f"Team: {team.name} ({team.key})")
        
        # Create an issue
        issue = await agent.create_issue(
            team_id=teams[0].id,
            title="New Issue",
            description="Created by Linear Agent",
            priority=2,
        )
        print(f"Created: {issue.identifier}")
        
        # Add a comment
        comment = await agent.add_comment(issue.id, "Hello from Linear Agent!")
        
        # Link a GitHub PR
        attachment = await agent.link_github_pr_to_issue(
            issue_id=issue.id,
            owner="myorg",
            repo="myrepo",
            pr_number=42,
        )
        
        # Check health
        report = await agent.check_health()
        print(report.summary())
        
        # Get learning insights
        summary = await agent.get_improvement_summary()
        print(summary)

asyncio.run(main())
```

### CLI

```bash
# Health check
linear-agent health

# List teams
linear-agent teams

# List issues
linear-agent issues --team <team-id>

# Show learning summary
linear-agent learn
```

## Architecture

The agent is structured into the following modules:

- **config.py**: Dataclass-based configuration management
- **client.py**: Async Linear GraphQL API client
- **github_client.py**: Async GitHub REST API client
- **health.py**: Health monitoring and quota tracking
- **self_learning.py**: Action logging and failure analysis
- **storage.py**: Persistent storage (JSONL audit log, JSON state)
- **orchestrator.py**: Main coordinator that ties everything together
- **cli.py**: Command-line interface

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Running Linter

```bash
ruff check linear_agent/ tests/
```

### Type Checking

```bash
mypy linear_agent/
```

## License

MIT License - see LICENSE file for details.
