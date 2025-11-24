#!/bin/bash

# Linear Agent Setup Script
# This script creates a complete Linear MCP agent implementation

set -e

echo "🚀 Setting up Linear Agent..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p src/tools
mkdir -p src/types
mkdir -p src/utils
mkdir -p src/prompts
mkdir -p src/config

# 1. Create package.json
echo "📦 Creating package.json..."
cat > package.json << 'EOF'
{
  "name": "linear-agent",
  "version": "1.0.0",
  "description": "Linear MCP agent for managing Linear issues via Claude",
  "main": "dist/index.js",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsc && node dist/index.js",
    "clean": "rm -rf dist"
  },
  "keywords": ["linear", "mcp", "agent", "claude"],
  "author": "",
  "license": "MIT",
  "dependencies": {
    "@linear/sdk": "^32.0.0",
    "@modelcontextprotocol/sdk": "^0.5.0",
    "dotenv": "^16.4.5",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "typescript": "^5.3.3"
  }
}
EOF

# 2. Create tsconfig.json
echo "⚙️  Creating tsconfig.json..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022"],
    "moduleResolution": "node",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
EOF

# 3. Create .env.example
echo "🔐 Creating .env.example..."
cat > .env.example << 'EOF'
# Linear API Configuration
LINEAR_API_KEY=your_linear_api_key_here
LINEAR_TEAM_ID=your_team_id_here

# Optional: Specific project ID to scope operations
LINEAR_PROJECT_ID=

# Agent Configuration
LOG_LEVEL=info
EOF

# 4. Create .gitignore
echo "🚫 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
package-lock.json
yarn.lock

# Build output
dist/
*.tsbuildinfo

# Environment
.env
.env.local

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF

# 5. Create README.md
echo "📖 Creating README.md..."
cat > README.md << 'EOF'
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
EOF

# 6. Create src/types/linear.ts
echo "📝 Creating src/types/linear.ts..."
cat > src/types/linear.ts << 'EOF'
// Linear API types
export interface LinearIssue {
  id: string;
  identifier: string;
  title: string;
  description?: string;
  priority: number;
  priorityLabel: string;
  state: {
    id: string;
    name: string;
    type: string;
  };
  assignee?: {
    id: string;
    name: string;
    email: string;
  };
  creator: {
    id: string;
    name: string;
  };
  project?: {
    id: string;
    name: string;
  };
  team: {
    id: string;
    name: string;
    key: string;
  };
  labels: Array<{
    id: string;
    name: string;
    color: string;
  }>;
  createdAt: string;
  updatedAt: string;
  url: string;
}

export interface LinearProject {
  id: string;
  name: string;
  description?: string;
  state: string;
  progress: number;
  startDate?: string;
  targetDate?: string;
  team: {
    id: string;
    name: string;
  };
  lead?: {
    id: string;
    name: string;
  };
  url: string;
}

export interface LinearTeam {
  id: string;
  name: string;
  key: string;
  description?: string;
}

export interface LinearUser {
  id: string;
  name: string;
  email: string;
  active: boolean;
}

export interface LinearComment {
  id: string;
  body: string;
  user: {
    id: string;
    name: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface IssueFilter {
  assigneeId?: string;
  creatorId?: string;
  priority?: number;
  stateType?: 'backlog' | 'unstarted' | 'started' | 'completed' | 'canceled';
  labelIds?: string[];
  projectId?: string;
}

export interface IssueCreateInput {
  title: string;
  description?: string;
  priority?: number;
  assigneeId?: string;
  projectId?: string;
  labelIds?: string[];
  stateId?: string;
}

export interface IssueUpdateInput {
  title?: string;
  description?: string;
  priority?: number;
  assigneeId?: string;
  projectId?: string;
  stateId?: string;
  labelIds?: string[];
}
EOF

# 7. Create src/types/mcp.ts
echo "📝 Creating src/types/mcp.ts..."
cat > src/types/mcp.ts << 'EOF'
// MCP types
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

export interface MCPRequest {
  method: string;
  params?: {
    name?: string;
    arguments?: Record<string, any>;
  };
}

export interface MCPResponse {
  content: Array<{
    type: 'text';
    text: string;
  }>;
  isError?: boolean;
}

export interface ToolHandler {
  (args: Record<string, any>): Promise<MCPResponse>;
}
EOF

# 8. Create src/types/agent.ts
echo "📝 Creating src/types/agent.ts..."
cat > src/types/agent.ts << 'EOF'
// Agent configuration types
export interface AgentConfig {
  name: string;
  version: string;
  description: string;
  capabilities: string[];
}

export interface LoggerConfig {
  level: 'debug' | 'info' | 'warn' | 'error';
  timestamp: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface OperationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: ValidationError[];
}
EOF

# 9. Create src/utils/logger.ts
echo "📝 Creating src/utils/logger.ts..."
cat > src/utils/logger.ts << 'EOF'
// Simple logger utility
export class Logger {
  private level: string;

  constructor(level: string = 'info') {
    this.level = level;
  }

  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.level);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex >= currentLevelIndex;
  }

  debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.debug(`[DEBUG] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info(`[INFO] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  error(message: string, error?: any): void {
    if (this.shouldLog('error')) {
      console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, error);
    }
  }
}

export const logger = new Logger(process.env.LOG_LEVEL || 'info');
EOF

# 10. Create src/utils/validator.ts
echo "📝 Creating src/utils/validator.ts..."
cat > src/utils/validator.ts << 'EOF'
import { ValidationError } from '../types/agent.js';

export class Validator {
  static validateRequired(value: any, fieldName: string): ValidationError | null {
    if (value === undefined || value === null || value === '') {
      return {
        field: fieldName,
        message: `${fieldName} is required`
      };
    }
    return null;
  }

  static validateString(value: any, fieldName: string, minLength?: number, maxLength?: number): ValidationError | null {
    if (typeof value !== 'string') {
      return {
        field: fieldName,
        message: `${fieldName} must be a string`
      };
    }
    if (minLength && value.length < minLength) {
      return {
        field: fieldName,
        message: `${fieldName} must be at least ${minLength} characters`
      };
    }
    if (maxLength && value.length > maxLength) {
      return {
        field: fieldName,
        message: `${fieldName} must be at most ${maxLength} characters`
      };
    }
    return null;
  }

  static validateNumber(value: any, fieldName: string, min?: number, max?: number): ValidationError | null {
    if (typeof value !== 'number') {
      return {
        field: fieldName,
        message: `${fieldName} must be a number`
      };
    }
    if (min !== undefined && value < min) {
      return {
        field: fieldName,
        message: `${fieldName} must be at least ${min}`
      };
    }
    if (max !== undefined && value > max) {
      return {
        field: fieldName,
        message: `${fieldName} must be at most ${max}`
      };
    }
    return null;
  }

  static validateEnum(value: any, fieldName: string, allowedValues: any[]): ValidationError | null {
    if (!allowedValues.includes(value)) {
      return {
        field: fieldName,
        message: `${fieldName} must be one of: ${allowedValues.join(', ')}`
      };
    }
    return null;
  }

  static collectErrors(validations: (ValidationError | null)[]): ValidationError[] {
    return validations.filter((v): v is ValidationError => v !== null);
  }
}
EOF

# 11. Create src/utils/error-handler.ts
echo "📝 Creating src/utils/error-handler.ts..."
cat > src/utils/error-handler.ts << 'EOF'
import { MCPResponse } from '../types/mcp.js';
import { logger } from './logger.js';

export class ErrorHandler {
  static handle(error: any, context: string): MCPResponse {
    logger.error(`Error in ${context}:`, error);

    let errorMessage = 'An unexpected error occurred';

    if (error instanceof Error) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    } else if (error?.message) {
      errorMessage = error.message;
    }

    return {
      content: [{
        type: 'text',
        text: `Error: ${errorMessage}`
      }],
      isError: true
    };
  }

  static handleValidationErrors(errors: Array<{ field: string; message: string }>): MCPResponse {
    const errorMessages = errors.map(e => `- ${e.field}: ${e.message}`).join('\n');
    return {
      content: [{
        type: 'text',
        text: `Validation errors:\n${errorMessages}`
      }],
      isError: true
    };
  }

  static success(message: string, data?: any): MCPResponse {
    const text = data ? `${message}\n\n${JSON.stringify(data, null, 2)}` : message;
    return {
      content: [{
        type: 'text',
        text
      }]
    };
  }
}
EOF

# 12. Create src/config/agent-config.ts
echo "📝 Creating src/config/agent-config.ts..."
cat > src/config/agent-config.ts << 'EOF'
import { AgentConfig } from '../types/agent.js';

export const agentConfig: AgentConfig = {
  name: 'Linear Agent',
  version: '1.0.0',
  description: 'MCP agent for managing Linear issues and projects',
  capabilities: [
    'issue_management',
    'project_management',
    'team_management',
    'search',
    'comments'
  ]
};

export const LINEAR_PRIORITY_MAP: Record<number, string> = {
  0: 'No priority',
  1: 'Urgent',
  2: 'High',
  3: 'Medium',
  4: 'Low'
};

export const STATE_TYPES = ['backlog', 'unstarted', 'started', 'completed', 'canceled'] as const;
EOF

