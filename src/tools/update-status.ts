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
