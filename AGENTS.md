# Agent Guidelines for Linear Agent Repository

## Overview
This repository contains an autonomous Linear agent for issue management with self-learning capabilities, GitHub integration, and multi-agent orchestration support. All coding agents working on this project must follow these guidelines.

## Core Principles

### 1. Code Quality Standards
- Write clean, well-documented, idiomatic Python code
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Maintain comprehensive docstrings for all modules, classes, and functions
- Keep functions focused and single-purpose
- Aim for test coverage above 80%

### 2. Architecture & Modularity
- Maintain clear separation of concerns
- Use dependency injection for external services (Linear API, GitHub API)
- Keep modules loosely coupled and highly cohesive
- Design for extensibility - new features should be easy to add
- Follow the single responsibility principle

### 3. Error Handling & Logging
- Use structured logging (JSON format preferred)
- Log all API calls, errors, and state changes
- Implement graceful degradation for non-critical failures
- Provide actionable error messages
- Never silently swallow exceptions

### 4. Testing Requirements
- Write unit tests for all business logic
- Include integration tests for API interactions
- Mock external dependencies appropriately
- Test edge cases and error scenarios
- Keep tests fast and deterministic

## Project-Specific Rules

### Linear Integration
- Always use the official Linear SDK/API
- Respect rate limits (implement exponential backoff)
- Validate all Linear webhook payloads
- Store Linear issue references securely
- Follow Linear's agent best practices (see docs)

### GitHub Integration
- Use Linear's native GitHub integration features
- Follow branch naming convention: `feature/`, `bugfix/`, `agent/`
- Include Linear issue key in commit messages
- Keep PRs focused and reviewable
- Auto-link PRs to Linear issues

### Self-Learning System
- Log all agent actions to persistent storage
- Record failures with full context
- Generate improvement suggestions automatically
- Create feedback tickets in Linear for review
- Maintain audit trail for all learning events

### Agent Rotation
- Implement health checks and quota monitoring
- Support graceful handoff to backup agents
- Preserve full context during rotation
- Notify workspace on rotation events
- Document rotation triggers and recovery procedures

## Branching & Merge Strategy

### For Multi-Agent Development
- Each coding agent should work on its own feature branch
- Branch naming: `<agent-name>/<feature-name>` (e.g., `codex/linear-webhook`, `claude/self-learning`)
- Never commit directly to `main`
- Open PR when feature is ready for review
- Wait for CI/CD checks to pass
- Require at least one approval before merge

### Merge Conflicts
- Resolve conflicts by understanding both changes
- Preserve functionality from all branches when possible
- Test thoroughly after conflict resolution
- Document any breaking changes in PR description

## Security & Privacy

### API Keys & Secrets
- Never commit API keys or secrets
- Use environment variables or secret managers
- Rotate credentials regularly
- Scope permissions to minimum required

### Data Handling
- Treat all Linear data as sensitive
- Implement proper access controls
- Log data access for audit purposes
- Follow data retention policies

## Documentation

### Code Documentation
- Update README.md with any new features
- Document all configuration options
- Provide usage examples
- Keep API documentation current

### Agent Behavior
- Document all agent decision points
- Explain error recovery strategies
- Maintain changelog for agent improvements
- Document known limitations

## Continuous Improvement

### When Adding Features
- Consider backward compatibility
- Update tests and documentation
- Add configuration options where appropriate
- Think about monitoring and observability

### When Fixing Bugs
- Add regression test
- Document root cause analysis
- Update error handling if needed
- Consider if similar bugs exist elsewhere

## Communication

### PR Descriptions
- Explain what changed and why
- Link to related Linear issues
- Include testing steps
- Note any breaking changes
- Add screenshots/logs if helpful

### Commit Messages
- Use conventional commits format
- Keep first line under 72 characters
- Provide context in commit body
- Reference Linear issues

## Performance

- Optimize for API call efficiency
- Implement caching where appropriate
- Monitor memory usage
- Profile code for bottlenecks
- Consider rate limits and quotas

## Compliance

- Check this file regularly for updates
- If guidelines change, review your code
- Flag conflicts between guidelines and implementation
- Propose improvements to these guidelines via PR

---

**Last Updated:** 2025-01-24
**Maintainer:** @mapachekurt
