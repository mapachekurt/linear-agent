# Operational Playbook

This document provides operational guidance for the Autonomous Linear Agent, including deployment, monitoring, and troubleshooting.

## Deployment

The agent is designed to be deployed as a long-running service. It can be run in a variety of environments, including:

-   **Virtual Machines**: The agent can be run on a VM, either manually or as a systemd service.
-   **Containers**: The agent can be containerized using Docker and deployed to a container orchestration platform like Kubernetes.

### Recommended Deployment Strategy

1.  **Containerize the application**: Use the provided `Dockerfile` to build a Docker image of the agent.
2.  **Deploy to Kubernetes**: Deploy the agent to a Kubernetes cluster for scalability and high availability.
3.  **Configure webhooks**: Configure Linear and GitHub to send webhooks to the deployed agent's public URL.

## Monitoring

The agent includes a `/health` endpoint that can be used for basic health checks. For more advanced monitoring, consider the following:

-   **Log Monitoring**: The agent logs all actions to a JSONL file (`agent_actions.jsonl`). This file should be monitored for errors and unexpected behavior.
-   **Metrics**: The agent can be extended to expose Prometheus metrics for monitoring API usage, error rates, and other key performance indicators.
-   **Alerting**: Configure alerts to be sent to your team's communication channels (e.g., Slack, PagerDuty) when errors are detected.

## Troubleshooting

### Common Issues

-   **`ValueError: GitHub App ID and Private Key must be set.`**: This error indicates that the `GITHUB_APP_ID` or `GITHUB_PRIVATE_KEY` environment variables are not set correctly. Ensure that the `.env` file is present and contains the correct values.
-   **`ValueError: LINEAR_API_KEY must be set.`**: This error indicates that the `LINEAR_API_KEY` environment variable is not set. Ensure that the `.env` file is present and contains the correct Linear API key.
-   **`422 Unprocessable Entity` errors**: These errors typically indicate a mismatch between the webhook payload and the Pydantic models. Check the logs for more details on the validation error.

### Debugging

-   **Enable debug logging**: The agent's logging level can be configured to provide more detailed output for debugging purposes.
-   **Inspect the agent_actions.jsonl file**: This file contains a detailed record of all agent actions, which can be invaluable for debugging.
-   **Review the feedback tickets**: The agent automatically creates feedback tickets in Linear when it encounters errors. These tickets can provide valuable context for debugging.

## Maintenance

### Updating the Agent

To update the agent to the latest version:

1.  Pull the latest changes from the repository.
2.  Rebuild the Docker image.
3.  Redeploy the agent.

### Rotating Credentials

It is recommended to rotate the agent's API keys and other credentials on a regular basis. To do this:

1.  Generate a new Linear API key and GitHub App private key.
2.  Update the environment variables in your deployment environment.
3.  Restart the agent.
