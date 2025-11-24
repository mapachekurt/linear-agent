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