# 13. Create src/config/mcp-config.ts
echo "📝 Creating src/config/mcp-config.ts..."
cat > src/config/mcp-config.ts << 'EOF'
export const mcpConfig = {
  serverInfo: {
    name: 'linear-agent',
    version: '1.0.0'
  },
  capabilities: {
    tools: {}
  }
};
EOF

# 14. Create src/prompts/system-prompt.ts
echo "📝 Creating src/prompts/system-prompt.ts..."
cat > src/prompts/system-prompt.ts << 'EOF'
export const SYSTEM_PROMPT = `You are a helpful assistant with access to Linear project management tools.

You can help users:
- List and search issues
- Create and update issues
- Manage issue assignments and status
- Add comments to issues
- Manage projects and teams

When working with Linear:
- Issue identifiers use the format TEAM-NUMBER (e.g., ENG-123)
- Priorities range from 0 (none) to 4 (low), with 1 being urgent
- Always provide clear, actionable information
- Format responses in a readable way
- Include relevant issue URLs when available

Guidelines:
- Ask for clarification if requirements are unclear
- Validate inputs before making changes
- Provide confirmation after successful operations
- Handle errors gracefully with helpful messages
`;
EOF

# 15. Create src/linear-client.ts
echo "📝 Creating src/linear-client.ts..."
cat > src/linear-client.ts << 'EOF'
import { LinearClient as LinearSDK, Issue, Project, Team, User } from '@linear/sdk';
import { LinearIssue, LinearProject, LinearTeam, IssueFilter, IssueCreateInput, IssueUpdateInput } from './types/linear.js';
import { logger } from './utils/logger.js';

export class LinearClient {
  private client: LinearSDK;
  private teamId: string;

  constructor(apiKey: string, teamId: string) {
    this.client = new LinearSDK({ apiKey });
    this.teamId = teamId;
    logger.info('Linear client initialized');
  }

  async listIssues(filter?: IssueFilter, limit: number = 50): Promise<LinearIssue[]> {
    try {
      const filterObj: any = { team: { id: { eq: this.teamId } } };

      if (filter?.assigneeId) {
        filterObj.assignee = { id: { eq: filter.assigneeId } };
      }
      if (filter?.priority !== undefined) {
        filterObj.priority = { eq: filter.priority };
      }
      if (filter?.stateType) {
        filterObj.state = { type: { eq: filter.stateType } };
      }
      if (filter?.projectId) {
        filterObj.project = { id: { eq: filter.projectId } };
      }

      const issues = await this.client.issues({
        filter: filterObj,
        first: limit,
        orderBy: 'updatedAt'
      });

      const result: LinearIssue[] = [];
      for (const issue of issues.nodes) {
        result.push(await this.formatIssue(issue));
      }

      logger.info(`Listed ${result.length} issues`);
      return result;
    } catch (error) {
      logger.error('Error listing issues:', error);
      throw error;
    }
  }

  async getIssue(issueId: string): Promise<LinearIssue> {
    try {
      const issue = await this.client.issue(issueId);
      return await this.formatIssue(issue);
    } catch (error) {
      logger.error(`Error getting issue ${issueId}:`, error);
      throw error;
    }
  }

  async createIssue(input: IssueCreateInput): Promise<LinearIssue> {
    try {
      const payload = await this.client.createIssue({
        teamId: this.teamId,
        title: input.title,
        description: input.description,
        priority: input.priority,
        assigneeId: input.assigneeId,
        projectId: input.projectId,
        labelIds: input.labelIds,
        stateId: input.stateId
      });

      const createdIssue = await payload.issue;
      if (!createdIssue) {
        throw new Error('Failed to create issue');
      }

      logger.info(`Created issue: ${createdIssue.identifier}`);
      return await this.formatIssue(createdIssue);
    } catch (error) {
      logger.error('Error creating issue:', error);
      throw error;
    }
  }

  async updateIssue(issueId: string, input: IssueUpdateInput): Promise<LinearIssue> {
    try {
      const payload = await this.client.updateIssue(issueId, input);
      const updatedIssue = await payload.issue;

      if (!updatedIssue) {
        throw new Error('Failed to update issue');
      }

      logger.info(`Updated issue: ${updatedIssue.identifier}`);
      return await this.formatIssue(updatedIssue);
    } catch (error) {
      logger.error(`Error updating issue ${issueId}:`, error);
      throw error;
    }
  }

  async addComment(issueId: string, body: string): Promise<{ id: string; body: string }> {
    try {
      const payload = await this.client.createComment({
        issueId,
        body
      });

      const comment = await payload.comment;
      if (!comment) {
        throw new Error('Failed to create comment');
      }

      logger.info(`Added comment to issue ${issueId}`);
      return {
        id: comment.id,
        body: comment.body
      };
    } catch (error) {
      logger.error(`Error adding comment to issue ${issueId}:`, error);
      throw error;
    }
  }

