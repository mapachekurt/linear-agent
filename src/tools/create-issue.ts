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
