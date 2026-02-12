"""
Peer Review Agentic MCP Server

A Model Context Protocol (MCP) server for automating peer review governance and validation.
Integrates with Git repositories, SonarQube, and Jira to standardize review criteria
and improve turnaround times.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config

__all__ = ["Config"]