  async searchIssues(query: string, limit: number = 20): Promise<LinearIssue[]> {
    try {
      const issues = await this.client.issueSearch(query, {
        first: limit,
        filter: { team: { id: { eq: this.teamId } } }
      });

      const result: LinearIssue[] = [];
      for (const issue of issues.nodes) {
        result.push(await this.formatIssue(issue));
      }

      logger.info(`Found ${result.length} issues matching "${query}"`);
      return result;
    } catch (error) {
      logger.error('Error searching issues:', error);
      throw error;
    }
  }

  async listProjects(limit: number = 50): Promise<LinearProject[]> {
    try {
      const projects = await this.client.projects({
        filter: { team: { id: { eq: this.teamId } } },
        first: limit
      });

      const result: LinearProject[] = [];
      for (const project of projects.nodes) {
        result.push(await this.formatProject(project));
      }

      logger.info(`Listed ${result.length} projects`);
      return result;
    } catch (error) {
      logger.error('Error listing projects:', error);
      throw error;
    }
  }

  async getProject(projectId: string): Promise<LinearProject> {
    try {
      const project = await this.client.project(projectId);
      return await this.formatProject(project);
    } catch (error) {
      logger.error(`Error getting project ${projectId}:`, error);
      throw error;
    }
  }

  async createProject(name: string, description?: string): Promise<LinearProject> {
    try {
      const payload = await this.client.createProject({
        teamIds: [this.teamId],
        name,
        description
      });

      const project = await payload.project;
      if (!project) {
        throw new Error('Failed to create project');
      }

      logger.info(`Created project: ${project.name}`);
      return await this.formatProject(project);
    } catch (error) {
      logger.error('Error creating project:', error);
      throw error;
    }
  }

  async listTeams(): Promise<LinearTeam[]> {
    try {
      const teams = await this.client.teams();
      const result: LinearTeam[] = [];

      for (const team of teams.nodes) {
        result.push({
          id: team.id,
          name: team.name,
          key: team.key,
          description: team.description || undefined
        });
      }

      logger.info(`Listed ${result.length} teams`);
      return result;
    } catch (error) {
      logger.error('Error listing teams:', error);
      throw error;
    }
  }

  private async formatIssue(issue: Issue): Promise<LinearIssue> {
    const [state, assignee, project, team, labels] = await Promise.all([
      issue.state,
      issue.assignee,
      issue.project,
      issue.team,
      issue.labels()
    ]);

    const creator = await issue.creator;

    return {
      id: issue.id,
      identifier: issue.identifier,
      title: issue.title,
      description: issue.description || undefined,
      priority: issue.priority,
      priorityLabel: issue.priorityLabel,
      state: state ? {
        id: state.id,
        name: state.name,
        type: state.type
      } : { id: '', name: 'Unknown', type: 'unknown' },
      assignee: assignee ? {
        id: assignee.id,
        name: assignee.name,
        email: assignee.email
      } : undefined,
      creator: {
        id: creator?.id || '',
        name: creator?.name || 'Unknown'
      },
      project: project ? {
        id: project.id,
        name: project.name
      } : undefined,
      team: {
        id: team.id,
        name: team.name,
        key: team.key
      },
      labels: labels.nodes.map(label => ({
        id: label.id,
        name: label.name,
        color: label.color
      })),
      createdAt: issue.createdAt.toISOString(),
      updatedAt: issue.updatedAt.toISOString(),
      url: issue.url
    };
  }

  private async formatProject(project: Project): Promise<LinearProject> {
    const [team, lead] = await Promise.all([
      project.team,
      project.lead
    ]);

    return {
      id: project.id,
      name: project.name,
      description: project.description || undefined,
      state: project.state,
      progress: project.progress,
      startDate: project.startDate?.toISOString(),
      targetDate: project.targetDate?.toISOString(),
      team: {
        id: team.id,
        name: team.name
      },
      lead: lead ? {
        id: lead.id,
        name: lead.name
      } : undefined,
      url: project.url
    };
  }
}
EOF

# 16. Create src/tools/list-issues.ts
echo "📝 Creating src/tools/list-issues.ts..."
cat > src/tools/list-issues.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';

export const listIssuesTool: MCPTool = {
  name: 'list_issues',
  description: 'List issues from Linear with optional filtering',
  inputSchema: {
    type: 'object',
    properties: {
      assigneeId: {
        type: 'string',
        description: 'Filter by assignee user ID'
      },
      priority: {
        type: 'number',
        description: 'Filter by priority (0-4, where 1 is urgent, 4 is low)'
      },
      stateType: {
        type: 'string',
        enum: ['backlog', 'unstarted', 'started', 'completed', 'canceled'],
        description: 'Filter by state type'
      },
      projectId: {
        type: 'string',
        description: 'Filter by project ID'
      },
      limit: {
        type: 'number',
        description: 'Maximum number of issues to return (default: 50)'
      }
    }
  }
};

