import { MCPResponse } from '../types/mcp.js';
import { logger } from './logger.js';

export class ErrorHandler {
  static handle(error: any, context: string): MCPResponse {
    logger.error(`Error in ${context}:`, error);

    let errorMessage = 'An unexpected error occurred';

    if (error instanceof Error) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    } else if (error?.message) {
      errorMessage = error.message;
    }

    return {
      content: [{
        type: 'text',
        text: `Error: ${errorMessage}`
      }],
      isError: true
    };
  }

  static handleValidationErrors(errors: Array<{ field: string; message: string }>): MCPResponse {
    const errorMessages = errors.map(e => `- ${e.field}: ${e.message}`).join('\n');
    return {
      content: [{
        type: 'text',
        text: `Validation errors:\n${errorMessages}`
      }],
      isError: true
    };
  }

  static success(message: string, data?: any): MCPResponse {
    const text = data ? `${message}\n\n${JSON.stringify(data, null, 2)}` : message;
    return {
      content: [{
        type: 'text',
        text
      }]
    };
  }
}
