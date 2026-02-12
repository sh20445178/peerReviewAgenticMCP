"""
Simple command-line interface for the Peer Review MCP Server.
"""

import asyncio
import sys
import typer
from rich.console import Console

app = typer.Typer(
    name="peer-review-mcp",
    help="Peer Review Agentic MCP Server",
    no_args_is_help=True
)
console = Console()


@app.command()
def start():
    """Start the Peer Review MCP Server."""
    console.print("🚀 Starting Peer Review MCP Server", style="bold green")
    
    try:
        from .server_simple import main
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def config_check():
    """Check configuration status."""
    from .config import config
    
    console.print("📋 Configuration Check", style="bold blue")
    console.print()
    
    # GitHub
    if config.github.access_token:
        console.print("✅ GitHub: Configured", style="green")
    else:
        console.print("❌ GitHub: Not configured", style="red")
    
    # SonarQube
    if config.sonarqube.url:
        console.print("✅ SonarQube: Configured", style="green")
    else:
        console.print("⚠️  SonarQube: Not configured (optional)", style="yellow")
    
    # Jira
    if config.jira.url:
        console.print("✅ Jira: Configured", style="green")
    else:
        console.print("⚠️  Jira: Not configured (optional)", style="yellow")
    
    console.print()
    console.print(f"Database: {config.database.url}", style="dim")


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"Peer Review MCP Server v{__version__}", style="bold")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
