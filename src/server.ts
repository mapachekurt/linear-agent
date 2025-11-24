import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from '@modelcontextprotocol/sdk/types.js';
import { LinearClient } from './linear-client.js';
import { MCPTool, ToolHandler } from './types/mcp.js';
import { logger } from './utils/logger.js';
import { mcpConfig } from './config/mcp-config.js';
import * as tools from './tools/index.js';

export class MCPServer {
  private server: Server;
  private tools: Map<string, MCPTool>;
  private handlers: Map<string, ToolHandler>;

  constructor(private linearClient: LinearClient) {
    this.server = new Server(mcpConfig.serverInfo, mcpConfig.capabilities);
    this.tools = new Map();
    this.handlers = new Map();
    this.setupHandlers();
  }

  private setupHandlers(): void {
    // Register all tools
    this.registerTool(tools.listIssuesTool, tools.createListIssuesHandler(this.linearClient));
    this.registerTool(tools.getIssueTool, tools.createGetIssueHandler(this.linearClient));
    this.registerTool(tools.createIssueTool, tools.createCreateIssueHandler(this.linearClient));
    this.registerTool(tools.updateIssueTool, tools.createUpdateIssueHandler(this.linearClient));
    this.registerTool(tools.addCommentTool, tools.createAddCommentHandler(this.linearClient));
    this.registerTool(tools.searchIssuesTool, tools.createSearchIssuesHandler(this.linearClient));
    this.registerTool(tools.assignIssueTool, tools.createAssignIssueHandler(this.linearClient));
    this.registerTool(tools.updateStatusTool, tools.createUpdateStatusHandler(this.linearClient));
    this.registerTool(tools.listProjectsTool, tools.createListProjectsHandler(this.linearClient));
    this.registerTool(tools.getProjectTool, tools.createGetProjectHandler(this.linearClient));
    this.registerTool(tools.createProjectTool, tools.createCreateProjectHandler(this.linearClient));
    this.registerTool(tools.listTeamsTool, tools.createListTeamsHandler(this.linearClient));

    // Handle list tools request
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: Array.from(this.tools.values())
    }));

    // Handle tool execution
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const handler = this.handlers.get(toolName);

      if (!handler) {
        throw new Error(`Unknown tool: ${toolName}`);
      }

      logger.info(`Executing tool: ${toolName}`);
      return await handler(request.params.arguments || {});
    });

    logger.info(`Registered ${this.tools.size} tools`);
  }

  private registerTool(tool: MCPTool, handler: ToolHandler): void {
    this.tools.set(tool.name, tool);
    this.handlers.set(tool.name, handler);
  }

  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    logger.info('MCP Server started and connected via stdio');
  }
}
