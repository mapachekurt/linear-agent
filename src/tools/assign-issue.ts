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
