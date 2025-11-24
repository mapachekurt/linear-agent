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
