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
