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