export const createListIssuesHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const issues = await client.listIssues({
        assigneeId: args.assigneeId,
        priority: args.priority,
        stateType: args.stateType,
        projectId: args.projectId
      }, args.limit);

      if (issues.length === 0) {
        return ErrorHandler.success('No issues found matching the criteria.');
      }

      const issueList = issues.map(issue => {
        const assignee = issue.assignee ? ` | Assigned to: ${issue.assignee.name}` : '';
        const project = issue.project ? ` | Project: ${issue.project.name}` : '';
        return `- ${issue.identifier}: ${issue.title}\n  Status: ${issue.state.name} | Priority: ${issue.priorityLabel}${assignee}${project}\n  ${issue.url}`;
      }).join('\n\n');

      return ErrorHandler.success(`Found ${issues.length} issue(s):\n\n${issueList}`);
    } catch (error) {
      return ErrorHandler.handle(error, 'list_issues');
    }
  };
};
EOF

# 17. Create src/tools/get-issue.ts
echo "📝 Creating src/tools/get-issue.ts..."
cat > src/tools/get-issue.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const getIssueTool: MCPTool = {
  name: 'get_issue',
  description: 'Get detailed information about a specific Linear issue',
  inputSchema: {
    type: 'object',
    properties: {
      issueId: {
        type: 'string',
        description: 'The issue ID or identifier (e.g., "ENG-123")'
      }
    },
    required: ['issueId']
  }
};

export const createGetIssueHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.issueId, 'issueId')
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issue = await client.getIssue(args.issueId);

      const details = `
# ${issue.identifier}: ${issue.title}

**Status:** ${issue.state.name}
**Priority:** ${issue.priorityLabel}
**Created:** ${new Date(issue.createdAt).toLocaleDateString()}
**Updated:** ${new Date(issue.updatedAt).toLocaleDateString()}
**Creator:** ${issue.creator.name}
${issue.assignee ? `**Assignee:** ${issue.assignee.name} (${issue.assignee.email})` : '**Assignee:** Unassigned'}
${issue.project ? `**Project:** ${issue.project.name}` : ''}
${issue.labels.length > 0 ? `**Labels:** ${issue.labels.map(l => l.name).join(', ')}` : ''}

## Description
${issue.description || 'No description provided'}

**URL:** ${issue.url}
      `.trim();

      return ErrorHandler.success(details);
    } catch (error) {
      return ErrorHandler.handle(error, 'get_issue');
    }
  };
};
EOF

# 18. Create src/tools/create-issue.ts
echo "📝 Creating src/tools/create-issue.ts..."
cat > src/tools/create-issue.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const createIssueTool: MCPTool = {
  name: 'create_issue',
  description: 'Create a new Linear issue',
  inputSchema: {
    type: 'object',
    properties: {
      title: {
        type: 'string',
        description: 'Issue title'
      },
      description: {
        type: 'string',
        description: 'Issue description (supports Markdown)'
      },
      priority: {
        type: 'number',
        description: 'Priority (0-4, where 1 is urgent, 4 is low)'
      },
      assigneeId: {
        type: 'string',
        description: 'User ID to assign the issue to'
      },
      projectId: {
        type: 'string',
        description: 'Project ID to add the issue to'
      }
    },
    required: ['title']
  }
};

export const createCreateIssueHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.title, 'title'),
        Validator.validateString(args.title, 'title', 1, 255)
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issue = await client.createIssue({
        title: args.title,
        description: args.description,
        priority: args.priority,
        assigneeId: args.assigneeId,
        projectId: args.projectId
      });

      return ErrorHandler.success(
        `✅ Created issue ${issue.identifier}: ${issue.title}\n\nURL: ${issue.url}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'create_issue');
    }
  };
};
EOF

# 19. Create src/tools/update-issue.ts
echo "📝 Creating src/tools/update-issue.ts..."
cat > src/tools/update-issue.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const updateIssueTool: MCPTool = {
  name: 'update_issue',
  description: 'Update an existing Linear issue',
  inputSchema: {
    type: 'object',
    properties: {
      issueId: {
        type: 'string',
        description: 'The issue ID or identifier to update'
      },
      title: {
        type: 'string',
        description: 'New issue title'
      },
      description: {
        type: 'string',
        description: 'New issue description'
      },
      priority: {
        type: 'number',
        description: 'New priority (0-4)'
      },
      stateId: {
        type: 'string',
        description: 'New state ID'
      },
      assigneeId: {
        type: 'string',
        description: 'New assignee user ID'
      }
    },
    required: ['issueId']
  }
};

export const createUpdateIssueHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.issueId, 'issueId')
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issue = await client.updateIssue(args.issueId, {
        title: args.title,
        description: args.description,
        priority: args.priority,
        stateId: args.stateId,
        assigneeId: args.assigneeId
      });

      return ErrorHandler.success(
        `✅ Updated issue ${issue.identifier}: ${issue.title}\n\nURL: ${issue.url}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'update_issue');
    }
  };
};
EOF

