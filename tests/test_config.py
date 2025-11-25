"""Tests for the config module."""

import os
from pathlib import Path
from unittest import mock

from linear_agent.config import (
    AgentConfig,
    BackoffPolicy,
    GitHubSettings,
    LinearSettings,
    StorageSettings,
)


class TestBackoffPolicy:
    """Tests for BackoffPolicy."""

    def test_default_values(self) -> None:
        """Test default backoff values."""
        policy = BackoffPolicy()
        assert policy.initial_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.multiplier == 2.0
        assert policy.max_retries == 5

    def test_get_delay(self) -> None:
        """Test delay calculation."""
        policy = BackoffPolicy(initial_delay=1.0, multiplier=2.0, max_delay=10.0)
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
        assert policy.get_delay(3) == 8.0
        assert policy.get_delay(4) == 10.0  # Capped at max_delay
        assert policy.get_delay(5) == 10.0  # Still capped


class TestLinearSettings:
    """Tests for LinearSettings."""

    def test_default_values(self) -> None:
        """Test default Linear settings."""
        settings = LinearSettings()
        assert settings.api_key == ""
        assert settings.api_url == "https://api.linear.app/graphql"
        assert settings.timeout == 30.0

    def test_from_env(self) -> None:
        """Test loading from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "LINEAR_API_KEY": "test-key",
                "LINEAR_API_URL": "https://custom.api/graphql",
                "LINEAR_TIMEOUT": "60.0",
            },
        ):
            settings = LinearSettings.from_env()
            assert settings.api_key == "test-key"
            assert settings.api_url == "https://custom.api/graphql"
            assert settings.timeout == 60.0


class TestGitHubSettings:
    """Tests for GitHubSettings."""

    def test_default_values(self) -> None:
        """Test default GitHub settings."""
        settings = GitHubSettings()
        assert settings.api_key == ""
        assert settings.api_url == "https://api.github.com"
        assert settings.timeout == 30.0

    def test_from_env(self) -> None:
        """Test loading from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "gh-token",
                "GITHUB_API_URL": "https://custom.github.com",
                "GITHUB_TIMEOUT": "45.0",
            },
        ):
            settings = GitHubSettings.from_env()
            assert settings.api_key == "gh-token"
            assert settings.api_url == "https://custom.github.com"
            assert settings.timeout == 45.0


class TestStorageSettings:
    """Tests for StorageSettings."""

    def test_default_values(self) -> None:
        """Test default storage settings."""
        settings = StorageSettings()
        assert settings.audit_log_path == Path("audit.jsonl")
        assert settings.state_file_path == Path("agent_state.json")
        assert settings.max_audit_entries == 10000

    def test_from_env(self) -> None:
        """Test loading from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "AUDIT_LOG_PATH": "/custom/audit.jsonl",
                "STATE_FILE_PATH": "/custom/state.json",
                "MAX_AUDIT_ENTRIES": "5000",
            },
        ):
            settings = StorageSettings.from_env()
            assert settings.audit_log_path == Path("/custom/audit.jsonl")
            assert settings.state_file_path == Path("/custom/state.json")
            assert settings.max_audit_entries == 5000


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_default_values(self) -> None:
        """Test default agent configuration."""
        config = AgentConfig()
        assert isinstance(config.linear, LinearSettings)
        assert isinstance(config.github, GitHubSettings)
        assert isinstance(config.storage, StorageSettings)

    def test_from_env(self) -> None:
        """Test loading complete config from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "LINEAR_API_KEY": "linear-key",
                "GITHUB_TOKEN": "github-token",
            },
        ):
            config = AgentConfig.from_env()
            assert config.linear.api_key == "linear-key"
            assert config.github.api_key == "github-token"
