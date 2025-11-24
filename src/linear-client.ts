import { LinearClient as LinearSDK, Issue, Project, Team, User } from '@linear/sdk';
import { LinearIssue, LinearProject, LinearTeam, IssueFilter, IssueCreateInput, IssueUpdateInput } from './types/linear.js';
import { logger } from './utils/logger.js';

export class LinearClient {
  private client: LinearSDK;
  private teamId: string;

  constructor(apiKey: string, teamId: string) {
    this.client = new LinearSDK({ apiKey });
    this.teamId = teamId;
    logger.info('Linear client initialized');
  }

  async listIssues(filter?: IssueFilter, limit: number = 50): Promise<LinearIssue[]> {
    try {
      const filterObj: any = { team: { id: { eq: this.teamId } } };

      if (filter?.assigneeId) {
        filterObj.assignee = { id: { eq: filter.assigneeId } };
      }
      if (filter?.priority !== undefined) {
        filterObj.priority = { eq: filter.priority };
      }
      if (filter?.stateType) {
        filterObj.state = { type: { eq: filter.stateType } };
      }
      if (filter?.projectId) {
        filterObj.project = { id: { eq: filter.projectId } };
      }

      const issues = await this.client.issues({
        filter: filterObj,
        first: limit,
        orderBy: 'updatedAt'
      });

      const result: LinearIssue[] = [];
      for (const issue of issues.nodes) {
        result.push(await this.formatIssue(issue));
      }

      logger.info(`Listed ${result.length} issues`);
      return result;
    } catch (error) {
      logger.error('Error listing issues:', error);
      throw error;
    }
  }

  async getIssue(issueId: string): Promise<LinearIssue> {
    try {
      const issue = await this.client.issue(issueId);
      return await this.formatIssue(issue);
    } catch (error) {
      logger.error(`Error getting issue ${issueId}:`, error);
      throw error;
    }
  }

  async createIssue(input: IssueCreateInput): Promise<LinearIssue> {
    try {
      const payload = await this.client.createIssue({
        teamId: this.teamId,
        title: input.title,
        description: input.description,
        priority: input.priority,
        assigneeId: input.assigneeId,
        projectId: input.projectId,
        labelIds: input.labelIds,
        stateId: input.stateId
      });

      const createdIssue = await payload.issue;
      if (!createdIssue) {
        throw new Error('Failed to create issue');
      }

      logger.info(`Created issue: ${createdIssue.identifier}`);
      return await this.formatIssue(createdIssue);
    } catch (error) {
      logger.error('Error creating issue:', error);
      throw error;
    }
  }

  async updateIssue(issueId: string, input: IssueUpdateInput): Promise<LinearIssue> {
    try {
      const payload = await this.client.updateIssue(issueId, input);
      const updatedIssue = await payload.issue;

      if (!updatedIssue) {
        throw new Error('Failed to update issue');
      }

      logger.info(`Updated issue: ${updatedIssue.identifier}`);
      return await this.formatIssue(updatedIssue);
    } catch (error) {
      logger.error(`Error updating issue ${issueId}:`, error);
      throw error;
    }
  }

  async addComment(issueId: string, body: string): Promise<{ id: string; body: string }> {
    try {
      const payload = await this.client.createComment({
        issueId,
        body
      });

      const comment = await payload.comment;
      if (!comment) {
        throw new Error('Failed to create comment');
      }

      logger.info(`Added comment to issue ${issueId}`);
      return {
        id: comment.id,
        body: comment.body
      };
    } catch (error) {
      logger.error(`Error adding comment to issue ${issueId}:`, error);
      throw error;
    }
  }

  async searchIssues(query: string, limit: number = 20): Promise<LinearIssue[]> {
    try {
      const issues = await this.client.issueSearch(query, {
        first: limit,
        filter: { team: { id: { eq: this.teamId } } }
      });

      const result: LinearIssue[] = [];
      for (const issue of issues.nodes) {
        result.push(await this.formatIssue(issue));
      }

      logger.info(`Found ${result.length} issues matching "${query}"`);
      return result;
    } catch (error) {
      logger.error('Error searching issues:', error);
      throw error;
    }
  }

  async listProjects(limit: number = 50): Promise<LinearProject[]> {
    try {
      const projects = await this.client.projects({
        filter: { team: { id: { eq: this.teamId } } },
        first: limit
      });

      const result: LinearProject[] = [];
      for (const project of projects.nodes) {
        result.push(await this.formatProject(project));
      }

      logger.info(`Listed ${result.length} projects`);
      return result;
    } catch (error) {
      logger.error('Error listing projects:', error);
      throw error;
    }
  }

  async getProject(projectId: string): Promise<LinearProject> {
    try {
      const project = await this.client.project(projectId);
      return await this.formatProject(project);
    } catch (error) {
      logger.error(`Error getting project ${projectId}:`, error);
      throw error;
    }
  }

  async createProject(name: string, description?: string): Promise<LinearProject> {
    try {
      const payload = await this.client.createProject({
        teamIds: [this.teamId],
        name,
        description
      });

      const project = await payload.project;
      if (!project) {
        throw new Error('Failed to create project');
      }

      logger.info(`Created project: ${project.name}`);
      return await this.formatProject(project);
    } catch (error) {
      logger.error('Error creating project:', error);
      throw error;
    }
  }

  async listTeams(): Promise<LinearTeam[]> {
    try {
      const teams = await this.client.teams();
      const result: LinearTeam[] = [];

      for (const team of teams.nodes) {
        result.push({
          id: team.id,
          name: team.name,
          key: team.key,
          description: team.description || undefined
        });
      }

      logger.info(`Listed ${result.length} teams`);
      return result;
    } catch (error) {
      logger.error('Error listing teams:', error);
      throw error;
    }
  }

  private async formatIssue(issue: Issue): Promise<LinearIssue> {
    const [state, assignee, project, team, labels] = await Promise.all([
      issue.state,
      issue.assignee,
      issue.project,
      issue.team,
      issue.labels()
    ]);

    const creator = await issue.creator;

    return {
      id: issue.id,
      identifier: issue.identifier,
      title: issue.title,
      description: issue.description || undefined,
      priority: issue.priority,
      priorityLabel: issue.priorityLabel,
      state: state ? {
        id: state.id,
        name: state.name,
        type: state.type
      } : { id: '', name: 'Unknown', type: 'unknown' },
      assignee: assignee ? {
        id: assignee.id,
        name: assignee.name,
        email: assignee.email
      } : undefined,
      creator: {
        id: creator?.id || '',
        name: creator?.name || 'Unknown'
      },
      project: project ? {
        id: project.id,
        name: project.name
      } : undefined,
      team: {
        id: team.id,
        name: team.name,
        key: team.key
      },
      labels: labels.nodes.map(label => ({
        id: label.id,
        name: label.name,
        color: label.color
      })),
      createdAt: issue.createdAt.toISOString(),
      updatedAt: issue.updatedAt.toISOString(),
      url: issue.url
    };
  }

  private async formatProject(project: Project): Promise<LinearProject> {
    const [team, lead] = await Promise.all([
      project.team,
      project.lead
    ]);

    return {
      id: project.id,
      name: project.name,
      description: project.description || undefined,
      state: project.state,
      progress: project.progress,
      startDate: project.startDate?.toISOString(),
      targetDate: project.targetDate?.toISOString(),
      team: {
        id: team.id,
        name: team.name
      },
      lead: lead ? {
        id: lead.id,
        name: lead.name
      } : undefined,
      url: project.url
    };
  }
}