# 20. Create src/tools/add-comment.ts
echo "📝 Creating src/tools/add-comment.ts..."
cat > src/tools/add-comment.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const addCommentTool: MCPTool = {
  name: 'add_comment',
  description: 'Add a comment to a Linear issue',
  inputSchema: {
    type: 'object',
    properties: {
      issueId: {
        type: 'string',
        description: 'The issue ID or identifier'
      },
      body: {
        type: 'string',
        description: 'Comment text (supports Markdown)'
      }
    },
    required: ['issueId', 'body']
  }
};

export const createAddCommentHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.issueId, 'issueId'),
        Validator.validateRequired(args.body, 'body'),
        Validator.validateString(args.body, 'body', 1)
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const comment = await client.addComment(args.issueId, args.body);

      return ErrorHandler.success(
        `✅ Added comment to issue ${args.issueId}\n\nComment ID: ${comment.id}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'add_comment');
    }
  };
};
EOF

# 21. Create src/tools/search-issues.ts
echo "📝 Creating src/tools/search-issues.ts..."
cat > src/tools/search-issues.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const searchIssuesTool: MCPTool = {
  name: 'search_issues',
  description: 'Search Linear issues by text query',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query text'
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results (default: 20)'
      }
    },
    required: ['query']
  }
};

export const createSearchIssuesHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.query, 'query'),
        Validator.validateString(args.query, 'query', 1)
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issues = await client.searchIssues(args.query, args.limit);

      if (issues.length === 0) {
        return ErrorHandler.success(`No issues found matching "${args.query}"`);
      }

      const issueList = issues.map(issue => {
        return `- ${issue.identifier}: ${issue.title}\n  Status: ${issue.state.name} | Priority: ${issue.priorityLabel}\n  ${issue.url}`;
      }).join('\n\n');

      return ErrorHandler.success(
        `Found ${issues.length} issue(s) matching "${args.query}":\n\n${issueList}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'search_issues');
    }
  };
};
EOF

# 22. Create src/tools/assign-issue.ts
echo "📝 Creating src/tools/assign-issue.ts..."
cat > src/tools/assign-issue.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const assignIssueTool: MCPTool = {
  name: 'assign_issue',
  description: 'Assign a Linear issue to a user',
  inputSchema: {
    type: 'object',
    properties: {
      issueId: {
        type: 'string',
        description: 'The issue ID or identifier'
      },
      assigneeId: {
        type: 'string',
        description: 'User ID to assign the issue to (use empty string to unassign)'
      }
    },
    required: ['issueId', 'assigneeId']
  }
};

export const createAssignIssueHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.issueId, 'issueId')
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const assigneeId = args.assigneeId === '' ? null : args.assigneeId;
      const issue = await client.updateIssue(args.issueId, { assigneeId: assigneeId as any });

      const message = assigneeId
        ? `✅ Assigned issue ${issue.identifier} to ${issue.assignee?.name}`
        : `✅ Unassigned issue ${issue.identifier}`;

      return ErrorHandler.success(`${message}\n\nURL: ${issue.url}`);
    } catch (error) {
      return ErrorHandler.handle(error, 'assign_issue');
    }
  };
};
EOF

# 23. Create src/tools/update-status.ts
echo "📝 Creating src/tools/update-status.ts..."
cat > src/tools/update-status.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const updateStatusTool: MCPTool = {
  name: 'update_status',
  description: 'Update the status of a Linear issue',
  inputSchema: {
    type: 'object',
    properties: {
      issueId: {
        type: 'string',
        description: 'The issue ID or identifier'
      },
      stateId: {
        type: 'string',
        description: 'The state ID to set'
      }
    },
    required: ['issueId', 'stateId']
  }
};

