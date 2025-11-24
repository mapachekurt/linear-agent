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
