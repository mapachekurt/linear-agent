"""
Command-line interface for Linear Agent.

This module provides a simple CLI for testing and running
the Linear Agent.
"""

import argparse
import asyncio
import logging
import sys

from linear_agent.config import AgentConfig
from linear_agent.orchestrator import Orchestrator


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with JSON-like format."""
    log_fmt = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(name)s", "message": "%(message)s"}'
    )
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_fmt,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


async def run_health_check(orchestrator: Orchestrator) -> int:
    """Run a health check and print results."""
    report = await orchestrator.check_health()
    print(report.summary())
    return 0 if report.is_healthy() else 1


async def run_list_teams(orchestrator: Orchestrator) -> int:
    """List all teams."""
    teams = await orchestrator.list_teams()
    print(f"Found {len(teams)} teams:")
    for team in teams:
        print(f"  - {team.name} ({team.key}): {team.id}")
    return 0


async def run_list_issues(orchestrator: Orchestrator, team_id: str | None) -> int:
    """List issues."""
    issues = await orchestrator.list_issues(team_id=team_id)
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - [{issue.identifier}] {issue.title}")
    return 0


async def run_learning_summary(orchestrator: Orchestrator) -> int:
    """Print learning summary."""
    summary = await orchestrator.get_improvement_summary()
    print(summary)
    return 0


async def main_async(args: argparse.Namespace) -> int:
    """Async main function."""
    config = AgentConfig.from_env()

    async with Orchestrator(config) as orchestrator:
        if args.command == "health":
            return await run_health_check(orchestrator)
        elif args.command == "teams":
            return await run_list_teams(orchestrator)
        elif args.command == "issues":
            return await run_list_issues(orchestrator, args.team)
        elif args.command == "learn":
            return await run_learning_summary(orchestrator)
        else:
            print(f"Unknown command: {args.command}")
            return 1


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Linear Agent CLI")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Health check command
    subparsers.add_parser("health", help="Run health check")

    # List teams command
    subparsers.add_parser("teams", help="List all teams")

    # List issues command
    issues_parser = subparsers.add_parser("issues", help="List issues")
    issues_parser.add_argument("--team", help="Filter by team ID")

    # Learning summary command
    subparsers.add_parser("learn", help="Show learning summary")

    args = parser.parse_args()
    setup_logging(args.log_level)

    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