export const createUpdateStatusHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.issueId, 'issueId'),
        Validator.validateRequired(args.stateId, 'stateId')
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issue = await client.updateIssue(args.issueId, {
        stateId: args.stateId
      });

      return ErrorHandler.success(
        `✅ Updated ${issue.identifier} status to: ${issue.state.name}\n\nURL: ${issue.url}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'update_status');
    }
  };
};
EOF

# 24. Create src/tools/list-projects.ts
echo "📝 Creating src/tools/list-projects.ts..."
cat > src/tools/list-projects.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';

export const listProjectsTool: MCPTool = {
  name: 'list_projects',
  description: 'List all projects in the Linear team',
  inputSchema: {
    type: 'object',
    properties: {
      limit: {
        type: 'number',
        description: 'Maximum number of projects to return (default: 50)'
      }
    }
  }
};

export const createListProjectsHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const projects = await client.listProjects(args.limit);

      if (projects.length === 0) {
        return ErrorHandler.success('No projects found.');
      }

      const projectList = projects.map(project => {
        const lead = project.lead ? ` | Lead: ${project.lead.name}` : '';
        const dates = project.targetDate
          ? ` | Target: ${new Date(project.targetDate).toLocaleDateString()}`
          : '';
        return `- ${project.name} (${project.state})\n  Progress: ${Math.round(project.progress)}%${lead}${dates}\n  ${project.url}`;
      }).join('\n\n');

      return ErrorHandler.success(`Found ${projects.length} project(s):\n\n${projectList}`);
    } catch (error) {
      return ErrorHandler.handle(error, 'list_projects');
    }
  };
};
EOF

# 25. Create src/tools/get-project.ts
echo "📝 Creating src/tools/get-project.ts..."
cat > src/tools/get-project.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const getProjectTool: MCPTool = {
  name: 'get_project',
  description: 'Get detailed information about a specific Linear project',
  inputSchema: {
    type: 'object',
    properties: {
      projectId: {
        type: 'string',
        description: 'The project ID'
      }
    },
    required: ['projectId']
  }
};

export const createGetProjectHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.projectId, 'projectId')
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const project = await client.getProject(args.projectId);

      const details = `
# ${project.name}

**State:** ${project.state}
**Progress:** ${Math.round(project.progress)}%
**Team:** ${project.team.name}
${project.lead ? `**Lead:** ${project.lead.name}` : ''}
${project.startDate ? `**Start Date:** ${new Date(project.startDate).toLocaleDateString()}` : ''}
${project.targetDate ? `**Target Date:** ${new Date(project.targetDate).toLocaleDateString()}` : ''}

## Description
${project.description || 'No description provided'}

**URL:** ${project.url}
      `.trim();

      return ErrorHandler.success(details);
    } catch (error) {
      return ErrorHandler.handle(error, 'get_project');
    }
  };
};
EOF

# 26. Create src/tools/create-project.ts
echo "📝 Creating src/tools/create-project.ts..."
cat > src/tools/create-project.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const createProjectTool: MCPTool = {
  name: 'create_project',
  description: 'Create a new Linear project',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'Project name'
      },
      description: {
        type: 'string',
        description: 'Project description (supports Markdown)'
      }
    },
    required: ['name']
  }
};

export const createCreateProjectHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.name, 'name'),
        Validator.validateString(args.name, 'name', 1, 255)
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const project = await client.createProject(args.name, args.description);

      return ErrorHandler.success(
        `✅ Created project: ${project.name}\n\nURL: ${project.url}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'create_project');
    }
  };
};
EOF

# 27. Create src/tools/list-teams.ts
echo "📝 Creating src/tools/list-teams.ts..."
cat > src/tools/list-teams.ts << 'EOF'
import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';

export const listTeamsTool: MCPTool = {
  name: 'list_teams',
  description: 'List all teams in the Linear workspace',
  inputSchema: {
    type: 'object',
    properties: {}
  }
};

export const createListTeamsHandler = (client: LinearClient): ToolHandler => {
  return async (_args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const teams = await client.listTeams();

      if (teams.length === 0) {
        return ErrorHandler.success('No teams found.');
      }

      const teamList = teams.map(team => {
        const desc = team.description ? `\n  ${team.description}` : '';
        return `- ${team.name} (${team.key})\n  ID: ${team.id}${desc}`;
      }).join('\n\n');

      return ErrorHandler.success(`Found ${teams.length} team(s):\n\n${teamList}`);
    } catch (error) {
      return ErrorHandler.handle(error, 'list_teams');
    }
  };
};
EOF

# 28. Create src/tools/index.ts
echo "📝 Creating src/tools/index.ts..."
cat > src/tools/index.ts << 'EOF'
// Tool exports
export { listIssuesTool, createListIssuesHandler } from './list-issues.js';
export { getIssueTool, createGetIssueHandler } from './get-issue.js';
export { createIssueTool, createCreateIssueHandler } from './create-issue.js';
export { updateIssueTool, createUpdateIssueHandler } from './update-issue.js';
export { addCommentTool, createAddCommentHandler } from './add-comment.js';
export { searchIssuesTool, createSearchIssuesHandler } from './search-issues.js';
export { assignIssueTool, createAssignIssueHandler } from './assign-issue.js';
export { updateStatusTool, createUpdateStatusHandler } from './update-status.js';
export { listProjectsTool, createListProjectsHandler } from './list-projects.js';
export { getProjectTool, createGetProjectHandler } from './get-project.js';
export { createProjectTool, createCreateProjectHandler } from './create-project.js';
export { listTeamsTool, createListTeamsHandler } from './list-teams.js';
EOF

