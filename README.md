# Linear Product Management Agent

This repository hosts the Mapache Linear Product Management Agent described in [AgentSpec.md](./AgentSpec.md). The agent runs on Google Vertex AI Agent Engine (Python ADK) and acts as the backlog brain for Mapache by shaping, classifying, prioritizing, and routing Linear issues.

## Capabilities
- Shapes Linear tickets into a Lean product format (problem, impact, scope, acceptance criteria, owner).
- Classifies tickets by surface (solutions/app/bridge), size, and source with confidence scoring.
- Prioritizes according to the Mapache funnel (solutions → app → bridge) and source weighting.
- Routes work to `route:copilot-agent`, `route:copilot-chat`, or `route:manual` depending on clarity and size.
- Validates Linear webhooks and emits action plans consumable by Copilot coding agents and reviewers.

## Package Layout
```
agents/linear_agent/
  classification.py   # Surface/size/source classification
  connectors.py       # Linear webhook validation and GitHub summary helpers
  models.py           # Core dataclasses for Lean tickets and decisions
  orchestrator.py     # ADK-facing agent orchestrator
  prioritization.py   # Mapache funnel scoring
  routing.py          # Routing decisions for Copilot vs manual
  shaping.py          # Lean ticket shaping utilities
```

## Usage
```python
from agents.linear_agent import LinearConnector, GitHubConnector, LinearProductAgent

agent = LinearProductAgent(linear=LinearConnector(webhook_secret="secret"), github=GitHubConnector())

plan = agent.process_webhook(payload=incoming_payload, signature="hex-hmac")
print(plan.routing.destination)
```

## Testing
Run unit tests locally:
```bash
python -m pytest
```
