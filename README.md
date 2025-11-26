# Linear Agent

Autonomous Linear agent for issue management with self-learning, GitHub integration, and multi-agent orchestration.

## Features
- Structured JSON logging with contextual metadata
- Linear GraphQL client with exponential backoff and webhook validation helpers
- GitHub integration for linking pull requests and commenting on issues
- Self-learning recorder that captures audit events and produces improvement suggestions
- Health monitoring and rotation awareness based on quotas
- Testable, dependency-injected design for extensibility

## Quickstart
1. Configure the agent using environment-derived values:
   ```python
   from linear_agent import AgentSettings, GitHubSettings, LinearSettings
   from linear_agent.github_integration import GitHubIntegration
   from linear_agent.linear_client import LinearClient
   from linear_agent.orchestrator import AgentOrchestrator
   from linear_agent.self_learning import SelfLearningRecorder
   from linear_agent.storage import FileStorage

   settings = AgentSettings(
       linear=LinearSettings(api_key="<linear-token>", webhook_secret="<optional-secret>"),
       github=GitHubSettings(token="<github-token>", default_repo="org/repo"),
   )
   storage = FileStorage(settings.storage)
   orchestrator = AgentOrchestrator(
       settings=settings,
       linear_client=LinearClient(settings.linear, session=<requests-session>),
       github=GitHubIntegration(settings.github, session=<requests-session>),
       learning=SelfLearningRecorder(storage),
   )
   ```

2. Handle incoming webhooks:
   ```python
   orchestrator.handle_webhook(payload, signature)
   ```

3. Create Linear issues and link GitHub pull requests:
   ```python
   orchestrator.create_issue_and_link_pr(team_id="team-id", title="Bug", description="Details", repo="org/repo", pull_number=42)
   ```

4. Generate improvement suggestions from recent audit history:
   ```python
   orchestrator.generate_improvement_suggestions()
   ```

## Testing
Run the test suite with:
```bash
python -m pytest
```