# 29. Create src/server.ts
echo "📝 Creating src/server.ts..."
cat > src/server.ts << 'EOF'
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from '@modelcontextprotocol/sdk/types.js';
import { LinearClient } from './linear-client.js';
import { MCPTool, ToolHandler } from './types/mcp.js';
import { logger } from './utils/logger.js';
import { mcpConfig } from './config/mcp-config.js';
import * as tools from './tools/index.js';

export class MCPServer {
  private server: Server;
  private tools: Map<string, MCPTool>;
  private handlers: Map<string, ToolHandler>;

  constructor(private linearClient: LinearClient) {
    this.server = new Server(mcpConfig.serverInfo, mcpConfig.capabilities);
    this.tools = new Map();
    this.handlers = new Map();
    this.setupHandlers();
  }

  private setupHandlers(): void {
    // Register all tools
    this.registerTool(tools.listIssuesTool, tools.createListIssuesHandler(this.linearClient));
    this.registerTool(tools.getIssueTool, tools.createGetIssueHandler(this.linearClient));
    this.registerTool(tools.createIssueTool, tools.createCreateIssueHandler(this.linearClient));
    this.registerTool(tools.updateIssueTool, tools.createUpdateIssueHandler(this.linearClient));
    this.registerTool(tools.addCommentTool, tools.createAddCommentHandler(this.linearClient));
    this.registerTool(tools.searchIssuesTool, tools.createSearchIssuesHandler(this.linearClient));
    this.registerTool(tools.assignIssueTool, tools.createAssignIssueHandler(this.linearClient));
    this.registerTool(tools.updateStatusTool, tools.createUpdateStatusHandler(this.linearClient));
    this.registerTool(tools.listProjectsTool, tools.createListProjectsHandler(this.linearClient));
    this.registerTool(tools.getProjectTool, tools.createGetProjectHandler(this.linearClient));
    this.registerTool(tools.createProjectTool, tools.createCreateProjectHandler(this.linearClient));
    this.registerTool(tools.listTeamsTool, tools.createListTeamsHandler(this.linearClient));

    // Handle list tools request
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: Array.from(this.tools.values())
    }));

    // Handle tool execution
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const handler = this.handlers.get(toolName);

      if (!handler) {
        throw new Error(`Unknown tool: ${toolName}`);
      }

      logger.info(`Executing tool: ${toolName}`);
      return await handler(request.params.arguments || {});
    });

    logger.info(`Registered ${this.tools.size} tools`);
  }

  private registerTool(tool: MCPTool, handler: ToolHandler): void {
    this.tools.set(tool.name, tool);
    this.handlers.set(tool.name, handler);
  }

  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    logger.info('MCP Server started and connected via stdio');
  }
}
EOF

# 30. Create src/index.ts
echo "📝 Creating src/index.ts..."
cat > src/index.ts << 'EOF'
import dotenv from 'dotenv';
import { LinearClient } from './linear-client.js';
import { MCPServer } from './server.js';
import { logger } from './utils/logger.js';

// Load environment variables
dotenv.config();

async function main() {
  try {
    // Validate required environment variables
    const apiKey = process.env.LINEAR_API_KEY;
    const teamId = process.env.LINEAR_TEAM_ID;

    if (!apiKey) {
      throw new Error('LINEAR_API_KEY environment variable is required');
    }

    if (!teamId) {
      throw new Error('LINEAR_TEAM_ID environment variable is required');
    }

    logger.info('Starting Linear MCP Agent...');

    // Initialize Linear client
    const linearClient = new LinearClient(apiKey, teamId);

    // Create and start MCP server
    const server = new MCPServer(linearClient);
    await server.start();

    logger.info('Linear MCP Agent is ready');
  } catch (error) {
    logger.error('Failed to start Linear MCP Agent:', error);
    process.exit(1);
  }
}

main();
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Install dependencies:"
echo "   npm install"
echo ""
echo "2. Configure environment:"
echo "   cp .env.example .env"
echo "   # Edit .env and add your LINEAR_API_KEY and LINEAR_TEAM_ID"
echo ""
echo "3. Build the project:"
echo "   npm run build"
echo ""
echo "4. Test the agent:"
echo "   npm start"
echo ""
echo "5. Configure Claude Desktop (see README.md for details)"
echo ""
echo "🎉 Your Linear agent is ready to use!"
