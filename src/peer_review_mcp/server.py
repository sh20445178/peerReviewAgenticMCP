"""
Main MCP Server implementation for Peer Review Automation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import json

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

from .config import config
from .models import (
    ReviewSummary, ReviewMetrics, PullRequestResponse, 
    ReviewResponse, GovernanceValidationResponse
)
from .services.database import DatabaseManager
from .services.peer_review import PeerReviewEngine
from .integrations.github import GitHubIntegration
from .integrations.sonarqube import SonarQubeIntegration
from .integrations.jira import JiraIntegration


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.mcp_server.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PeerReviewMCPServer:
    """Main MCP Server for Peer Review Automation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("peer-review-mcp")
        self.db_manager = DatabaseManager()
        self.peer_review_engine = PeerReviewEngine(self.db_manager)
        
        # Initialize integrations
        self.github = GitHubIntegration(config.github) if config.github.access_token else None
        self.sonarqube = SonarQubeIntegration(config.sonarqube) if config.sonarqube.url else None
        self.jira = JiraIntegration(config.jira) if config.jira.url else None
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Peer Review MCP Server initialized")
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="analyze_pull_request",
                    description="Analyze a pull request for compliance and review criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number"
                            }
                        },
                        "required": ["repository", "pr_number"]
                    }
                ),
                types.Tool(
                    name="get_review_summary",
                    description="Get summary of a pull request review status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number"
                            }
                        },
                        "required": ["repository", "pr_number"]
                    }
                ),
                Tool(
                    name="validate_governance",
                    description="Validate pull request against governance policies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number"
                            }
                        },
                        "required": ["repository", "pr_number"]
                    }
                ),
                Tool(
                    name="get_review_metrics",
                    description="Get review performance metrics for a repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["repository"]
                    }
                ),
                Tool(
                    name="trigger_automated_checks",
                    description="Trigger automated checks for a pull request",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number"
                            },
                            "check_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of checks to run (build, test, code_quality, security)",
                                "default": ["build", "test", "code_quality"]
                            }
                        },
                        "required": ["repository", "pr_number"]
                    }
                ),
                Tool(
                    name="create_jira_issue",
                    description="Create a Jira issue for review findings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "pr_number": {
                                "type": "integer", 
                                "description": "Pull request number"
                            },
                            "issue_type": {
                                "type": "string",
                                "description": "Jira issue type (Bug, Task, etc.)",
                                "default": "Task"
                            },
                            "priority": {
                                "type": "string",
                                "description": "Issue priority (Low, Medium, High, Critical)",
                                "default": "Medium"
                            }
                        },
                        "required": ["repository", "pr_number"]
                    }
                ),
                Tool(
                    name="update_review_criteria",
                    description="Update review criteria for a repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository full name (owner/repo)"
                            },
                            "criteria_name": {
                                "type": "string",
                                "description": "Name of the criteria to update"
                            },
                            "criteria_rules": {
                                "type": "object",
                                "description": "New rules for the criteria"
                            }
                        },
                        "required": ["repository", "criteria_name", "criteria_rules"]
                    }
                )
            ]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            try:
                if name == "analyze_pull_request":
                    return await self._analyze_pull_request(arguments)
                elif name == "get_review_summary":
                    return await self._get_review_summary(arguments)
                elif name == "validate_governance":
                    return await self._validate_governance(arguments)
                elif name == "get_review_metrics":
                    return await self._get_review_metrics(arguments)
                elif name == "trigger_automated_checks":
                    return await self._trigger_automated_checks(arguments)
                elif name == "create_jira_issue":
                    return await self._create_jira_issue(arguments)
                elif name == "update_review_criteria":
                    return await self._update_review_criteria(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.app.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="peer-review://repositories",
                    name="Repositories",
                    description="List of tracked repositories",
                    mimeType="application/json"
                ),
                Resource(
                    uri="peer-review://pull-requests",
                    name="Pull Requests", 
                    description="Active pull requests",
                    mimeType="application/json"
                ),
                Resource(
                    uri="peer-review://review-criteria",
                    name="Review Criteria",
                    description="Governance and review criteria",
                    mimeType="application/json"
                ),
                Resource(
                    uri="peer-review://metrics",
                    name="Review Metrics",
                    description="Review performance metrics",
                    mimeType="application/json"
                )
            ]
        
        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content."""
            if uri == "peer-review://repositories":
                repositories = await self.db_manager.get_all_repositories()
                return str([repo.model_dump() for repo in repositories])
            elif uri == "peer-review://pull-requests":
                pull_requests = await self.db_manager.get_active_pull_requests()
                return str([pr.model_dump() for pr in pull_requests])
            elif uri == "peer-review://review-criteria":
                criteria = await self.db_manager.get_all_review_criteria()
                return str([criterion.model_dump() for criterion in criteria])
            elif uri == "peer-review://metrics":
                metrics = await self.peer_review_engine.get_global_metrics()
                return str(metrics.model_dump())
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    # Tool implementation methods
    
    async def _analyze_pull_request(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze a pull request for compliance."""
        repository = arguments["repository"]
        pr_number = arguments["pr_number"]
        
        logger.info(f"Analyzing PR {pr_number} in {repository}")
        
        # Get or create PR in database
        pr = await self._get_or_sync_pull_request(repository, pr_number)
        
        # Run analysis
        analysis = await self.peer_review_engine.analyze_pull_request(pr.id)
        
        # Format response
        response = {
            "status": "analyzed",
            "repository": repository,
            "pr_number": pr_number,
            "analysis": analysis,
            "compliance_score": analysis.get("compliance_score", 0),
            "recommendations": analysis.get("recommendations", [])
        }
        
        return [TextContent(type="text", text=str(response))]
    
    async def _get_review_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get review summary for a pull request."""
        repository = arguments["repository"]
        pr_number = arguments["pr_number"]
        
        logger.info(f"Getting review summary for PR {pr_number} in {repository}")
        
        summary = await self.peer_review_engine.get_review_summary(repository, pr_number)
        
        return [TextContent(type="text", text=str(summary.model_dump()))]
    
    async def _validate_governance(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Validate governance policies."""
        repository = arguments["repository"]
        pr_number = arguments["pr_number"]
        
        logger.info(f"Validating governance for PR {pr_number} in {repository}")
        
        validation = await self.peer_review_engine.validate_governance(repository, pr_number)
        
        return [TextContent(type="text", text=str(validation.model_dump()))]
    
    async def _get_review_metrics(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get review metrics."""
        repository = arguments["repository"]
        days = arguments.get("days", 30)
        
        logger.info(f"Getting review metrics for {repository} (last {days} days)")
        
        metrics = await self.peer_review_engine.get_repository_metrics(repository, days)
        
        return [TextContent(type="text", text=str(metrics.model_dump()))]
    
    async def _trigger_automated_checks(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Trigger automated checks."""
        repository = arguments["repository"]
        pr_number = arguments["pr_number"]
        check_types = arguments.get("check_types", ["build", "test", "code_quality"])
        
        logger.info(f"Triggering checks {check_types} for PR {pr_number} in {repository}")
        
        results = []
        
        # Trigger SonarQube check if available
        if "code_quality" in check_types and self.sonarqube:
            sonar_result = await self.sonarqube.analyze_pull_request(repository, pr_number)
            results.append(sonar_result)
        
        # Trigger other checks via GitHub Actions or similar
        if self.github:
            github_results = await self.github.trigger_checks(repository, pr_number, check_types)
            results.extend(github_results)
        
        return [TextContent(type="text", text=str(results))]
    
    async def _create_jira_issue(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create Jira issue for review findings."""
        repository = arguments["repository"]
        pr_number = arguments["pr_number"]
        issue_type = arguments.get("issue_type", "Task")
        priority = arguments.get("priority", "Medium")
        
        if not self.jira:
            return [TextContent(type="text", text="Jira integration not configured")]
        
        logger.info(f"Creating Jira issue for PR {pr_number} in {repository}")
        
        # Get PR summary for issue content
        summary = await self.peer_review_engine.get_review_summary(repository, pr_number)
        
        issue = await self.jira.create_issue_for_review(
            repository, pr_number, summary, issue_type, priority
        )
        
        return [TextContent(type="text", text=str(issue))]
    
    async def _update_review_criteria(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update review criteria."""
        repository = arguments["repository"]
        criteria_name = arguments["criteria_name"]
        criteria_rules = arguments["criteria_rules"]
        
        logger.info(f"Updating review criteria '{criteria_name}' for {repository}")
        
        updated = await self.peer_review_engine.update_review_criteria(
            repository, criteria_name, criteria_rules
        )
        
        return [TextContent(type="text", text=str(updated.model_dump()))]
    
    async def _get_or_sync_pull_request(self, repository: str, pr_number: int) -> PullRequestResponse:
        """Get or synchronize pull request from GitHub."""
        # First try to get from database
        pr = await self.db_manager.get_pull_request_by_repo_and_number(repository, pr_number)
        
        if not pr and self.github:
            # If not in database and GitHub is available, sync it
            github_pr = await self.github.get_pull_request(repository, pr_number)
            if github_pr:
                # Create repository if it doesn't exist
                repo = await self.db_manager.get_or_create_repository_from_github(repository)
                
                # Create pull request
                pr_data = {
                    "repository_id": repo.id,
                    "pr_number": pr_number,
                    "title": github_pr["title"],
                    "description": github_pr.get("body"),
                    "author": github_pr["user"]["login"],
                    "source_branch": github_pr["head"]["ref"],
                    "target_branch": github_pr["base"]["ref"],
                    "github_id": github_pr["id"],
                    "github_url": github_pr["html_url"],
                    "labels": [label["name"] for label in github_pr.get("labels", [])]
                }
                pr = await self.db_manager.create_pull_request(pr_data)
        
        if not pr:
            raise ValueError(f"Pull request {pr_number} not found in {repository}")
        
        return pr
    
    async def start(self):
        """Start the MCP server."""
        logger.info("Starting Peer Review MCP Server")
        
        # Initialize database
        await self.db_manager.initialize()
        
        # Start the server
        await self.app.run()
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping Peer Review MCP Server")
        
        # Close database connections
        await self.db_manager.close()


# Convenience function for running the server
async def run_server():
    """Run the MCP server."""
    server = PeerReviewMCPServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(run_server())