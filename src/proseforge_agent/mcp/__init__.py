"""Model Context Protocol client integration."""

from .client import (
    MCPCapabilityReport,
    MCPClient,
    MCPPrompt,
    MCPResource,
    MCPServerSpec,
    MCPTool,
    MCPTransport,
    PlaceholderMCPTransport,
    StaticMCPTransport,
    StdioMCPTransport,
    default_demo_client,
)

__all__ = [
    "MCPCapabilityReport",
    "MCPClient",
    "MCPPrompt",
    "MCPResource",
    "MCPServerSpec",
    "MCPTool",
    "MCPTransport",
    "PlaceholderMCPTransport",
    "StaticMCPTransport",
    "StdioMCPTransport",
    "default_demo_client",
]
