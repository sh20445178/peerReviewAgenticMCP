"""
Configuration management for the Peer Review MCP Server.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite:///peer_review.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    
    class Config:
        env_prefix = "DB_"


class GitHubConfig(BaseSettings):
    """GitHub integration configuration."""
    
    access_token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token"
    )
    webhook_secret: Optional[str] = Field(
        default=None,
        description="GitHub webhook secret for validating payloads"
    )
    base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL (use for GitHub Enterprise)"
    )
    
    class Config:
        env_prefix = "GITHUB_"


class SonarQubeConfig(BaseSettings):
    """SonarQube integration configuration."""
    
    url: Optional[str] = Field(
        default=None,
        description="SonarQube server URL"
    )
    token: Optional[str] = Field(
        default=None,
        description="SonarQube authentication token"
    )
    username: Optional[str] = Field(
        default=None,
        description="SonarQube username (alternative to token)"
    )
    password: Optional[str] = Field(
        default=None,
        description="SonarQube password (alternative to token)"
    )
    
    class Config:
        env_prefix = "SONARQUBE_"


class JiraConfig(BaseSettings):
    """Jira integration configuration."""
    
    url: Optional[str] = Field(
        default=None,
        description="Jira server URL"
    )
    username: Optional[str] = Field(
        default=None,
        description="Jira username"
    )
    api_token: Optional[str] = Field(
        default=None,
        description="Jira API token"
    )
    
    class Config:
        env_prefix = "JIRA_"


class PeerReviewConfig(BaseSettings):
    """Peer review criteria and governance settings."""
    
    min_reviewers: int = Field(
        default=2,
        description="Minimum number of reviewers required"
    )
    required_labels: List[str] = Field(
        default_factory=lambda: ["code-review", "ready-for-review"],
        description="Required labels for PR review"
    )
    blocked_labels: List[str] = Field(
        default_factory=lambda: ["wip", "do-not-merge"],
        description="Labels that block PR merge"
    )
    automated_checks: List[str] = Field(
        default_factory=lambda: ["build", "tests", "code-quality"],
        description="Automated checks that must pass"
    )
    review_timeout_hours: int = Field(
        default=48,
        description="Maximum hours to wait for review"
    )
    
    class Config:
        env_prefix = "PEER_REVIEW_"


class MCPServerConfig(BaseSettings):
    """MCP server configuration."""
    
    host: str = Field(
        default="127.0.0.1",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        description="Server port number"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        env_prefix = "MCP_"


class Config(BaseSettings):
    """Main configuration class combining all settings."""
    
    app_name: str = Field(
        default="Peer Review Agentic MCP Server",
        description="Application name"
    )
    version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    sonarqube: SonarQubeConfig = Field(default_factory=SonarQubeConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    peer_review: PeerReviewConfig = Field(default_factory=PeerReviewConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_integration_config(self, integration_name: str) -> Optional[BaseSettings]:
        """Get configuration for a specific integration."""
        integration_map = {
            'github': self.github,
            'sonarqube': self.sonarqube,
            'jira': self.jira
        }
        return integration_map.get(integration_name.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
config = Config()