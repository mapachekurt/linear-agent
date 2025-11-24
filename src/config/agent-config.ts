import { AgentConfig } from '../types/agent.js';

export const agentConfig: AgentConfig = {
  name: 'Linear Agent',
  version: '1.0.0',
  description: 'MCP agent for managing Linear issues and projects',
  capabilities: [
    'issue_management',
    'project_management',
    'team_management',
    'search',
    'comments'
  ]
};

export const LINEAR_PRIORITY_MAP: Record<number, string> = {
  0: 'No priority',
  1: 'Urgent',
  2: 'High',
  3: 'Medium',
  4: 'Low'
};

export const STATE_TYPES = ['backlog', 'unstarted', 'started', 'completed', 'canceled'] as const;
