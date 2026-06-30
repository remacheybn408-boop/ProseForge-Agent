"""Agent runtime interfaces."""

from .events import BackgroundJobRunner, EventBus, EventRecord, JobResult
from .eval import EvalHarness, EvalReport, EvalSuite, EvalTaskResult, GoldenTask
from .attachments import AttachmentIngestResult, AttachmentIngestor
from .audit import AuditStep, AuditTrailStore, ReplayResult
from .execution_guard import ExecutionGuard, ExecutionGuardResult, ExecutionPolicy
from .function_calling import (
    ProviderToolCall,
    StructuredToolAdapter,
    StructuredToolResult,
    ToolCallLoop,
    ToolLoopResult,
)
from .kernel import AgentKernel
from .intent_router import IntentDecision, IntentRouter
from .types import AgentIntent, AgentTurnRequest, AgentTurnResult, ToolCallResult
from .control import ControlSignal, ControlToken
from .context_window import ContextUsageReport, ContextWindowManager
from .degradation import CapabilityReport, CapabilityRuntime, FeatureCheck, FeatureDeclaration, FeatureLevel
from .permissions import PERMISSION_LEVELS, PermissionDecision, PermissionPolicy
from .profiles import AgentProfile, AgentProfileRegistry
from .provider_fallback import ProviderFallbackAttempt, ProviderFallbackChain, ProviderFallbackResult
from .prompt_templates import (
    PromptTemplate,
    PromptTemplateRegistry,
    PromptTemplateValidation,
    PromptTemplateValidationError,
)
from .sandbox import Approval, ExecRequest, ExecResult, Sandbox
from .subagent import Scope, SubAgentResult, SubAgentRunner
from .structured_output import (
    StructuredOutputRepairResult,
    repair_structured_output,
    validate_or_repair,
)
from .tools import (
    AgentTool,
    ToolContext,
    ToolRegistry,
    ToolResult,
    default_tool_registry,
    general_tool_registry,
    register_writing_domain_tools,
)

__all__ = [
    "BackgroundJobRunner",
    "AttachmentIngestResult",
    "AttachmentIngestor",
    "AuditStep",
    "AuditTrailStore",
    "EvalHarness",
    "EvalReport",
    "EvalSuite",
    "EvalTaskResult",
    "GoldenTask",
    "EventBus",
    "EventRecord",
    "ExecutionGuard",
    "ExecutionGuardResult",
    "ExecutionPolicy",
    "ProviderToolCall",
    "StructuredToolAdapter",
    "StructuredToolResult",
    "ToolCallLoop",
    "ToolLoopResult",
    "AgentKernel",
    "IntentDecision",
    "IntentRouter",
    "AgentIntent",
    "AgentTurnRequest",
    "AgentTurnResult",
    "ToolCallResult",
    "ControlSignal",
    "ControlToken",
    "ContextUsageReport",
    "ContextWindowManager",
    "CapabilityReport",
    "CapabilityRuntime",
    "FeatureCheck",
    "FeatureDeclaration",
    "FeatureLevel",
    "PERMISSION_LEVELS",
    "PermissionDecision",
    "PermissionPolicy",
    "AgentProfile",
    "AgentProfileRegistry",
    "ProviderFallbackAttempt",
    "ProviderFallbackChain",
    "ProviderFallbackResult",
    "PromptTemplate",
    "PromptTemplateRegistry",
    "PromptTemplateValidation",
    "PromptTemplateValidationError",
    "ReplayResult",
    "Approval",
    "ExecRequest",
    "ExecResult",
    "Sandbox",
    "Scope",
    "SubAgentResult",
    "SubAgentRunner",
    "StructuredOutputRepairResult",
    "AgentTool",
    "ToolContext",
    "ToolRegistry",
    "ToolResult",
    "JobResult",
    "default_tool_registry",
    "general_tool_registry",
    "register_writing_domain_tools",
    "repair_structured_output",
    "validate_or_repair",
]
