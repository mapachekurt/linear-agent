# Linear Agent

A Model Context Protocol (MCP) agent for managing Linear issues through Claude.

## Features

- 🎯 List, search, and filter issues
- ✏️ Create and update issues
- 💬 Add comments to issues
- 📊 Manage projects and teams
- 🔄 Update issue status and assignments
- 🤖 Natural language interface via Claude

## Prerequisites

- Node.js 18 or higher
- Linear account with API access
- Linear API key

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your LINEAR_API_KEY and LINEAR_TEAM_ID
```

3. Build the project:
```bash
npm run build
```

4. Run the agent:
```bash
npm start
```

## Getting Your Linear API Key

1. Go to https://linear.app/settings/api
2. Create a new Personal API Key
3. Copy the key to your `.env` file

## Getting Your Team ID

You can find your team ID by:
1. Using the `list-teams` tool after starting the agent
2. Or checking your Linear URL: `https://linear.app/<team-key>/...`

## MCP Configuration

Add this to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "linear-agent": {
      "command": "node",
      "args": ["/absolute/path/to/linear-agent/dist/index.js"],
      "env": {
        "LINEAR_API_KEY": "your_api_key_here",
        "LINEAR_TEAM_ID": "your_team_id_here"
      }
    }
  }
}
```

## Available Tools

- `list_issues` - List issues with filtering options
- `get_issue` - Get detailed information about a specific issue
- `create_issue` - Create a new issue
- `update_issue` - Update an existing issue
- `add_comment` - Add a comment to an issue
- `search_issues` - Search issues by text
- `assign_issue` - Assign an issue to a team member
- `update_status` - Update issue status
- `list_projects` - List all projects
- `get_project` - Get project details
- `create_project` - Create a new project
- `list_teams` - List all teams

## Usage Examples

Once configured with Claude Desktop, you can use natural language:

- "List all high priority bugs in my team"
- "Create an issue for implementing dark mode"
- "Show me issue ABC-123"
- "Add a comment to issue ABC-123 saying the fix is ready"
- "Assign issue ABC-123 to John"
- "Update ABC-123 status to In Progress"

## Development

```bash
# Build
npm run build

# Clean build artifacts
npm run clean

# Development mode (build + run)
npm run dev
```

## License

MIT
