# Linear Agent Specification

This document describes the responsibilities for the Mapache Linear Product Management Agent. It is the authoritative source of truth for the agent implementation.

## Platform
- Runs on Google Vertex AI Agent Engine using the Python ADK.
- Provides ADK-compatible tool metadata so coordinators can invoke the agent.

## Integrations
- Linear: MCP plus REST API/webhooks.
- GitHub: MCP (for Copilot agents) and REST/GraphQL.
- Slack: handled by a separate bot; this agent only accepts Slack-provided context.

## Business Model Context
- **mapache.solutions**: GUI-first, AI-native micro-SaaS apps.
- **mapache.app**: conversational OS that reuses GUIs via MCP-GUI.

## Core Jobs
1. Shape and clean up Linear tickets into a Lean format (problem, impact, scope, acceptance criteria, owner).
2. Classify tickets by surface (solutions/app/bridge), size, and source.
3. Prioritize tickets using the Mapache funnel (solutions → app → bridge).
4. Decide routing: `route:copilot-agent` vs `route:copilot-chat` vs `route:manual`.
5. Provide action outputs suitable for downstream Copilot coding agents and manual reviewers.

## Operational Behavior
- Validate incoming Linear webhooks.
- Maintain lightweight state for auditability.
- Expose health information for rotation.
- Remain fully testable with mocked integrations.
