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
