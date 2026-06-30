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
from .approval import MCPApprovalGate, MCPApprovalQueue, MCPApprovalRequest
from .registry import MCPServerConfig, MCPServerRegistry
from .policy import MCPPolicy, MCPPolicyDecision, MCPPolicyStore
from .schema import MCPSchemaCache, MCPSchemaValidationResult, MCPSchemaValidator, MCPSchemaVersion

__all__ = [
    "MCPCapabilityReport",
    "MCPApprovalGate",
    "MCPApprovalQueue",
    "MCPApprovalRequest",
    "MCPClient",
    "MCPPrompt",
    "MCPResource",
    "MCPSchemaCache",
    "MCPSchemaValidationResult",
    "MCPSchemaValidator",
    "MCPSchemaVersion",
    "MCPServerSpec",
    "MCPServerConfig",
    "MCPServerRegistry",
    "MCPPolicy",
    "MCPPolicyDecision",
    "MCPPolicyStore",
    "MCPTool",
    "MCPTransport",
    "PlaceholderMCPTransport",
    "StaticMCPTransport",
    "StdioMCPTransport",
    "default_demo_client",
]
