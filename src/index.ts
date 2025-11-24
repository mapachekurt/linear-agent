import dotenv from 'dotenv';
import { LinearClient } from './linear-client.js';
import { MCPServer } from './server.js';
import { logger } from './utils/logger.js';

// Load environment variables
dotenv.config();

async function main() {
  try {
    // Validate required environment variables
    const apiKey = process.env.LINEAR_API_KEY;
    const teamId = process.env.LINEAR_TEAM_ID;

    if (!apiKey) {
      throw new Error('LINEAR_API_KEY environment variable is required');
    }

    if (!teamId) {
      throw new Error('LINEAR_TEAM_ID environment variable is required');
    }

    logger.info('Starting Linear MCP Agent...');

    // Initialize Linear client
    const linearClient = new LinearClient(apiKey, teamId);

    // Create and start MCP server
    const server = new MCPServer(linearClient);
    await server.start();

    logger.info('Linear MCP Agent is ready');
  } catch (error) {
    logger.error('Failed to start Linear MCP Agent:', error);
    process.exit(1);
  }
}

main();
