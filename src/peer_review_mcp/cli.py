"""
Command-line interface for the Peer Review MCP Server.
"""

import asyncio
import logging
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .server import PeerReviewMCPServer
from .config import config

app = typer.Typer(
    name="peer-review-mcp",
    help="Peer Review Agentic MCP Server - Automate peer review governance and validation",
    no_args_is_help=True
)
console = Console()


def setup_logging(debug: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@app.command()
def start(
    host: str = typer.Option(
        config.mcp_server.host,
        "--host",
        "-h",
        help="Host address to bind to"
    ),
    port: int = typer.Option(
        config.mcp_server.port,
        "--port",
        "-p",
        help="Port number to bind to"
    ),
    debug: bool = typer.Option(
        config.mcp_server.debug,
        "--debug",
        "-d",
        help="Enable debug mode"
    ),
    log_level: str = typer.Option(
        config.mcp_server.log_level,
        "--log-level",
        "-l",
        help="Logging level"
    )
):
    """Start the Peer Review MCP Server."""
    setup_logging(debug)
    
    console.print(f"🚀 Starting Peer Review MCP Server", style="bold green")
    console.print(f"   Host: {host}")
    console.print(f"   Port: {port}")
    console.print(f"   Debug: {debug}")
    console.print(f"   Log Level: {log_level}")
    console.print()
    
    try:
        server = PeerReviewMCPServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Error starting server: {e}", style="red")
        sys.exit(1)


@app.command()
def config_check():
    """Check configuration and integration status."""
    console.print("📋 Configuration Check", style="bold blue")
    console.print()
    
    # Create configuration table
    table = Table(title="Configuration Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")
    
    # Check GitHub configuration
    if config.github.access_token:
        table.add_row("GitHub", "✅ Configured", f"Base URL: {config.github.base_url}")
    else:
        table.add_row("GitHub", "❌ Not Configured", "Missing access token")
    
    # Check SonarQube configuration
    if config.sonarqube.url and (config.sonarqube.token or config.sonarqube.username):
        table.add_row("SonarQube", "✅ Configured", f"URL: {config.sonarqube.url}")
    else:
        table.add_row("SonarQube", "⚠️ Optional", "Not configured")
    
    # Check Jira configuration
    if config.jira.url and config.jira.username and config.jira.api_token:
        table.add_row("Jira", "✅ Configured", f"URL: {config.jira.url}")
    else:
        table.add_row("Jira", "⚠️ Optional", "Not configured")
    
    # Check Database configuration
    table.add_row("Database", "✅ Configured", f"URL: {config.database.url}")
    
    console.print(table)
    console.print()
    
    # Show peer review configuration
    console.print("⚙️ Peer Review Settings", style="bold yellow")
    console.print(f"   Min Reviewers: {config.peer_review.min_reviewers}")
    console.print(f"   Required Labels: {config.peer_review.required_labels}")
    console.print(f"   Blocked Labels: {config.peer_review.blocked_labels}")
    console.print(f"   Review Timeout: {config.peer_review.review_timeout_hours} hours")


@app.command()
def test_integrations():
    """Test integration connectivity."""
    console.print("🔌 Testing Integrations", style="bold blue")
    console.print()
    
    async def run_tests():
        from .integrations.github import GitHubIntegration
        from .integrations.sonarqube import SonarQubeIntegration
        from .integrations.jira import JiraIntegration
        
        # Test GitHub
        console.print("Testing GitHub integration...")
        if config.github.access_token:
            try:
                github = GitHubIntegration(config.github)
                if github.github:
                    user = github.github.get_user()
                    console.print(f"✅ GitHub: Connected as {user.login}", style="green")
                else:
                    console.print("❌ GitHub: Failed to initialize", style="red")
            except Exception as e:
                console.print(f"❌ GitHub: Error - {e}", style="red")
        else:
            console.print("⚠️ GitHub: Not configured", style="yellow")
        
        # Test SonarQube
        console.print("Testing SonarQube integration...")
        if config.sonarqube.url:
            try:
                sonarqube = SonarQubeIntegration(config.sonarqube)
                # Simple test - try to make a request
                projects = await sonarqube._make_request('GET', 'projects/search')
                if projects:
                    console.print("✅ SonarQube: Connected successfully", style="green")
                else:
                    console.print("❌ SonarQube: Failed to connect", style="red")
            except Exception as e:
                console.print(f"❌ SonarQube: Error - {e}", style="red")
        else:
            console.print("⚠️ SonarQube: Not configured", style="yellow")
        
        # Test Jira
        console.print("Testing Jira integration...")
        if config.jira.url and config.jira.username and config.jira.api_token:
            try:
                jira = JiraIntegration(config.jira)
                if jira.is_enabled():
                    projects = await jira.get_projects()
                    console.print(f"✅ Jira: Connected, found {len(projects)} projects", style="green")
                else:
                    console.print("❌ Jira: Failed to connect", style="red")
            except Exception as e:
                console.print(f"❌ Jira: Error - {e}", style="red")
        else:
            console.print("⚠️ Jira: Not configured", style="yellow")
    
    try:
        asyncio.run(run_tests())
    except Exception as e:
        console.print(f"❌ Error during testing: {e}", style="red")


@app.command()
def init_db():
    """Initialize the database."""
    console.print("🗄️ Initializing Database", style="bold blue")
    
    async def run_init():
        from .services.database import DatabaseManager
        
        try:
            db_manager = DatabaseManager()
            await db_manager.initialize()
            console.print("✅ Database initialized successfully", style="green")
        except Exception as e:
            console.print(f"❌ Error initializing database: {e}", style="red")
            sys.exit(1)
    
    asyncio.run(run_init())


@app.command()
def version():
    """Show version information."""
    from . import __version__
    
    console.print(f"Peer Review Agentic MCP Server v{__version__}", style="bold")


@app.command()
def analyze(
    repository: str = typer.Argument(..., help="Repository name (owner/repo)"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)")
):
    """Analyze a specific pull request."""
    console.print(f"🔍 Analyzing PR #{pr_number} in {repository}", style="bold blue")
    
    async def run_analysis():
        try:
            from .services.database import DatabaseManager
            from .services.peer_review import PeerReviewEngine
            
            db_manager = DatabaseManager()
            await db_manager.initialize()
            
            engine = PeerReviewEngine(db_manager)
            
            # This would need actual PR ID from database
            # For demo purposes, show what the analysis would look like
            console.print("Mock analysis results:", style="yellow")
            console.print(f"  Repository: {repository}")
            console.print(f"  PR Number: {pr_number}")
            console.print(f"  Compliance Score: 85%")
            console.print(f"  Status: Needs Review")
            console.print(f"  Recommendations: 3")
            
        except Exception as e:
            console.print(f"❌ Error during analysis: {e}", style="red")
    
    asyncio.run(run_analysis())


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()