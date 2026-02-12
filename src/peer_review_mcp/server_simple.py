"""
Simplified MCP Server implementation for Peer Review Automation.
"""

import asyncio
import logging

from mcp.server import Server
import mcp.types as types

from .config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.mcp_server.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create a simple MCP server
server = Server("peer-review-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MCP tools."""
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
                    "repository": {"type": "string"},
                    "pr_number": {"type": "integer"}
                },
                "required": ["repository", "pr_number"]
            }
        ),
        types.Tool(
            name="config_check",
            description="Check configuration status",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with args: {arguments}")
    
    if name == "analyze_pull_request":
        repo = arguments.get("repository")
        pr_num = arguments.get("pr_number")
        result = {
            "status": "success",
            "repository": repo,
            "pr_number": pr_num,
            "compliance_score": 85.0,
            "message": "Mock analysis result - integrate with actual review engine"
        }
        return [types.TextContent(
            type="text",
            text=f"Analysis Result:\n{result}"
        )]
    
    elif name == "get_review_summary":
        repo = arguments.get("repository")
        pr_num = arguments.get("pr_number")
        return [types.TextContent(
            type="text",
            text=f"Review summary for {repo} PR#{pr_num}"
        )]
    
    elif name == "config_check":
        status = {
            "github": "configured" if config.github.access_token else "not configured",
            "sonarqube": "configured" if config.sonarqube.url else "not configured",
            "jira": "configured" if config.jira.url else "not configured"
        }
        return [types.TextContent(
            type="text",
            text=f"Configuration Status:\n{status}"
        )]
    
    return [types.TextContent(
        type="text",
        text=f"Unknown tool: {name}"
    )]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Peer Review MCP Server (Simple Version)")
    
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(
            read_stream,
            write_stream,
            init_options
        )


if __name__ == "__main__":
    asyncio.run(main())
