import { MCPTool, MCPResponse, ToolHandler } from '../types/mcp.js';
import { LinearClient } from '../linear-client.js';
import { ErrorHandler } from '../utils/error-handler.js';
import { Validator } from '../utils/validator.js';

export const searchIssuesTool: MCPTool = {
  name: 'search_issues',
  description: 'Search Linear issues by text query',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query text'
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results (default: 20)'
      }
    },
    required: ['query']
  }
};

export const createSearchIssuesHandler = (client: LinearClient): ToolHandler => {
  return async (args: Record<string, any>): Promise<MCPResponse> => {
    try {
      const errors = Validator.collectErrors([
        Validator.validateRequired(args.query, 'query'),
        Validator.validateString(args.query, 'query', 1)
      ]);

      if (errors.length > 0) {
        return ErrorHandler.handleValidationErrors(errors);
      }

      const issues = await client.searchIssues(args.query, args.limit);

      if (issues.length === 0) {
        return ErrorHandler.success(`No issues found matching "${args.query}"`);
      }

      const issueList = issues.map(issue => {
        return `- ${issue.identifier}: ${issue.title}\n  Status: ${issue.state.name} | Priority: ${issue.priorityLabel}\n  ${issue.url}`;
      }).join('\n\n');

      return ErrorHandler.success(
        `Found ${issues.length} issue(s) matching "${args.query}":\n\n${issueList}`
      );
    } catch (error) {
      return ErrorHandler.handle(error, 'search_issues');
    }
  };
};
