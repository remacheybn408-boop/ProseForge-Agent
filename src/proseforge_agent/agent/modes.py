"""Conversation mode and intent vocabularies."""

CONVERSATION_MODES: tuple[str, ...] = (
    "general_chat",
    "project_chat",
    "workflow_chat",
    "operator_chat",
    "creative_chat",
)

INTENT_NAMES: tuple[str, ...] = (
    "answer_directly",
    "retrieve_context",
    "update_memory_candidate",
    "start_workflow",
    "continue_workflow",
    "explain_artifact",
    "configure_provider",
    "diagnose_installation",
    "switch_mode",
    "ask_clarifying_question",
)

__all__ = ["CONVERSATION_MODES", "INTENT_NAMES"]
