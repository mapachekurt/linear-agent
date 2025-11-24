// Agent configuration types
export interface AgentConfig {
  name: string;
  version: string;
  description: string;
  capabilities: string[];
}

export interface LoggerConfig {
  level: 'debug' | 'info' | 'warn' | 'error';
  timestamp: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface OperationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: ValidationError[];
}
