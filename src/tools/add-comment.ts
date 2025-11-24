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
