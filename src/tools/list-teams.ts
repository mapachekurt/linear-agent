import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';

export const listTeamsTool: MCPTool = {
  name: 'list_teams',
  description: 'List all teams in the Linear workspace',
  inputSchema: {
    type: 'object',
    properties: {}
  }
};

export const createListTeamsHandler = (client: LinearClient): ToolHandler => {
  return async (_args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const teams = await client.listTeams();

      if (teams.length === 0) {
        return ErrorHandler.success('No teams found.');
      }

      const teamList = teams.map(team => {
        const desc = team.description ? `\n  ${team.description}` : '';
        return `- ${team.name} (${team.key})\n  ID: ${team.id}${desc}`;
      }).join('\n\n');

      return ErrorHandler.success(`Found ${teams.length} team(s):\n\n${teamList}`);
    } catch (error) {
      return ErrorHandler.handle(error, 'list_teams');
    }
  };
};
