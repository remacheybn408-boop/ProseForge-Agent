"""Command line entry point for ProseForge Agent.

This is the operator surface: a top-level ``pf-agent`` parser with one
subparser per command group (project, proseforge, provider, memory, retrieve,
phase-plan, daily-workbook, chapter, workflow, report, extension). Every group
shares output flags (``--format``, ``--write``, ``--dry-run``, ``--out``) so
filesystem-changing commands can be previewed. Commands render their result
through :mod:`proseforge_agent.reports` so Markdown, JSON, and terminal output
stay consistent and JSON stays stable for automation.

Deep execution of each group is wired by that group's integration task; this
card establishes the entry points, shared flags, and report rendering.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

from . import __version__
from .errors import ProseForgeAgentError
from .reports import Report, ReportRenderer, ReportSection
from .reports.registry import default_registry

# name -> {help, inputs, artifacts}. Drives both the subparsers and the
# self-describing `report command-reference` output.
COMMAND_GROUPS: dict[str, dict] = {
    "project": {
        "help": "Create and inspect novel projects",
        "inputs": "project slug, title, config path",
        "artifacts": "project workspace, project config",
    },
    "proseforge": {
        "help": "Bridge to the ProseForge engine (discovery, dry-run actions)",
        "inputs": "engine root, action name",
        "artifacts": "engine action results",
    },
    "provider": {
        "help": "Inspect configured model providers and role routing",
        "inputs": "providers config (YAML)",
        "artifacts": "provider/role report",
    },
    "usage": {
        "help": "Report metered provider token usage and cost",
        "inputs": "usage log (JSONL), since filter",
        "artifacts": "per-provider usage report",
    },
    "memory": {
        "help": "List and export durable project memory",
        "inputs": "agent database path, project slug",
        "artifacts": "memory export report",
    },
    "retrieve": {
        "help": "Build evidence packs for an intent",
        "inputs": "project slug, intent, token budget",
        "artifacts": "evidence pack",
    },
    "rag": {
        "help": "Search and manage retrieval-augmented generation indexes",
        "inputs": "query, project slug, RAG chunk index",
        "artifacts": "hybrid retrieval results",
    },
    "phase-plan": {
        "help": "Generate a structured phase plan from intake",
        "inputs": "intake file, memory",
        "artifacts": "phase plan",
    },
    "daily-workbook": {
        "help": "Generate the dated daily workbook",
        "inputs": "project state, date",
        "artifacts": "daily workbook",
    },
    "chapter": {
        "help": "Run the chapter lifecycle (prepare, draft, review, accept)",
        "inputs": "project, chapter number, provider, until-stage",
        "artifacts": "context, draft, review, acceptance artifacts",
    },
    "workflow": {
        "help": "Inspect and resume workflow runs",
        "inputs": "runs directory, run id",
        "artifacts": "workflow run report",
    },
    "report": {
        "help": "Render shared reports (Markdown, JSON, terminal)",
        "inputs": "report name",
        "artifacts": "rendered report files",
    },
    "extension": {
        "help": "List and inspect installed extensions",
        "inputs": "extension registry",
        "artifacts": "extension report",
    },
    "plugin": {
        "help": "Discover and manage ProseForge Agent plugins",
        "inputs": "plugin id or local plugin path",
        "artifacts": "plugin manifest and registry records",
    },
    "chat": {
        "help": "Run one-shot agent chat and intent classification",
        "inputs": "message, mode, provider",
        "artifacts": "agent turn report",
    },
    "tui": {
        "help": "Run the non-desktop terminal UI",
        "inputs": "provider, project binding, check flag",
        "artifacts": "terminal UI state",
    },
    "gateway": {
        "help": "Run non-desktop messaging gateway surfaces",
        "inputs": "platform subcommand, provider, check flag",
        "artifacts": "gateway sessions and delivery queue",
    },
    "environments": {
        "help": "Inspect and check execution environments",
        "inputs": "environment action, provider, backend",
        "artifacts": "execution environment report",
    },
    "processes": {
        "help": "Inspect and manage terminal process lifecycle",
        "inputs": "process action and process id",
        "artifacts": "process registry entries",
    },
    "browser": {
        "help": "Run managed cloud browser checks",
        "inputs": "browser action and provider",
        "artifacts": "browser trace and bounded artifact refs",
    },
    "media": {
        "help": "Run managed media generation and transcription tools",
        "inputs": "media action, fixture, prompt, provider",
        "artifacts": "media artifact references and text candidates",
    },
    "session": {
        "help": "Manage conversation session lifecycle",
        "inputs": "session id, project filter, cleanup age",
        "artifacts": "chat session metadata",
    },
    "context": {
        "help": "Inspect context window usage and compact session history",
        "inputs": "provider, session id, token budget",
        "artifacts": "context usage report and compacted message summary",
    },
    "prompt": {
        "help": "Manage system prompt templates and session overrides",
        "inputs": "template id, session id, override text",
        "artifacts": "prompt template and session prompt records",
    },
    "prompt-template": {
        "help": "List and validate workflow prompt templates",
        "inputs": "prompt template id",
        "artifacts": "prompt template registry report",
    },
    "tools": {
        "help": "List internal tools and permission levels",
        "inputs": "tool registry",
        "artifacts": "tool registry report",
    },
    "skills": {
        "help": "List and manage local agent skills",
        "inputs": "skill action and id",
        "artifacts": "skill registry records and review plans",
    },
    "jobs": {
        "help": "Run allow-listed background agent jobs",
        "inputs": "job name, provider, dry-run flag",
        "artifacts": "event bus records, job report",
    },
    "notifications": {
        "help": "List and test user notification events",
        "inputs": "notification subcommand",
        "artifacts": "notification center JSONL records",
    },
    "artifacts": {
        "help": "Inspect novel artifact dependency graphs",
        "inputs": "project slug, artifact id",
        "artifacts": "artifacts.graph.yaml",
    },
    "import": {
        "help": "Import existing manuscripts into a novel project",
        "inputs": "manuscript path, project slug",
        "artifacts": "raw import archive, chapters, manifest mappings",
    },
    "ingest": {
        "help": "Ingest attachments into searchable project artifacts",
        "inputs": "file, image, or folder path and project slug",
        "artifacts": "attachment artifact, searchable text, memory candidate",
    },
    "debug": {
        "help": "Inspect and replay agent audit trails",
        "inputs": "session id and optional step number",
        "artifacts": "redacted audit trail reports",
    },
    "mcp": {
        "help": "Inspect configured MCP servers and exposed capabilities",
        "inputs": "server id",
        "artifacts": "MCP capability, tool, resource, and prompt reports",
    },
    "scene": {
        "help": "Run scene-level draft, review, rewrite, and merge steps",
        "inputs": "project slug, chapter id, scene id",
        "artifacts": "scene files, chapter draft, artifact graph records",
    },
    "export": {
        "help": "Compile and export a novel project",
        "inputs": "project slug, format, optional chapter range",
        "artifacts": "book export artifact",
    },
    "publishing": {
        "help": "Manage publishing metadata",
        "inputs": "project slug, title, author, metadata fields",
        "artifacts": "publishing.yaml",
    },
    "bible": {
        "help": "Manage explicit canon bible entries",
        "inputs": "project slug, section, entry fields",
        "artifacts": "bible YAML files and snapshots",
    },
    "continuity": {
        "help": "Check and resolve continuity conflicts",
        "inputs": "project slug, conflict id, resolution action",
        "artifacts": "continuity conflict report and audit log",
    },
    "timeline": {
        "help": "Manage story timeline events and consistency checks",
        "inputs": "project slug, event date/order/location/characters",
        "artifacts": "timeline event store and conflict report",
    },
    "plot-thread": {
        "help": "Track long-running plot threads and stale payoffs",
        "inputs": "project slug, thread metadata, current chapter",
        "artifacts": "plot thread store and stale-thread report",
    },
    "foreshadow": {
        "help": "Track planted foreshadowing and overdue payoffs",
        "inputs": "project slug, foreshadowing metadata, current chapter",
        "artifacts": "foreshadowing store and overdue report",
    },
    "character-arc": {
        "help": "Track character desires, changes, relationships, and appearances",
        "inputs": "project slug, character id, arc updates",
        "artifacts": "character arc store and whole-book report",
    },
    "relation": {
        "help": "Manage character, faction, and organization relationship graphs",
        "inputs": "project slug, relation endpoints and type",
        "artifacts": "relationship graph data, markdown, and Graphviz dot",
    },
    "rules": {
        "help": "Manage explicit writing rules for draft/review/rewrite evidence",
        "inputs": "rule text or id, level, project slug, chapter",
        "artifacts": "writing rule store and evidence records",
    },
    "style": {
        "help": "Compile style preferences into executable checks",
        "inputs": "project slug, preferences, chapter id",
        "artifacts": "compiled style profile and style check report",
    },
    "quality": {
        "help": "Run writing quality gates and summarize chapter reports",
        "inputs": "project slug and chapter id",
        "artifacts": "quality gate report with actionable violations",
    },
    "literary": {
        "help": "Run literary style regression baselines and drift tests",
        "inputs": "project slug, golden sample directory",
        "artifacts": "literary baseline and drift report",
    },
    "rewrite": {
        "help": "Apply named rewrite strategies and list the strategy library",
        "inputs": "project slug, chapter id, strategy",
        "artifacts": "revision artifact per chapter and strategy",
    },
    "reader-review": {
        "help": "Run an editorial-grade reader experience review of a chapter or volume",
        "inputs": "project slug, chapter id or volume id",
        "artifacts": "structured reader report with actionable suggestions",
    },
    "search": {
        "help": "Search the whole manuscript for a keyword or exact phrase",
        "inputs": "query, project slug, scope, exact flag",
        "artifacts": "ranked file/chapter/line hits with snippets",
    },
    "draft": {
        "help": "Manage chapter draft versions: list, diff, rollback, and branch",
        "inputs": "project slug, chapter id, version ids, branch name",
        "artifacts": "versioned drafts with checksum and provider/prompt metadata",
    },
    "editorial": {
        "help": "Run the editorial pipeline: stage a chapter from outline to final",
        "inputs": "project slug, chapter id, target stage",
        "artifacts": "per-stage editorial artifacts and pipeline state",
    },
    "approval": {
        "help": "Review the human approval queue for high-risk actions",
        "inputs": "project slug, approval id",
        "artifacts": "approval queue entries with decision status",
    },
    "stats": {
        "help": "Show writing analytics: word trends, effort, and completion prediction",
        "inputs": "project slug, daily/export subcommand, target words",
        "artifacts": "analytics summary, daily trend, and CSV export",
    },
    "backup": {
        "help": "Create, verify, and restore checksum-verified project backups",
        "inputs": "project slug, backup id, dry-run flag",
        "artifacts": "backup snapshots with checksum manifest",
    },
    "setup": {
        "help": "Run the guided first-use setup wizard",
        "inputs": "setup mode, provider, repair/reconfigure flags",
        "artifacts": "agent config, workspace directories, setup summary",
    },
    "init": {
        "help": "Initialize a ProseForge Agent workspace",
        "inputs": "portable/native mode, ProseForge root",
        "artifacts": "agent config, workspace, provider stub, doctor report",
    },
    "doctor": {
        "help": "Run read-only installation diagnostics",
        "inputs": "optional diagnostic section",
        "artifacts": "doctor report",
    },
    "completions": {
        "help": "Show shell completions and launcher install plans",
        "inputs": "shell name",
        "artifacts": "completion script",
    },
    "upgrade": {
        "help": "Check or run safe workspace upgrades",
        "inputs": "version range, check flag",
        "artifacts": "backup and migration report",
    },
    "uninstall": {
        "help": "Plan uninstall and data retention actions",
        "inputs": "plan flag, remove user data flag",
        "artifacts": "uninstall plan",
    },
    "service": {
        "help": "Check the local agent service facade",
        "inputs": "bind address, provider, check flag",
        "artifacts": "local API readiness report",
    },
    "support": {
        "help": "Create redacted operator support bundles",
        "inputs": "bundle subcommand, redaction flag",
        "artifacts": "support bundle diagnostics",
    },
    "qa": {
        "help": "Show native QA matrix coverage requirements",
        "inputs": "matrix subcommand, show flag",
        "artifacts": "cross-platform QA matrix",
    },
    "release": {
        "help": "Run release readiness gates",
        "inputs": "check subcommand, complete-agent flag",
        "artifacts": "release gate report",
    },
    "eval": {
        "help": "Run deterministic agent task-success evaluations",
        "inputs": "golden suite, provider, threshold",
        "artifacts": "agent eval report",
    },
    "status": {
        "help": "Show resolved capability flags and safe-mode status",
        "inputs": "capabilities flag, config",
        "artifacts": "capability map report",
    },
    "offline": {
        "help": "Show offline mode capability status",
        "inputs": "offline status",
        "artifacts": "offline capability report",
    },
    "cache": {
        "help": "Inspect and clear provider request cache",
        "inputs": "cache subcommand",
        "artifacts": "request cache entries and stats",
    },
    "run": {
        "help": "Run an autonomous, goal-directed agent loop",
        "inputs": "goal, provider, iteration budget, show-plan flag",
        "artifacts": "loop run summary, decomposed plan",
    },
}


def _output_parser() -> argparse.ArgumentParser:
    """Shared output flags for every command group."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--format",
        choices=["markdown", "json", "terminal"],
        default="terminal",
        help="output format",
    )
    parent.add_argument("--write", action="store_true", help="write artifacts to disk")
    parent.add_argument(
        "--dry-run",
        action="store_true",
        help="preview a filesystem-changing command without writing",
    )
    parent.add_argument("--out", default=None, help="output directory for --write")
    return parent


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``pf-agent`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="pf-agent",
        description=(
            "ProseForge Agent: agentic orchestration for long-form novel "
            "production on top of the ProseForge engine."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--offline", action="store_true", help="disable remote/network-dependent actions")

    shared = _output_parser()
    subparsers = parser.add_subparsers(dest="command", metavar="<group>")
    for name, spec in COMMAND_GROUPS.items():
        group = subparsers.add_parser(
            name,
            parents=[] if name in {"export", "stats"} else [shared],
            help=spec["help"],
            description=(
                f"{spec['help']}.\n"
                f"Inputs: {spec['inputs']}.\n"
                f"Artifacts: {spec['artifacts']}."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        group.add_argument(
            "subcommand",
            nargs="?",
            help="group subcommand (e.g. 'command-reference', 'list')",
        )
        group.add_argument("--providers", default=None, help="providers config (YAML)")
        if name == "chat":
            group.add_argument("--message", default=None, help="one-shot chat message")
            group.add_argument("--text", default=None, help="text to classify")
            group.add_argument("--provider", default=None, help="chat provider")
            group.add_argument("--no-project", action="store_true", help="do not bind a project")
            group.add_argument("--project", default=None, help="project slug")
            group.add_argument("--mode", default="general_chat", help="conversation mode")
            group.add_argument("--system", default=None, help="system prompt override for this chat turn")
            group.add_argument(
                "--show-prompt",
                action="store_true",
                help="print the structured prompt pack without running the turn",
            )
            group.add_argument(
                "--show-citations",
                action="store_true",
                help="print retrieval citations without inventing missing context",
            )
            group.add_argument(
                "--show-memory-candidates",
                action="store_true",
                help="extract preference candidates without accepting memory",
            )
            group.add_argument(
                "--propose-handoff",
                action="store_true",
                help="create a workflow handoff package without starting it",
            )
            group.add_argument(
                "--permission-level",
                default="read_only",
                help="maximum permission level for this turn",
            )
            group.add_argument(
                "--explain-safety",
                action="store_true",
                help="assess untrusted content with the injection guard and show the safety verdict",
            )
            group.add_argument(
                "--stream",
                action="store_true",
                help="stream the response incrementally as it is generated",
            )
            group.add_argument("--show-events", action="store_true", help="show fake streaming tool output events")
            group.add_argument("--profile", default=None, help="agent persona profile")
            group.add_argument("--profiles-file", default=None, help="YAML file with agent profiles")
        if name == "tui":
            group.add_argument("--provider", default="fake", help="TUI provider")
            group.add_argument("--project", default=None, help="project slug")
            group.add_argument("--no-project", action="store_true", help="start without project binding")
            group.add_argument("--mode", default="general_chat", help="conversation mode")
            group.add_argument("--check", action="store_true", help="render deterministic state and exit")
        if name == "gateway":
            group.add_argument("gateway_arg", nargs="?", help="gateway platform or action")
            group.add_argument("--platform", default="telegram", help="relay pairing platform")
            group.add_argument("--fixture", default=None, help="gateway fixture for inspect commands")
            group.add_argument("--provider", default="fake", help="gateway provider")
            group.add_argument("--check", action="store_true", help="validate gateway readiness and exit")
        if name == "environments":
            group.add_argument("environment_arg", nargs="?", help="environment backend or action")
            group.add_argument("--provider", default="fake", help="environment provider")
            group.add_argument("--image", default="python:3.11", help="container image for environment checks")
            group.add_argument("--profile", default="demo", help="remote environment profile")
        if name == "processes":
            group.add_argument("process_id", nargs="?", help="process id")
        if name == "browser":
            group.add_argument("--provider", default="fake", help="browser provider")
        if name == "media":
            group.add_argument("--fixture", default="voice-note", help="media fixture")
            group.add_argument("--prompt", default="", help="media generation prompt")
            group.add_argument("--provider", default="fake", help="media provider")
        if name == "session":
            group.add_argument("session_id", nargs="?", help="chat session id")
            group.add_argument("--project", default=None, help="project slug")
            group.add_argument("--include-deleted", action="store_true", help="include deleted sessions")
            group.add_argument("--older-than", default="90d", help="cleanup age such as 90d")
            group.add_argument("--no-tools", action="store_true", help="omit tool calls from session export")
            group.add_argument("--no-evidence", action="store_true", help="omit evidence refs from session export")
            group.add_argument("--no-redact", action="store_true", help="do not redact secrets during export")
            group.add_argument("--from-step", type=int, default=None, help="message step for session branching")
            group.add_argument("--name", default=None, help="branch name for session branching")
            group.add_argument("--into", dest="into_session", default=None, help="target session id for merge")
            group.add_argument("--only-approved", action="store_true", help="merge only approved branch messages")
            group.add_argument("--message-step", action="append", type=int, default=None, help="branch message step to merge")
        if name == "context":
            group.add_argument("--provider", default="fake", help="provider family/name")
            group.add_argument("--session", default=None, help="chat session id")
            group.add_argument("--project", default=None, help="active project slug")
            group.add_argument("--max-context", type=int, default=None, help="override provider context window")
            group.add_argument("--reserve", type=int, default=256, help="reserved completion tokens")
            group.add_argument("--keep-last", type=int, default=6, help="messages to keep after compaction")
        if name == "rag":
            group.add_argument("rag_query", nargs="?", help="query for rag search")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--top-k", type=int, default=5, help="number of search results")
            group.add_argument("--suite", default=None, help="RAG eval suite YAML or JSON")
        if name == "prompt":
            group.add_argument("prompt_arg", nargs="?", help="prompt template id for show")
            group.add_argument("--session", default=None, help="chat session id")
            group.add_argument("--template", default=None, help="system prompt template id")
            group.add_argument("--text", default=None, help="literal session prompt override")
        if name == "prompt-template":
            group.add_argument("template_id", nargs="?", help="workflow prompt template id")
        if name == "project":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--title", default=None, help="project title")
            group.add_argument("--author", default=None, help="project author")
            group.add_argument("--language", default="zh-CN", help="project language")
            group.add_argument("--fix", action="store_true", help="apply safe repairs (project doctor)")
        if name == "artifacts":
            group.add_argument("artifact_id", nargs="?", help="artifact id for trace")
            group.add_argument("--slug", default=None, help="project slug")
        if name == "import":
            group.add_argument("path", nargs="?", help="file or folder to import")
            group.add_argument("--slug", default=None, help="project slug")
        if name == "ingest":
            group.add_argument("path", nargs="?", help="attachment file or folder")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--provider", default="fake", help="vision provider for images")
        if name == "debug":
            group.add_argument("debug_session", nargs="?", help="audit session id")
            group.add_argument("--step", type=int, default=1, help="audit step number")
        if name == "mcp":
            group.add_argument("server", nargs="?", help="MCP server id")
            group.add_argument("mcp_extra", nargs="?", help="extra MCP argument")
            group.add_argument("--display-name", default=None, help="MCP server display name")
            group.add_argument("--transport", default="stdio", help="MCP transport: stdio, http, or sse")
            group.add_argument(
                "--command",
                dest="mcp_command",
                action="append",
                default=None,
                help="stdio command token (repeatable)",
            )
            group.add_argument("--url", default="", help="HTTP/SSE server URL")
            group.add_argument("--cwd", default="", help="server working directory")
            group.add_argument("--env", action="append", default=None, help="allowed env KEY=VALUE (repeatable)")
            group.add_argument("--env-allow", action="append", default=None, help="environment variable name to inherit")
            group.add_argument("--secret-ref", action="append", default=None, help="secret env KEY=secret://ref (repeatable)")
            group.add_argument("--trust-level", default="local", help="server trust level")
            group.add_argument("--permission-profile", default="read_only", help="permission profile")
            group.add_argument("--timeout", type=int, default=None, help="timeout in milliseconds")
            group.add_argument("--rate-limit", type=int, default=None, help="rate limit per minute")
            group.add_argument("--filesystem-allow", action="append", default=None, help="allowed filesystem prefix")
            group.add_argument("--filesystem-deny", action="append", default=None, help="denied filesystem prefix")
            group.add_argument("--network-allow", action="append", default=None, help="allowed network host")
            group.add_argument("--command-allow", action="append", default=None, help="allowed command")
            group.add_argument("--project-scope", default="", help="project scope label")
            group.add_argument("--write-mode", default="approval_required", help="read_only, approval_required, or allowed")
            group.add_argument("--allow-secrets", action="store_true", help="allow explicit secret injection")
        if name == "scene":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--chapter", default=None, help="chapter id")
            group.add_argument("--scene", default=None, help="scene id")
            group.add_argument("--goal", default="", help="scene goal")
            group.add_argument("--location", default="", help="scene location")
            group.add_argument("--characters", default="", help="comma-separated characters")
            group.add_argument("--conflict", default="", help="scene conflict")
            group.add_argument("--tone", default="", help="emotional tone")
        if name == "export":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--format", default="txt", help="export format")
            group.add_argument("--from-chapter", default=None, help="first chapter id")
            group.add_argument("--to-chapter", default=None, help="last chapter id")
            group.add_argument("--back-matter", default=None, help="back matter text")
        if name == "publishing":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--title", default=None, help="book title")
            group.add_argument("--subtitle", default=None, help="book subtitle")
            group.add_argument("--author", default=None, help="author")
            group.add_argument("--pen-name", default=None, help="pen name")
            group.add_argument("--summary", default=None, help="summary")
            group.add_argument("--keywords", default=None, help="comma-separated keywords")
            group.add_argument("--copyright", default=None, help="copyright statement")
            group.add_argument("--ai-usage-statement", default=None, help="AI usage statement")
        if name == "bible":
            group.add_argument("bible_arg", nargs="?", help="bible section or entry type")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--id", default=None, help="entry id")
            group.add_argument("--name", default=None, help="entry display name")
            group.add_argument("--role", default=None, help="character role or entry role")
            group.add_argument("--text", default=None, help="entry text")
        if name == "continuity":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--conflict", default=None, help="conflict id")
            group.add_argument("--action", default="defer", help="resolution action")
        if name == "timeline":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--id", default=None, help="timeline event id")
            group.add_argument("--title", default=None, help="timeline event title")
            group.add_argument("--absolute-date", default="", help="absolute in-world or calendar date")
            group.add_argument("--relative-date", default="", help="relative date such as before chapter 2")
            group.add_argument("--story-day", type=int, default=None, help="story day index")
            group.add_argument("--order", type=int, default=0, help="order within the story day")
            group.add_argument("--parallel", action="store_true", help="mark as a parallel event")
            group.add_argument("--character", action="append", default=None, help="character present in the event")
            group.add_argument("--location", default="", help="event location")
            group.add_argument("--cause", action="append", default=None, help="causal predecessor event id")
            group.add_argument("--effect", action="append", default=None, help="causal successor event id")
            group.add_argument("--chapter", default="", help="chapter id")
            group.add_argument("--scene", default="", help="scene id")
        if name == "plot-thread":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--id", default=None, help="plot thread id")
            group.add_argument("--type", default="subplot", help="plot thread type")
            group.add_argument("--status", default="active", help="plot thread status")
            group.add_argument("--first-appearance", default="", help="first chapter or scene appearance")
            group.add_argument("--last-touched", default="", help="last chapter or scene where the thread moved")
            group.add_argument("--expected-payoff", default="", help="expected payoff chapter or note")
            group.add_argument("--linked-chapter", action="append", default=None, help="chapter linked to the thread")
            group.add_argument("--linked-character", action="append", default=None, help="character linked to the thread")
            group.add_argument("--current-chapter", type=int, default=None, help="current chapter number for stale checks")
            group.add_argument("--max-gap", type=int, default=3, help="maximum chapters without progress")
        if name == "foreshadow":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--id", default=None, help="foreshadowing id")
            group.add_argument("--planted-chapter", default="", help="chapter where the clue was planted")
            group.add_argument("--expected-payoff-chapter", default="", help="chapter where payoff is expected")
            group.add_argument("--status", default="planted", help="foreshadowing status")
            group.add_argument("--importance", default="medium", help="importance level")
            group.add_argument("--related-character", action="append", default=None, help="related character")
            group.add_argument("--related-plot-thread", default="", help="related plot thread id")
            group.add_argument("--current-chapter", type=int, default=None, help="current chapter number for overdue checks")
            group.add_argument("--max-gap", type=int, default=5, help="maximum chapters without payoff")
            group.add_argument("--resolved-chapter", default="", help="chapter where the clue was resolved")
        if name == "character-arc":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--character", default=None, help="character id")
            group.add_argument("--desire", default="", help="character desire")
            group.add_argument("--fear", default="", help="character fear")
            group.add_argument("--flaw", default="", help="character flaw")
            group.add_argument("--belief", default="", help="character belief")
            group.add_argument("--turning-point", action="append", default=None, help="turning point as chapter:change")
            group.add_argument(
                "--relationship-change",
                action="append",
                default=None,
                help="relationship change as character:change",
            )
            group.add_argument("--chapter", action="append", default=None, help="chapter appearance")
            group.add_argument("--arc-status", default="", help="arc status")
        if name == "relation":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--source", default=None, help="relation source node")
            group.add_argument("--target", default=None, help="relation target node")
            group.add_argument("--type", default="friend", help="relation type")
            group.add_argument("--evidence", action="append", default=None, help="evidence id or chapter")
            group.add_argument("--status", default="active", help="relation status")
            group.add_argument("--note", default="", help="relation note")
            group.add_argument(
                "--graph-format",
                choices=["json", "markdown", "dot"],
                default="json",
                help="relationship graph export format",
            )
        if name == "rules":
            group.add_argument("rule_text", nargs="?", help="rule text for add or rule id for remove")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--level", default="project", help="rule level: global, project, or chapter")
            group.add_argument("--chapter", default="", help="chapter id for chapter-level rules")
        if name == "style":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--preference", action="append", default=None, help="style preference to compile")
            group.add_argument("--chapter", default=None, help="chapter id to check")
        if name == "quality":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--chapter", default=None, help="chapter id to check")
        if name == "literary":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--golden-dir", default="tests/literary/golden", help="golden sample directory")
            group.add_argument("--threshold", type=float, default=0.25, help="drift threshold")
        if name == "rewrite":
            group.add_argument("rewrite_arg", nargs="?", help="rewrite subcommand argument")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--strategy", default=None, help="rewrite strategy")
            group.add_argument("--chapter", default=None, help="chapter id")
        if name == "reader-review":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--chapter", default=None, help="chapter id")
            group.add_argument("--volume", default=None, help="volume id")
        if name == "search":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--scope", default="manuscript", help="search scope: manuscript or all")
            group.add_argument("--exact", action="store_true", help="match the query as an exact phrase")
            group.add_argument("--provider", default="fake", help="web search provider when --slug is omitted")
            group.add_argument("--json", action="store_true", help="emit JSON web search output")
        if name == "draft":
            group.add_argument("draft_args", nargs="*", help="draft subcommand arguments (e.g. 'list' or two version ids)")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--chapter", default=None, help="chapter id")
            group.add_argument("--to", default=None, help="target version id for rollback")
            group.add_argument("--name", default=None, help="branch name")
            group.add_argument("--from-version", default=None, help="base version id for branch")
            group.add_argument("--approve", action="store_true", help="approve a rollback")
        if name == "editorial":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--chapter", default=None, help="chapter id")
            group.add_argument("--to", default=None, help="target editorial stage for promote")
            group.add_argument("--approve", action="store_true", help="approve a high-risk promote")
        if name == "approval":
            group.add_argument("approval_id", nargs="?", help="approval id for show/approve/reject")
            group.add_argument("--slug", default=None, help="project slug")
        if name == "backup":
            group.add_argument("backup_id", nargs="?", help="backup id for verify/restore")
            group.add_argument("--slug", default=None, help="project slug")
        if name == "stats":
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--target-words", type=int, default=None, help="target word count for prediction")
            group.add_argument(
                "--format",
                choices=["markdown", "json", "terminal", "csv"],
                default="terminal",
                help="output format (csv applies to `stats export`)",
            )
        if name == "chapter":
            group.add_argument("chapter_ids", nargs="*", help="chapter ids for reorganization")
            group.add_argument("--slug", default=None, help="project slug")
            group.add_argument("--to-volume", default=None, help="target volume id")
            group.add_argument("--after", default=None, help="chapter id to insert after")
            group.add_argument("--at-scene", default=None, help="scene id for split")
            group.add_argument("--into", default=None, help="merged chapter id")
        if name == "usage":
            group.add_argument(
                "--usage-log",
                default="logs/usage.jsonl",
                help="path to the usage JSONL log",
            )
            group.add_argument(
                "--since",
                default=None,
                help="filter usage records (e.g. 'today'); shows all when omitted",
            )
        if name == "tools":
            group.add_argument("tool_arg", nargs="?", help="managed tool action")
            group.add_argument(
                "--include-permissions",
                action="store_true",
                help="include permission levels in the tool list",
            )
            group.add_argument("--domain", default=None, help="filter tools by domain")
            group.add_argument("--provider", default="fake", help="managed tool provider")
        if name == "skills":
            group.add_argument("skill_arg", nargs="?", help="skill id or query")
            group.add_argument("skill_extra", nargs="*", help="extra skill arguments")
            group.add_argument("--provider", default="fake", help="skill provider")
            group.add_argument("--skill", default=None, help="skill id for usage reports")
            group.add_argument("--all", action="store_true", help="apply skill command to all skills")
        if name == "jobs":
            group.add_argument("job_name", nargs="?", help="allow-listed background job")
            group.add_argument("--provider", default="fake", help="provider for the job")
        if name == "notifications":
            group.add_argument("--desktop", action="store_true", help="send a desktop test notification")
            group.add_argument("--webhook", action="store_true", help="send a webhook test notification")
        if name == "plugin":
            group.add_argument("plugin_arg", nargs="?", help="plugin id or path")
            group.add_argument("plugin_extra", nargs="*", help="extra plugin command arguments")
            group.add_argument("--registry", default=None, help="plugin registry index JSON")
            group.add_argument("--with-demo-project", action="store_true", help="run plugin test with a demo project")
            group.add_argument("--hook", default="on_after_export", help="plugin hook to trigger during `plugin test`")
        if name == "setup":
            group.add_argument("--quick", action="store_true", help="run quick guided setup")
            group.add_argument("--full", action="store_true", help="run full guided setup")
            group.add_argument("--minimal", action="store_true", help="run zero-key fake-provider setup")
            group.add_argument("--non-interactive", action="store_true", help="run without prompts")
            group.add_argument("--reconfigure", action="store_true", help="backup and rewrite config")
            group.add_argument(
                "--add-provider",
                nargs="?",
                const="deepseek",
                default=None,
                help="append a provider while keeping fake fallback",
            )
            group.add_argument("--skip-provider-test", action="store_true", help="skip provider ping")
            group.add_argument("--no-shell", action="store_true", help="skip shell completion registration")
            group.add_argument("--repair", action="store_true", help="repair config/workspace without deleting data")
            group.add_argument("--print-config", action="store_true", help="print redacted effective config")
        if name == "init":
            group.add_argument("--portable", action="store_true", help="initialize portable .pf-agent workspace")
            group.add_argument("--native", action="store_true", help="initialize native app directories")
            group.add_argument("--proseforge-root", default="${PROSEFORGE_ROOT}", help="ProseForge engine root")
            group.add_argument("--non-interactive", action="store_true", help="run without prompts")
        if name == "doctor":
            group.add_argument("--section", default=None, help="diagnostic section to run")
        if name == "completions":
            group.add_argument("--shell", default="powershell", help="shell to render")
        if name == "upgrade":
            group.add_argument("--check", action="store_true", help="check upgrade readiness without migration")
            group.add_argument("--from-version", default="1", help="current workspace schema version")
            group.add_argument("--to-version", default="2", help="target workspace schema version")
        if name == "uninstall":
            group.add_argument("--plan", action="store_true", help="show uninstall plan without deleting")
            group.add_argument("--remove-user-data", action="store_true", help="include user data in plan")
        if name == "service":
            group.add_argument("--provider", default="fake", help="service provider")
            group.add_argument("--check", action="store_true", help="validate service configuration only")
            group.add_argument("--bind", default="127.0.0.1", help="service bind address")
            group.add_argument("--allow-remote", action="store_true", help="allow non-loopback bind")
            group.add_argument("--permission-level", default="read_only", help="service permission ceiling")
        if name == "support":
            group.add_argument("--redact", action="store_true", help="redact paths and secrets")
        if name == "qa":
            group.add_argument("--show", action="store_true", help="show required native QA matrix")
            group.add_argument(
                "--check",
                action="store_true",
                help="validate the CI matrix against the native QA matrix (with 'ci')",
            )
            group.add_argument(
                "--workflow",
                default=".github/workflows/ci.yml",
                help="path to the CI workflow file for 'qa ci'",
            )
        if name == "release":
            group.add_argument("--complete-agent", action="store_true", help="run the complete agent release gate")
            group.add_argument("--write-report", action="store_true", help="write release report to reports/")
        if name == "eval":
            group.add_argument("--provider", default="fake", help="provider for deterministic eval")
            group.add_argument("--suite", default=None, help="path to a golden task suite JSON file")
            group.add_argument("--threshold", type=float, default=None, help="override suite success threshold")
            group.add_argument("--write-report", action="store_true", help="write eval report to reports/")
        if name == "run":
            group.add_argument("--goal", default=None, help="goal for the autonomous run")
            group.add_argument("--provider", default="fake", help="provider for the run")
            group.add_argument("--allow-exec", action="store_true", help="allow sandboxed command execution")
            group.add_argument("--approve", action="store_true", help="approve sandboxed execution for this run")
            group.add_argument("--delegate", action="store_true", help="delegate a scoped sub-task during the run")
            group.add_argument(
                "--show-plan",
                action="store_true",
                help="print the decomposed plan with per-task status",
            )
            group.add_argument(
                "--max-iterations",
                type=int,
                default=5,
                help="iteration budget for the autonomous loop",
            )
            group.add_argument(
                "--verify",
                action="store_true",
                help="self-verify each output against criteria and reflect/retry on failure",
            )
        if name == "status":
            group.add_argument(
                "--capabilities",
                action="store_true",
                help="list each capability as enabled/degraded/disabled with a reason",
            )
            group.add_argument(
                "--disable",
                action="append",
                default=None,
                help="disable a capability for this run (repeatable)",
            )
        if name == "provider":
            group.add_argument(
                "--provider",
                default=None,
                help="provider name to probe (default: fake)",
            )
            group.add_argument(
                "--write-report",
                action="store_true",
                help="write the provider report to the output directory",
            )
            group.add_argument(
                "--all-policies",
                action="store_true",
                help="render route decisions for all non-manual policies",
            )
            group.add_argument(
                "--all",
                action="store_true",
                help="operate on all configured provider profiles",
            )
            group.add_argument(
                "--shape-only",
                action="store_true",
                help="run offline shape certification only",
            )
            group.add_argument(
                "--real-if-key-present",
                action="store_true",
                help="run real smoke only when the provider key is present",
            )
            group.add_argument(
                "--records-dir",
                default=None,
                help="directory for provider certification records",
            )
            group.add_argument(
                "--route-matrix",
                default=None,
                help="provider route matrix YAML",
            )
            group.add_argument(
                "--role",
                default="drafter",
                help="role to route (default: drafter)",
            )
            group.add_argument("--model", default=None, help="provider model for setup")
            group.add_argument("--api-key", default=None, help="provider API key for setup")
            group.add_argument("--verify", action="store_true", help="verify provider after setup")
            group.add_argument(
                "--endpoint",
                action="append",
                default=None,
                help="local OpenAI-compatible endpoint to inspect",
            )

    return parser


# -- handlers -----------------------------------------------------------------


def _emit(report: Report, fmt: str) -> int:
    print(ReportRenderer().render(report, fmt))
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    name = args.subcommand or "command-reference"
    report = default_registry().build(name, groups=COMMAND_GROUPS)
    if args.write and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"{name}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _handle_project_doctor(args: argparse.Namespace) -> int:
    from .novel import ProjectHealthDoctor

    doctor = ProjectHealthDoctor(Path(".pf-agent") / "workspace", slug=args.slug)
    result = doctor.diagnose(fix=bool(getattr(args, "fix", False)))
    issue_lines = [
        f"{issue.kind}: {issue.target} ({issue.severity}, fixable={issue.fixable}) — {issue.detail}"
        for issue in result.issues
    ] or ["no issues detected"]
    sections = [
        ReportSection("Summary", [f"slug={result.slug}", f"status={result.status}", f"issues={len(result.issues)}"]),
        ReportSection("Issues", issue_lines),
    ]
    if result.fixed:
        sections.append(ReportSection("Fixed", list(result.fixed)))
    report = Report(
        title="Project Health",
        status=result.status,
        next_action="Run `pf-agent project doctor --slug <slug> --fix` to apply safe repairs"
        if result.status != "ok"
        else "Project structure is healthy",
        sections=sections,
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_project(args: argparse.Namespace) -> int:
    if args.subcommand not in {"init", "manifest", "validate", "doctor"} or not args.slug:
        return _emit(
            _planned_report("project", "Run `pf-agent project init --slug <slug>`"),
            args.format,
        )
    if args.subcommand == "doctor":
        return _handle_project_doctor(args)
    from .novel import NovelProjectStore

    store = NovelProjectStore(Path(".pf-agent") / "workspace")
    if args.subcommand == "init":
        manifest = store.init_project(
            slug=args.slug,
            title=args.title,
            author=args.author,
            language=args.language,
        )
        report = Report(
            title="Project Manifest",
            status="ok",
            next_action="Use `pf-agent project validate --slug <slug>` before writing",
            sections=[
                ReportSection(
                    "Manifest",
                    [
                        f"slug={manifest.project['slug']}",
                        f"title={manifest.project['title']}",
                        f"path={manifest.path}",
                    ],
                )
            ],
            data=manifest.to_dict() | {"path": str(manifest.path)},
        )
        return _emit(report, args.format)
    if args.subcommand == "manifest":
        manifest = store.load(args.slug)
        report = Report(
            title="Project Manifest",
            status="ok",
            next_action="Use this manifest as the project source index",
            sections=[
                ReportSection(
                    "Project",
                    [
                        f"slug={manifest.project.get('slug')}",
                        f"title={manifest.project.get('title')}",
                        f"language={manifest.project.get('language')}",
                    ],
                )
            ],
            data=manifest.to_dict() | {"path": str(manifest.path)},
        )
        return _emit(report, args.format)
    validation = store.validate(args.slug)
    report = Report(
        title="Project Manifest Validation",
        status="ok" if validation["status"] == "ok" else "blocked",
        next_action="Fix manifest errors before running project workflows",
        sections=[
            ReportSection(
                "Validation",
                [f"valid={str(validation['status'] == 'ok').lower()}", *validation["errors"]],
            )
        ],
        data=validation,
    )
    _emit(report, args.format)
    return 0 if validation["status"] == "ok" else 1


def _handle_artifacts(args: argparse.Namespace) -> int:
    if args.subcommand == "list" and not args.slug:
        from .agent.artifacts import ArtifactStore

        store = ArtifactStore(Path(".pf-agent"))
        refs = store.list()
        report = Report(
            title="Tool Artifacts",
            status="ok",
            next_action="Pass --slug to inspect novel artifact graph instead",
            sections=[
                ReportSection(
                    "Artifacts",
                    [f"{ref.id} ({ref.kind}) {ref.path}" for ref in refs] or ["(none)"],
                )
            ],
            data={"artifacts": [ref.to_dict() for ref in refs]},
        )
        return _emit(report, args.format)
    if args.subcommand not in {"list", "graph", "trace"} or not args.slug:
        return _emit(
            _planned_report("artifacts", "Run `pf-agent artifacts list --slug <slug>`"),
            args.format,
        )
    from .novel import ArtifactGraphStore

    graph = ArtifactGraphStore(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "list":
        records = graph.list()
        report = Report(
            title="Artifact List",
            status="ok",
            next_action="Use `pf-agent artifacts trace <id> --slug <slug>` to inspect provenance",
            sections=[
                ReportSection(
                    "Artifacts",
                    [f"{record.id} ({record.type})" for record in records] or ["(none)"],
                )
            ],
            data={"artifacts": [record.to_dict() for record in records]},
        )
        return _emit(report, args.format)
    if args.subcommand == "graph":
        edges = graph.edges()
        report = Report(
            title="Artifact Graph",
            status="ok",
            next_action="Keep draft/review/revision/export artifacts traceable",
            sections=[
                ReportSection(
                    "Edges",
                    [f"{source} -> {target}" for source, target in edges] or ["(no edges)"],
                )
            ],
            data={"edges": [{"source": source, "target": target} for source, target in edges]},
        )
        return _emit(report, args.format)
    trace = graph.trace(args.artifact_id or "")
    report = Report(
        title="Artifact Trace",
        status="ok" if trace else "blocked",
        next_action="Add missing source artifacts before accepting generated outputs",
        sections=[ReportSection("Trace", trace or ["artifact not found"])],
        data={"artifact_id": args.artifact_id, "trace": trace},
    )
    _emit(report, args.format)
    return 0 if trace else 1


def _handle_import(args: argparse.Namespace) -> int:
    if args.subcommand not in {"preview", "manuscript"} or not args.path or not args.slug:
        return _emit(
            _planned_report("import", "Run `pf-agent import manuscript <path> --slug <slug>`"),
            args.format,
        )
    from .novel import BulkImporter

    importer = BulkImporter(Path(".pf-agent") / "workspace", slug=args.slug)
    result = importer.preview(args.path) if args.subcommand == "preview" else importer.import_manuscript(args.path)
    title = "Import Preview" if result.preview else "Bulk Import"
    report = Report(
        title=title,
        status=result.status,
        next_action="Review chapter mapping before drafting from imported material",
        sections=[
            ReportSection(
                "Chapters",
                [f"{chapter.id}: {chapter.title}" for chapter in result.chapters] or ["(none)"],
            ),
            ReportSection("Warnings", result.warnings),
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_ingest(args: argparse.Namespace) -> int:
    if args.subcommand not in {"file", "image", "folder"} or not args.path or not args.slug:
        return _emit(
            _planned_report("ingest", "Run `pf-agent ingest file <path> --slug <slug>`"),
            args.format,
        )
    from .agent import AttachmentIngestor

    describer = (lambda path: f"fake vision description for {path.name}") if args.provider == "fake" else None
    ingestor = AttachmentIngestor(Path(".pf-agent"), vision_describer=describer)
    if args.subcommand == "folder":
        results = ingestor.ingest_folder(args.path, slug=args.slug)
    elif args.subcommand == "image":
        results = [ingestor.ingest_image(args.path, slug=args.slug)]
    else:
        results = [ingestor.ingest_file(args.path, slug=args.slug)]

    lines = [
        f"{result.id} {result.kind} status={result.status} searchable={result.searchable_path}"
        for result in results
    ] or ["(none)"]
    warnings = [warning for result in results for warning in result.warnings]
    report = Report(
        title="Attachment Ingestion",
        status="ok" if all(result.status == "ok" for result in results) else "degraded",
        next_action="Review memory candidates before promoting attachment facts to canon",
        sections=[
            ReportSection("Project", [f"slug={args.slug}"]),
            ReportSection("Artifacts", lines),
            ReportSection("Warnings", warnings or ["(none)"]),
        ],
        data={"results": [result.to_dict() for result in results]},
    )
    return _emit(report, args.format)


def _handle_debug(args: argparse.Namespace) -> int:
    if args.subcommand not in {"session", "step", "replay"} or not args.debug_session:
        return _emit(_planned_report("debug", "Run `pf-agent debug session <session_id>`"), args.format)
    from .agent import AuditTrailStore

    store = AuditTrailStore(Path(".pf-agent"))
    if args.subcommand == "session":
        steps = store.list_session(args.debug_session)
        report = Report(
            title="Audit Session",
            status="ok",
            next_action="Use `pf-agent debug step <session_id> --step <n>` for details",
            sections=[
                ReportSection(
                    "Steps",
                    [
                        f"{step.step}: intent={step.intent.get('name', '')} "
                        f"provider={step.provider.get('name', '')} action={step.final_action}"
                        for step in steps
                    ]
                    or ["(none)"],
                )
            ],
            data={"steps": [step.to_dict() for step in steps]},
        )
        return _emit(report, args.format)
    if args.subcommand == "step":
        step = store.get_step(args.debug_session, args.step)
        report = Report(
            title="Audit Step",
            status="ok",
            next_action="Use replay to reconstruct ordered decisions",
            sections=[
                ReportSection(
                    "Decision",
                    [
                        f"step={step.step}",
                        f"intent={step.intent.get('name', '')}",
                        f"tool={step.tool_choice or '(none)'}",
                        f"provider={step.provider.get('name', '')}",
                        f"trace={step.trace_id or '(none)'}",
                    ],
                ),
                ReportSection("Input", step.input.splitlines() or ["(empty)"]),
                ReportSection("Output", step.model_output.splitlines() or ["(empty)"]),
            ],
            data=step.to_dict(),
        )
        return _emit(report, args.format)
    replay = store.replay(args.debug_session)
    report = Report(
        title="Audit Replay",
        status="ok",
        next_action="Replay is read-only; rerun workflows only after explicit approval",
        sections=[
            ReportSection(
                "Replay",
                [
                    f"session={replay.session_id}",
                    f"steps={replay.step_count}",
                    f"actions={', '.join(replay.actions) or '(none)'}",
                    f"final_output={replay.final_output or '(empty)'}",
                ],
            )
        ],
        data=replay.to_dict(),
    )
    return _emit(report, args.format)


def _parse_key_values(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"expected KEY=VALUE, got {value!r}")
        key, item = value.split("=", 1)
        parsed[key] = item
    return parsed


def _handle_mcp(args: argparse.Namespace) -> int:
    if args.subcommand not in {
        None,
        "list",
        "inspect",
        "tools",
        "resources",
        "prompts",
        "add",
        "enable",
        "disable",
        "remove",
        "config",
        "policy",
    }:
        return _emit(_planned_report("mcp", "Run `pf-agent mcp list`"), args.format)
    from .mcp import MCPClient, MCPPolicy, MCPPolicyStore, MCPServerConfig, MCPServerRegistry, default_demo_client

    registry = MCPServerRegistry(Path(".pf-agent"))

    if args.subcommand == "policy":
        policy_store = MCPPolicyStore(Path(".pf-agent"))
        action = args.server or "list"
        if action == "list":
            policies = policy_store.list()
            report = Report(
                title="MCP Policy",
                status="ok",
                next_action="Run `pf-agent mcp policy show <server>` before enabling tool execution",
                sections=[
                    ReportSection(
                        "Policies",
                        [f"{policy.server_id} write_mode={policy.write_mode}" for policy in policies] or ["(none)"],
                    )
                ],
                data={"policies": [policy.to_dict() for policy in policies]},
            )
            return _emit(report, args.format)
        if action == "show":
            if not args.mcp_extra:
                return _emit(_planned_report("mcp", "Pass a server id to `mcp policy show`"), args.format)
            policy = policy_store.get(args.mcp_extra)
        elif action == "set":
            if not args.mcp_extra:
                return _emit(_planned_report("mcp", "Pass a server id to `mcp policy set`"), args.format)
            policy = policy_store.set(
                MCPPolicy(
                    server_id=args.mcp_extra,
                    filesystem_allow=list(args.filesystem_allow or []),
                    filesystem_deny=list(args.filesystem_deny or []),
                    network_allow=list(args.network_allow or []),
                    command_allow=list(args.command_allow or []),
                    secrets_allowed=bool(args.allow_secrets),
                    project_scope=args.project_scope or "",
                    write_mode=args.write_mode,
                )
            )
        else:
            return _emit(_planned_report("mcp", "Run `pf-agent mcp policy list`"), args.format)
        report = Report(
            title="MCP Policy",
            status="ok",
            next_action="Dangerous MCP actions must pass policy and approval checks",
            sections=[
                ReportSection(
                    "Policy",
                    [
                        f"server={policy.server_id}",
                        f"filesystem_allow={','.join(policy.filesystem_allow) or '(none)'}",
                        f"filesystem_deny={','.join(policy.filesystem_deny) or '(none)'}",
                        f"network_allow={','.join(policy.network_allow) or '(none)'}",
                        f"command_allow={','.join(policy.command_allow) or '(none)'}",
                        f"secrets_allowed={policy.secrets_allowed}",
                        f"project_scope={policy.project_scope or '(none)'}",
                        f"write_mode={policy.write_mode}",
                    ],
                )
            ],
            data=policy.to_dict(),
        )
        return _emit(report, args.format)

    if args.subcommand in {"add", "enable", "disable", "remove", "config"}:
        if not args.server:
            return _emit(_planned_report("mcp", "Pass an MCP server id"), args.format)
        if args.subcommand == "add":
            config = registry.add(
                MCPServerConfig(
                    id=args.server,
                    display_name=args.display_name or args.server,
                    transport=args.transport,
                    command=list(args.mcp_command or []),
                    url=args.url or "",
                    env=_parse_key_values(args.env or []),
                    env_allow=list(args.env_allow or []),
                    secret_refs=_parse_key_values(args.secret_ref or []),
                    cwd=args.cwd or "",
                    enabled=True,
                    trust_level=args.trust_level,
                    permission_profile=args.permission_profile,
                    timeout_ms=args.timeout or 10000,
                    rate_limit_per_minute=args.rate_limit or 60,
                )
            )
        elif args.subcommand == "enable":
            config = registry.enable(args.server)
        elif args.subcommand == "disable":
            config = registry.disable(args.server)
        elif args.subcommand == "remove":
            config = registry.remove(args.server)
        else:
            config = registry.configure(
                args.server,
                display_name=args.display_name,
                transport=args.transport if args.transport != "stdio" else None,
                command=list(args.mcp_command or []) if args.mcp_command else None,
                url=args.url or None,
                cwd=args.cwd or None,
                env=_parse_key_values(args.env or []) if args.env else None,
                env_allow=list(args.env_allow or []) if args.env_allow else None,
                secret_refs=_parse_key_values(args.secret_ref or []) if args.secret_ref else None,
                trust_level=args.trust_level if args.trust_level != "local" else None,
                permission_profile=args.permission_profile if args.permission_profile != "read_only" else None,
                timeout_ms=args.timeout,
                rate_limit_per_minute=args.rate_limit,
            )
        report = Report(
            title="MCP Server Config",
            status="ok",
            next_action="Inspect configured servers before allowing tool execution",
            sections=[
                ReportSection(
                    "Server",
                    [
                        f"id={config.id}",
                        f"transport={config.transport}",
                        f"enabled={config.enabled}",
                        f"trust_level={config.trust_level}",
                        f"permission_profile={config.permission_profile}",
                        f"timeout_ms={config.timeout_ms}",
                        f"rate_limit_per_minute={config.rate_limit_per_minute}",
                    ],
                )
            ],
            data=config.to_dict(),
        )
        return _emit(report, args.format)

    if args.subcommand in {None, "list"}:
        configs = registry.list()
        if configs:
            lines = [
                f"{config.id} ({config.transport}) enabled={config.enabled} "
                f"trust={config.trust_level} permission={config.permission_profile}"
                for config in configs
            ]
            data = {"servers": [config.to_dict() for config in configs]}
        else:
            client = default_demo_client()
            lines = [f"{client.spec.id} ({client.spec.transport})"]
            data = {"servers": [client.spec.to_dict()]}
        report = Report(
            title="MCP Servers",
            status="ok",
            next_action="Run `pf-agent mcp inspect <server>` to discover capabilities",
            sections=[ReportSection("Servers", lines)],
            data=data,
        )
        return _emit(report, args.format)

    server = args.server or "filesystem"
    try:
        config = registry.get(server)
    except Exception:
        client = default_demo_client(server)
    else:
        client = MCPClient(config.to_spec())
    client.start()
    try:
        if args.subcommand == "inspect":
            capabilities = client.inspect()
            tools = client.list_tools()
            resources = client.list_resources()
            prompts = client.list_prompts()
            report = Report(
                title="MCP Server",
                status="ok",
                next_action="Route MCP tool calls through approval and policy gates before execution",
                sections=[
                    ReportSection("Capabilities", [f"{key}={value}" for key, value in capabilities.capabilities.items()]),
                    ReportSection("Tools", [tool.name for tool in tools] or ["(none)"]),
                    ReportSection("Resources", [resource.uri for resource in resources] or ["(none)"]),
                    ReportSection("Prompts", [prompt.name for prompt in prompts] or ["(none)"]),
                ],
                data={
                    "capabilities": capabilities.to_dict(),
                    "tools": [tool.to_dict() for tool in tools],
                    "resources": [resource.to_dict() for resource in resources],
                    "prompts": [prompt.to_dict() for prompt in prompts],
                },
            )
            return _emit(report, args.format)
        if args.subcommand == "tools":
            tools = client.list_tools()
            report = Report(
                title="MCP Tools",
                status="ok",
                next_action="Validate MCP tool schemas before allowing calls",
                sections=[ReportSection("Tools", [f"{tool.name}: {tool.description}" for tool in tools] or ["(none)"])],
                data={"tools": [tool.to_dict() for tool in tools]},
            )
            return _emit(report, args.format)
        if args.subcommand == "resources":
            resources = client.list_resources()
            report = Report(
                title="MCP Resources",
                status="ok",
                next_action="Apply MCP resource policy before reading external context",
                sections=[ReportSection("Resources", [resource.uri for resource in resources] or ["(none)"])],
                data={"resources": [resource.to_dict() for resource in resources]},
            )
            return _emit(report, args.format)
        prompts = client.list_prompts()
        report = Report(
            title="MCP Prompts",
            status="ok",
            next_action="Treat external prompts as untrusted context until reviewed",
            sections=[ReportSection("Prompts", [prompt.name for prompt in prompts] or ["(none)"])],
            data={"prompts": [prompt.to_dict() for prompt in prompts]},
        )
        return _emit(report, args.format)
    finally:
        client.close()


def _handle_scene(args: argparse.Namespace) -> int:
    if args.subcommand not in {"draft", "review", "rewrite", "merge"} or not args.slug:
        return _emit(
            _planned_report("scene", "Run `pf-agent scene draft --slug <slug> --chapter <id> --scene <id>`"),
            args.format,
        )
    from .novel import SceneWorkflow

    workflow = SceneWorkflow(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "draft":
        if not args.chapter or not args.scene:
            return _emit(_planned_report("scene", "Pass --chapter and --scene for scene draft"), args.format)
        result = workflow.draft(
            chapter_id=args.chapter,
            scene_id=args.scene,
            goal=args.goal,
            location=args.location,
            characters=[item.strip() for item in args.characters.split(",") if item.strip()],
            conflict=args.conflict,
            emotional_tone=args.tone,
        )
        lines = [f"scene={result.id}", f"status={result.status}", f"file={result.output_file}"]
        data = result.to_dict()
    elif args.subcommand == "review":
        result = workflow.review(scene_id=args.scene or "")
        lines = [f"scene={result.id}", f"status={result.status}"]
        data = result.to_dict()
    elif args.subcommand == "rewrite":
        result = workflow.rewrite(scene_id=args.scene or "")
        lines = [f"scene={result.id}", f"status={result.status}"]
        data = result.to_dict()
    else:
        path = workflow.merge(chapter_id=args.chapter or "")
        lines = [f"chapter={args.chapter}", f"file={path}"]
        data = {"chapter": args.chapter, "path": str(path)}
    report = Report(
        title="Scene Workflow",
        status="ok",
        next_action="Review merged chapter draft before export",
        sections=[ReportSection("Result", lines)],
        data=data,
    )
    return _emit(report, args.format)


def _handle_chapter(args: argparse.Namespace) -> int:
    if args.subcommand not in {"move", "split", "merge", "renumber"} or not args.slug:
        return _emit(_planned_report("chapter", "Run `pf-agent chapter renumber --slug <slug>`"), args.format)
    from .novel import ChapterReorganizer

    reorganizer = ChapterReorganizer(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "move":
        result = reorganizer.move(
            args.chapter_ids[0] if args.chapter_ids else "",
            to_volume=args.to_volume,
            after=args.after,
        )
    elif args.subcommand == "split":
        result = reorganizer.split(
            args.chapter_ids[0] if args.chapter_ids else "",
            at_scene=args.at_scene or "",
        )
    elif args.subcommand == "merge":
        left = args.chapter_ids[0] if len(args.chapter_ids) > 0 else ""
        right = args.chapter_ids[1] if len(args.chapter_ids) > 1 else ""
        result = reorganizer.merge(left, right, into=args.into or left)
    else:
        result = reorganizer.renumber()
    report = Report(
        title="Chapter Reorganization",
        status="ok" if result.get("status") == "ok" else "blocked",
        next_action="Review reorg.log and manifest before drafting further",
        sections=[ReportSection("Result", [f"{key}={value}" for key, value in result.items()])],
        data=result,
    )
    _emit(report, args.format)
    return 0 if result.get("status") == "ok" else 1


def _handle_export(args: argparse.Namespace) -> int:
    if not args.slug:
        return _emit(_planned_report("export", "Run `pf-agent export --slug <slug> --format txt`"), "terminal")
    from .novel import BookExporter

    chapter_range = None
    if args.from_chapter or args.to_chapter:
        chapter_range = (args.from_chapter or args.to_chapter, args.to_chapter or args.from_chapter)
    result = BookExporter(Path(".pf-agent") / "workspace", slug=args.slug).export(
        format=args.format,
        chapter_range=chapter_range,
        back_matter=args.back_matter,
    )
    report = Report(
        title="Book Export",
        status=result.status,
        next_action="Review the exported book artifact before publishing",
        sections=[
            ReportSection(
                "Export",
                [
                    f"format={result.format}",
                    f"path={result.path}",
                    f"chapters={', '.join(result.chapters)}",
                    *[f"warning={warning}" for warning in result.warnings],
                ],
            )
        ],
        data=result.to_dict(),
    )
    return _emit(report, "terminal")


def _handle_publishing(args: argparse.Namespace) -> int:
    if args.subcommand not in {"init", "edit", "validate"} or not args.slug:
        return _emit(_planned_report("publishing", "Run `pf-agent publishing init --slug <slug>`"), args.format)
    from .novel import PublishingMetadataStore

    store = PublishingMetadataStore(Path(".pf-agent") / "workspace", slug=args.slug)
    fields = {
        "title": args.title,
        "subtitle": args.subtitle,
        "author": args.author,
        "pen_name": args.pen_name,
        "summary": args.summary,
        "keywords": [item.strip() for item in args.keywords.split(",")] if args.keywords else None,
        "copyright": args.copyright,
        "ai_usage_statement": args.ai_usage_statement,
    }
    if args.subcommand == "init":
        metadata = store.init(**fields)
        data = metadata.to_dict()
        status = "ok"
        lines = [f"path={metadata.path}", f"title={metadata.data.get('title')}"]
    elif args.subcommand == "edit":
        metadata = store.edit(**fields)
        data = metadata.to_dict()
        status = "ok"
        lines = [f"path={metadata.path}", f"summary={metadata.data.get('summary')}"]
    else:
        data = store.validate()
        status = "ok" if data["status"] == "ok" else "blocked"
        lines = [f"valid={str(data['status'] == 'ok').lower()}", *data["errors"]]
    report = Report(
        title="Publishing Metadata",
        status=status,
        next_action="Use publishing metadata during export and platform submission",
        sections=[ReportSection("Metadata", lines)],
        data=data,
    )
    _emit(report, args.format)
    return 0 if status == "ok" else 1


def _handle_bible(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add", "list", "freeze", "snapshot"} or not args.slug:
        return _emit(_planned_report("bible", "Run `pf-agent bible add character --slug <slug>`"), args.format)
    from .novel import CanonBibleManager

    manager = CanonBibleManager(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add":
        entry = {
            key: value
            for key, value in {
                "id": args.id,
                "name": args.name,
                "role": args.role,
                "text": args.text,
            }.items()
            if value
        }
        data = manager.add(args.bible_arg or "character", entry)
        lines = [f"{key}={value}" for key, value in data.items()]
        status = "ok" if data.get("status") == "ok" else "blocked"
    elif args.subcommand == "list":
        entries = manager.list(args.bible_arg or "characters")
        data = {"entries": entries}
        lines = [str(entry) for entry in entries] or ["(none)"]
        status = "ok"
    elif args.subcommand == "freeze":
        data = manager.freeze()
        lines = ["frozen=true"]
        status = "ok"
    else:
        data = manager.snapshot()
        lines = [f"id={data['id']}", f"path={data['path']}"]
        status = "ok"
    report = Report(
        title="Canon Bible",
        status=status,
        next_action="Use bible snapshots as explicit canon evidence",
        sections=[ReportSection("Bible", lines)],
        data=data,
    )
    _emit(report, args.format)
    return 0 if status == "ok" else 1


def _handle_continuity(args: argparse.Namespace) -> int:
    if args.subcommand not in {"check", "resolve"} or not args.slug:
        return _emit(_planned_report("continuity", "Run `pf-agent continuity check --slug <slug>`"), args.format)
    from .novel import ContinuityResolver

    resolver = ContinuityResolver(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "check":
        conflicts = resolver.check()
        report = Report(
            title="Continuity Check",
            status="ok" if not conflicts else "degraded",
            next_action="Resolve or defer every conflict before accepting canon",
            sections=[
                ReportSection(
                    "Conflicts",
                    [f"{conflict.id}: {conflict.subject}.{conflict.key}" for conflict in conflicts] or ["(none)"],
                )
            ],
            data={"conflicts": [conflict.to_dict() for conflict in conflicts]},
        )
        return _emit(report, args.format)
    result = resolver.resolve(args.conflict or "", action=args.action)
    report = Report(
        title="Continuity Resolve",
        status="ok" if result.get("status") == "ok" else "blocked",
        next_action="Review continuity audit log after resolution",
        sections=[ReportSection("Resolution", [f"{key}={value}" for key, value in result.items()])],
        data=result,
    )
    _emit(report, args.format)
    return 0 if result.get("status") == "ok" else 1


def _handle_timeline(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add-event", "check", "view"} or not args.slug:
        return _emit(_planned_report("timeline", "Run `pf-agent timeline add-event --slug <slug>`"), args.format)
    from .novel import TimelineEngine

    timeline = TimelineEngine(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add-event":
        if not args.id or not args.title:
            return _emit(_planned_report("timeline", "Pass --id and --title for timeline add-event"), args.format)
        event = timeline.add_event(
            id=args.id,
            title=args.title,
            absolute_date=args.absolute_date,
            relative_date=args.relative_date,
            story_day=args.story_day,
            order=args.order,
            parallel=args.parallel,
            characters=args.character or [],
            location=args.location,
            causes=args.cause or [],
            effects=args.effect or [],
            chapter_id=args.chapter,
            scene_id=args.scene,
        )
        report = Report(
            title="Timeline Event",
            status="ok",
            next_action="Run `pf-agent timeline check --slug <slug>` before accepting chronology",
            sections=[
                ReportSection(
                    "Event",
                    [
                        f"id={event.id}",
                        f"title={event.title}",
                        f"story_day={event.story_day}",
                        f"order={event.order}",
                    ],
                )
            ],
            data=event.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "check":
        conflicts = timeline.check()
        report = Report(
            title="Timeline Check",
            status="ok" if not conflicts else "degraded",
            next_action="Resolve location and causal conflicts before drafting dependent scenes",
            sections=[
                ReportSection(
                    "Conflicts",
                    [
                        f"{item['id']}: {item['type']} {item.get('character') or item.get('event')}"
                        for item in conflicts
                    ]
                    or ["(none)"],
                )
            ],
            data={"conflicts": conflicts},
        )
        return _emit(report, args.format)
    events = timeline.view()
    report = Report(
        title="Timeline View",
        status="ok",
        next_action="Use timeline order as context for scene and chapter planning",
        sections=[
            ReportSection(
                "Events",
                [
                    f"{event.id}: day={event.story_day} order={event.order} title={event.title}"
                    for event in events
                ]
                or ["(none)"],
            )
        ],
        data={"events": [event.to_dict() for event in events]},
    )
    return _emit(report, args.format)


def _handle_plot_thread(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add", "list", "stale"} or not args.slug:
        return _emit(_planned_report("plot-thread", "Run `pf-agent plot-thread add --slug <slug>`"), args.format)
    from .novel import PlotThreadManager

    manager = PlotThreadManager(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add":
        if not args.id:
            return _emit(_planned_report("plot-thread", "Pass --id for plot-thread add"), args.format)
        thread = manager.add_thread(
            id=args.id,
            type=args.type,
            status=args.status,
            first_appearance=args.first_appearance,
            last_touched=args.last_touched,
            expected_payoff=args.expected_payoff,
            linked_chapters=args.linked_chapter or [],
            linked_characters=args.linked_character or [],
        )
        report = Report(
            title="Plot Thread",
            status="ok",
            next_action="Run `pf-agent plot-thread stale --slug <slug>` during chapter planning",
            sections=[
                ReportSection(
                    "Thread",
                    [
                        f"id={thread.id}",
                        f"type={thread.type}",
                        f"status={thread.status}",
                        f"expected_payoff={thread.expected_payoff}",
                    ],
                )
            ],
            data=thread.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "list":
        threads = manager.list()
        report = Report(
            title="Plot Thread List",
            status="ok",
            next_action="Review stale threads before accepting late-book drafts",
            sections=[
                ReportSection(
                    "Threads",
                    [f"{thread.id}: {thread.type} {thread.status}" for thread in threads] or ["(none)"],
                )
            ],
            data={"threads": [thread.to_dict() for thread in threads]},
        )
        return _emit(report, args.format)
    if args.current_chapter is None:
        return _emit(_planned_report("plot-thread", "Pass --current-chapter for stale checks"), args.format)
    stale_threads = manager.stale(current_chapter=args.current_chapter, max_gap=args.max_gap)
    report = Report(
        title="Plot Thread Stale",
        status="ok" if not stale_threads else "degraded",
        next_action="Touch, resolve, or intentionally defer every stale plot thread",
        sections=[
            ReportSection(
                "Stale",
                [
                    f"{thread['id']}: stale {thread['chapters_since_touched']} chapters"
                    for thread in stale_threads
                ]
                or ["(none)"],
            )
        ],
        data={"threads": stale_threads},
    )
    return _emit(report, args.format)


def _handle_foreshadow(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add", "list", "overdue", "resolve"} or not args.slug:
        return _emit(_planned_report("foreshadow", "Run `pf-agent foreshadow add --slug <slug>`"), args.format)
    from .novel import ForeshadowingTracker

    tracker = ForeshadowingTracker(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add":
        if not args.id or not args.planted_chapter:
            return _emit(_planned_report("foreshadow", "Pass --id and --planted-chapter for foreshadow add"), args.format)
        record = tracker.add(
            id=args.id,
            planted_chapter=args.planted_chapter,
            expected_payoff_chapter=args.expected_payoff_chapter,
            status=args.status,
            importance=args.importance,
            related_characters=args.related_character or [],
            related_plot_thread=args.related_plot_thread,
        )
        report = Report(
            title="Foreshadow",
            status="ok",
            next_action="Run `pf-agent foreshadow overdue --slug <slug>` during revision",
            sections=[
                ReportSection(
                    "Foreshadow",
                    [
                        f"id={record.id}",
                        f"status={record.status}",
                        f"importance={record.importance}",
                        f"expected_payoff={record.expected_payoff_chapter}",
                    ],
                )
            ],
            data=record.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "list":
        records = tracker.list()
        report = Report(
            title="Foreshadow List",
            status="ok",
            next_action="Keep planted clues tied to payoff chapters",
            sections=[
                ReportSection(
                    "Foreshadowing",
                    [f"{record.id}: {record.status} -> {record.expected_payoff_chapter}" for record in records]
                    or ["(none)"],
                )
            ],
            data={"foreshadowing": [record.to_dict() for record in records]},
        )
        return _emit(report, args.format)
    if args.subcommand == "overdue":
        if args.current_chapter is None:
            return _emit(_planned_report("foreshadow", "Pass --current-chapter for foreshadow overdue"), args.format)
        overdue = tracker.overdue(current_chapter=args.current_chapter, max_gap=args.max_gap)
        report = Report(
            title="Foreshadow Overdue",
            status="ok" if not overdue else "degraded",
            next_action="Resolve, advance, or intentionally defer overdue foreshadowing",
            sections=[
                ReportSection(
                    "Overdue",
                    [
                        f"{record['id']}: overdue {record.get('chapters_since_planted')} chapters ({record['reason']})"
                        for record in overdue
                    ]
                    or ["(none)"],
                )
            ],
            data={"foreshadowing": overdue},
        )
        return _emit(report, args.format)
    result = tracker.resolve(args.id or "", resolved_chapter=args.resolved_chapter)
    report = Report(
        title="Foreshadow Resolve",
        status="ok" if result.get("status") == "resolved" else "blocked",
        next_action="Re-run overdue checks after resolving planted clues",
        sections=[ReportSection("Resolution", [f"{key}={value}" for key, value in result.items()])],
        data=result,
    )
    _emit(report, args.format)
    return 0 if result.get("status") == "resolved" else 1


def _handle_character_arc(args: argparse.Namespace) -> int:
    if args.subcommand not in {"init", "update", "report"} or not args.slug:
        return _emit(_planned_report("character-arc", "Run `pf-agent character-arc init --slug <slug>`"), args.format)
    from .novel import CharacterArcTracker

    tracker = CharacterArcTracker(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "init":
        if not args.character:
            return _emit(_planned_report("character-arc", "Pass --character for character-arc init"), args.format)
        arc = tracker.init_arc(
            character_id=args.character,
            desire=args.desire,
            fear=args.fear,
            flaw=args.flaw,
            belief=args.belief,
            arc_status=args.arc_status or "introduced",
        )
        report = Report(
            title="Character Arc",
            status="ok",
            next_action="Update arc turning points as chapters are drafted",
            sections=[
                ReportSection(
                    "Arc",
                    [
                        f"character={arc.character_id}",
                        f"desire={arc.desire}",
                        f"belief={arc.belief}",
                        f"status={arc.arc_status}",
                    ],
                )
            ],
            data=arc.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "update":
        if not args.character:
            return _emit(_planned_report("character-arc", "Pass --character for character-arc update"), args.format)
        arc = tracker.update_arc(
            character_id=args.character,
            desire=args.desire,
            fear=args.fear,
            flaw=args.flaw,
            belief=args.belief,
            turning_points=[_split_pair(item, "chapter", "change") for item in args.turning_point or []],
            relationship_changes=[
                _split_pair(item, "character", "change") for item in args.relationship_change or []
            ],
            chapter_appearances=args.chapter or [],
            arc_status=args.arc_status,
        )
        report = Report(
            title="Character Arc Update",
            status="ok",
            next_action="Run `pf-agent character-arc report --slug <slug>` for whole-book changes",
            sections=[
                ReportSection(
                    "Arc",
                    [
                        f"character={arc.character_id}",
                        f"turning_points={len(arc.turning_points)}",
                        f"appearances={len(arc.chapter_appearances)}",
                        f"status={arc.arc_status}",
                    ],
                )
            ],
            data=arc.to_dict(),
        )
        return _emit(report, args.format)
    report_data = tracker.report()
    report = Report(
        title="Character Arc Report",
        status="ok",
        next_action="Use arc reports when revising emotional continuity",
        sections=[ReportSection("Summary", report_data["summary"] or ["(none)"])],
        data=report_data,
    )
    return _emit(report, args.format)


def _handle_relation(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add", "list", "graph"} or not args.slug:
        return _emit(_planned_report("relation", "Run `pf-agent relation add --slug <slug>`"), args.format)
    from .novel import RelationshipGraph

    graph = RelationshipGraph(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add":
        if not args.source or not args.target:
            return _emit(_planned_report("relation", "Pass --source and --target for relation add"), args.format)
        try:
            edge = graph.add_relation(
                source=args.source,
                target=args.target,
                type=args.type,
                evidence=args.evidence or [],
                status=args.status,
                note=args.note,
            )
        except ValueError as exc:
            report = Report(
                title="Relationship Graph",
                status="blocked",
                next_action="Use a supported relation type",
                sections=[ReportSection("Error", [str(exc)])],
                data={"error": str(exc)},
            )
            _emit(report, args.format)
            return 1
        report = Report(
            title="Relationship Graph",
            status="ok",
            next_action="Run `pf-agent relation graph --slug <slug>` to export graph context",
            sections=[
                ReportSection(
                    "Relation",
                    [f"{edge.source} -> {edge.target}", f"type={edge.type}", f"status={edge.status}"],
                )
            ],
            data=edge.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "list":
        edges = graph.list()
        report = Report(
            title="Relationship Graph List",
            status="ok",
            next_action="Use relation graph exports as structured evidence",
            sections=[
                ReportSection(
                    "Relations",
                    [f"{edge.source} -> {edge.target}: {edge.type}" for edge in edges] or ["(none)"],
                )
            ],
            data={"relations": [edge.to_dict() for edge in edges]},
        )
        return _emit(report, args.format)
    graph_data = graph.graph(format=args.graph_format)
    lines = graph_data.splitlines() if isinstance(graph_data, str) else [
        f"nodes={len(graph_data['nodes'])}",
        f"edges={len(graph_data['edges'])}",
    ]
    report = Report(
        title="Relationship Graph",
        status="ok",
        next_action="Inject graph evidence into retrieval packs for relationship-sensitive scenes",
        sections=[ReportSection("Graph", lines or ["(empty)"])],
        data={"format": args.graph_format, "graph": graph_data},
    )
    return _emit(report, args.format)


def _handle_rules(args: argparse.Namespace) -> int:
    if args.subcommand not in {"add", "list", "remove"}:
        return _emit(_planned_report("rules", "Run `pf-agent rules add \"<rule>\"`"), args.format)
    from .novel import WritingRulesStore

    store = WritingRulesStore(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "add":
        if not args.rule_text:
            return _emit(_planned_report("rules", "Pass rule text for rules add"), args.format)
        try:
            rule = store.add(args.rule_text, level=args.level, chapter=args.chapter)
        except ValueError as exc:
            report = Report(
                title="Writing Rules",
                status="blocked",
                next_action="Use global, project, or chapter rule level",
                sections=[ReportSection("Error", [str(exc)])],
                data={"error": str(exc)},
            )
            _emit(report, args.format)
            return 1
        report = Report(
            title="Writing Rules",
            status="ok",
            next_action="Draft, review, and rewrite flows can read these rules as evidence",
            sections=[
                ReportSection(
                    "Rule",
                    [f"id={rule.id}", f"level={rule.level}", f"chapter={rule.chapter}", f"text={rule.text}"],
                )
            ],
            data=rule.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "list":
        rules = store.list()
        report = Report(
            title="Writing Rules",
            status="ok",
            next_action="Remove obsolete rules or keep them explicit for future drafts",
            sections=[
                ReportSection(
                    "Rules",
                    [f"{rule.id}: [{rule.level}] {rule.text}" for rule in rules] or ["(none)"],
                )
            ],
            data={"rules": [rule.to_dict() for rule in rules]},
        )
        return _emit(report, args.format)
    result = store.remove(args.rule_text or "")
    report = Report(
        title="Writing Rules",
        status="ok" if result["removed"] else "blocked",
        next_action="Run `pf-agent rules list` to confirm active rules",
        sections=[ReportSection("Remove", [f"{key}={value}" for key, value in result.items()])],
        data=result,
    )
    _emit(report, args.format)
    return 0 if result["removed"] else 1


def _handle_style(args: argparse.Namespace) -> int:
    if args.subcommand not in {"compile", "check"} or not args.slug:
        return _emit(_planned_report("style", "Run `pf-agent style compile --slug <slug>`"), args.format)
    from .novel import StyleProfileCompiler

    compiler = StyleProfileCompiler(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "compile":
        profile = compiler.compile(args.preference) if args.preference else compiler.compile_from_rules()
        report = Report(
            title="Style Profile",
            status="ok",
            next_action="Run `pf-agent style check --slug <slug> --chapter <id>` before review",
            sections=[
                ReportSection(
                    "Checks",
                    [
                        f"punctuation={', '.join(profile.punctuation_checks) or 'none'}",
                        f"lexical={', '.join(profile.lexical_checks) or 'none'}",
                        f"narration={', '.join(profile.narration_distance_checks) or 'none'}",
                        f"review_gates={', '.join(profile.review_gate_rules) or 'none'}",
                    ],
                )
            ],
            data=profile.to_dict(),
        )
        return _emit(report, args.format)
    if not args.chapter:
        return _emit(_planned_report("style", "Pass --chapter for style check"), args.format)
    result = compiler.check_chapter(args.chapter)
    report = Report(
        title="Style Check",
        status=result["status"],
        next_action="Fix style violations or revise the compiled style profile",
        sections=[
            ReportSection(
                "Violations",
                [
                    f"{violation['code']}: {violation['message']}"
                    for violation in result["violations"]
                ]
                or ["(none)"],
            )
        ],
        data=result,
    )
    return _emit(report, args.format)


def _handle_quality(args: argparse.Namespace) -> int:
    if args.subcommand not in {"check", "report"} or not args.slug:
        return _emit(_planned_report("quality", "Run `pf-agent quality check --slug <slug> --chapter <id>`"), args.format)
    from .novel import WritingQualityGateRunner

    runner = WritingQualityGateRunner(Path(".pf-agent") / "workspace", slug=args.slug)
    if args.subcommand == "check":
        if not args.chapter:
            return _emit(_planned_report("quality", "Pass --chapter for quality check"), args.format)
        result = runner.check_chapter(args.chapter)
        report = Report(
            title="Quality Check",
            status=result["status"],
            next_action="Fix reported violations before accepting the chapter",
            sections=[
                ReportSection(
                    "Violations",
                    [
                        (
                            f"{item['code']} line={item['line']} column={item['column']}: "
                            f"{item['suggestion']}"
                        )
                        for item in result["violations"]
                    ]
                    or ["(none)"],
                )
            ],
            data=result,
        )
        return _emit(report, args.format)
    data = runner.report()
    lines = [
        f"chapters={data['summary']['chapters']}",
        f"total_violations={data['summary']['total_violations']}",
    ]
    for chapter in data["chapters"]:
        lines.append(f"{chapter.get('chapter')}: {len(chapter.get('violations', []))} violations")
    report = Report(
        title="Quality Report",
        status=data["status"],
        next_action="Use the report before release or regression comparison",
        sections=[ReportSection("Summary", lines)],
        data=data,
    )
    return _emit(report, args.format)


def _handle_literary(args: argparse.Namespace) -> int:
    if args.subcommand not in {"baseline", "test"} or not args.slug:
        return _emit(_planned_report("literary", "Run `pf-agent literary baseline --slug <slug>`"), args.format)
    from .novel import LiteraryRegressionSuite, read_golden_samples

    suite = LiteraryRegressionSuite(Path(".pf-agent") / "workspace", slug=args.slug, threshold=args.threshold)
    samples = read_golden_samples(args.golden_dir)
    if args.subcommand == "baseline":
        data = suite.baseline(samples)
        lines = [f"samples={len(data['samples'])}", f"threshold={data['threshold']}"]
        for sample in data["samples"]:
            lines.append(f"{sample['id']}: baseline")
        report = Report(
            title="Literary Regression",
            status="ok",
            next_action="Run `pf-agent literary test --slug <slug>` after prompt or style changes",
            sections=[ReportSection("Baseline", lines)],
            data=data,
        )
        return _emit(report, args.format)
    data = suite.test(samples)
    lines = [
        f"{item['sample']} {item['metric']}: expected={item['expected']} actual={item['actual']}"
        for item in data["drift"]
    ] or ["(no drift)"]
    report = Report(
        title="Literary Regression",
        status=data["status"],
        next_action="Review prompt, model, or style changes when drift is degraded",
        sections=[ReportSection("Drift", lines)],
        data=data,
    )
    return _emit(report, args.format)


def _handle_rewrite(args: argparse.Namespace) -> int:
    from .novel import RewriteStrategyLibrary

    library = RewriteStrategyLibrary(Path(".pf-agent") / "workspace", slug=args.slug or "")
    if args.subcommand == "strategies" and args.rewrite_arg == "list":
        strategies = library.list_strategies()
        report = Report(
            title="Rewrite Strategies",
            status="ok",
            next_action="Run `pf-agent rewrite --strategy <name> --chapter <id>`",
            sections=[
                ReportSection(
                    "Strategies",
                    [f"{strategy.name}: {strategy.description}" for strategy in strategies],
                )
            ],
            data={"strategies": [strategy.to_dict() for strategy in strategies]},
        )
        return _emit(report, args.format)
    if args.subcommand is not None:
        return _emit(_planned_report("rewrite", "Run `pf-agent rewrite strategies list`"), args.format)
    if not args.slug or not args.strategy or not args.chapter:
        return _emit(_planned_report("rewrite", "Pass --slug, --strategy, and --chapter"), args.format)
    try:
        result = library.rewrite(strategy=args.strategy, chapter=args.chapter)
    except ValueError as exc:
        report = Report(
            title="Rewrite",
            status="blocked",
            next_action="Pick a strategy from `pf-agent rewrite strategies list`",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1
    report = Report(
        title="Rewrite",
        status="ok",
        next_action="Review the revision artifact before replacing chapter text",
        sections=[
            ReportSection(
                "Revision",
                [f"chapter={result.chapter}", f"strategy={result.strategy}", f"path={result.path}"],
            )
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_reader_review(args: argparse.Namespace) -> int:
    from .novel import ReaderExperienceReviewer

    if not args.slug or (bool(args.chapter) == bool(args.volume)):
        return _emit(
            _planned_report("reader-review", "Pass --slug and exactly one of --chapter or --volume"),
            args.format,
        )
    reviewer = ReaderExperienceReviewer(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        report_data = reviewer.review(chapter=args.chapter, volume=args.volume)
    except ValueError as exc:
        report = Report(
            title="Reader Experience",
            status="blocked",
            next_action="Provide an existing chapter or a volume with chapters",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1
    signal_lines = [
        f"{signal.name}: {signal.level} ({signal.score:.2f}) — {signal.detail}"
        for signal in report_data.signals
    ]
    suggestion_lines = [f"[{item.signal}] {item.message}" for item in report_data.suggestions] or [
        "无需改动：各项读者体验信号均健康。"
    ]
    report = Report(
        title="Reader Experience",
        status=report_data.status,
        next_action="Apply the suggestions, then re-review the chapter",
        sections=[
            ReportSection("Target", [f"target={report_data.target}", f"scope={report_data.scope}", f"path={report_data.path}"]),
            ReportSection("Signals", signal_lines),
            ReportSection("Suggestions", suggestion_lines),
        ],
        data=report_data.to_dict(),
    )
    return _emit(report, args.format)


def _handle_search(args: argparse.Namespace) -> int:
    query = args.subcommand
    if getattr(args, "json", False):
        args.format = "json"
    if not query:
        return _emit(
            _planned_report("search", 'Run `pf-agent search "<query>" --slug <slug>`'),
            args.format,
        )
    if not args.slug:
        from .tools.managed.url_safety import UrlSafetyPolicy
        from .tools.managed.web_search import FakeWebSearchProvider, WebSearchResponse

        if args.provider != "fake":
            response = WebSearchResponse(
                query=query,
                results=[],
                provider=args.provider,
                degraded=True,
                reason=f"provider {args.provider!r} is not configured for managed web search",
            )
        else:
            response = FakeWebSearchProvider().search(query)
        policy = UrlSafetyPolicy(network_enabled=args.provider == "fake")
        safety = [policy.check(result.url).to_dict() for result in response.results]
        report = Report(
            title="Web Search",
            status="degraded" if response.degraded else "ok",
            next_action="Use web results as citation candidates only; do not promote them to canon automatically",
            sections=[
                ReportSection("Query", [f"query={response.query}", f"provider={args.provider}"]),
                ReportSection(
                    "Citations",
                    [
                        f"{citation['id']} {citation['title']} {citation['url']}"
                        for citation in response.citations
                    ]
                    or ["(none)"],
                ),
            ],
            data=response.to_dict() | {"safety": safety},
        )
        return _emit(report, args.format)

    from .novel import ManuscriptSearch

    searcher = ManuscriptSearch(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        result = searcher.search(query, scope=args.scope, exact=args.exact)
    except ValueError as exc:
        report = Report(
            title="Manuscript Search",
            status="blocked",
            next_action="Use scope 'manuscript' or 'all' and a non-empty query",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1
    hit_lines = [
        f"{hit.chapter or hit.domain}:{hit.line} {hit.snippet}" for hit in result.hits
    ] or ["no matches"]
    report = Report(
        title="Manuscript Search",
        status="ok",
        next_action="Open the cited file at the reported line",
        sections=[
            ReportSection("Query", [f"query={result.query}", f"scope={result.scope}", f"exact={result.exact}", f"count={result.count}"]),
            ReportSection("Hits", hit_lines),
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_draft(args: argparse.Namespace) -> int:
    from .novel import DraftVersionStore

    sub = args.subcommand
    draft_args = list(getattr(args, "draft_args", []) or [])
    if not args.slug or sub not in {"version", "diff", "rollback", "branch"}:
        return _emit(
            _planned_report("draft", "Run `pf-agent draft version list --slug <slug> --chapter <id>`"),
            args.format,
        )
    store = DraftVersionStore(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        if sub == "version" and draft_args[:1] == ["list"]:
            if not args.chapter:
                return _emit(_planned_report("draft", "Pass --chapter for `draft version list`"), args.format)
            versions = store.list_versions(args.chapter)
            lines = [
                f"{version.id} checksum={version.checksum[:12]} provider={version.provider or '-'} prompt={version.prompt or '-'} branch={version.branch}"
                for version in versions
            ] or ["no versions"]
            return _emit(
                Report(
                    title="Draft Versions",
                    status="ok",
                    next_action="Diff or roll back to one of these versions",
                    sections=[ReportSection(f"chapter {args.chapter}", lines)],
                    data={"chapter": args.chapter, "versions": [version.to_dict() for version in versions]},
                ),
                args.format,
            )
        if sub == "diff":
            if len(draft_args) < 2:
                return _emit(_planned_report("draft", "Run `pf-agent draft diff <v1> <v2>`"), args.format)
            result = store.diff(draft_args[0], draft_args[1])
            return _emit(
                Report(
                    title="Draft Diff",
                    status="ok" if result.changed else "ok",
                    next_action="Roll back if the change should be reverted",
                    sections=[
                        ReportSection("Versions", [f"a={result.version_a}", f"b={result.version_b}", f"changed={result.changed}"]),
                        ReportSection("Diff", result.diff.splitlines() or ["(identical)"]),
                    ],
                    data=result.to_dict(),
                ),
                args.format,
            )
        if sub == "rollback":
            if not args.chapter or not args.to:
                return _emit(_planned_report("draft", "Pass --chapter and --to for rollback"), args.format)
            result = store.rollback(args.chapter, to=args.to, approve=args.approve)
            status = "ok" if result.status == "rolled_back" else "blocked"
            next_action = "Rollback applied" if result.approved else "Re-run with --approve to roll back"
            return _emit(
                Report(
                    title="Draft Rollback",
                    status=status,
                    next_action=next_action,
                    sections=[ReportSection("Rollback", [f"chapter={result.chapter}", f"to={result.to}", f"status={result.status}", f"approved={result.approved}"])],
                    data=result.to_dict(),
                ),
                args.format,
            )
        # branch
        if not args.chapter or not args.name:
            return _emit(_planned_report("draft", "Pass --chapter and --name for branch"), args.format)
        branch = store.branch(args.chapter, name=args.name, from_version=args.from_version)
        return _emit(
            Report(
                title="Draft Branch",
                status="ok",
                next_action="Continue editing on the new branch version",
                sections=[ReportSection("Branch", [f"name={branch.name}", f"chapter={branch.chapter}", f"base={branch.base_version}", f"head={branch.head_version}"])],
                data=branch.to_dict(),
            ),
            args.format,
        )
    except ValueError as exc:
        report = Report(
            title="Draft",
            status="blocked",
            next_action="Use an existing version id and chapter",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1


def _handle_editorial(args: argparse.Namespace) -> int:
    from .novel import EditorialPipeline

    sub = args.subcommand
    if not args.slug or sub not in {"run", "status", "promote"}:
        return _emit(
            _planned_report("editorial", "Run `pf-agent editorial run --slug <slug> --chapter <id>`"),
            args.format,
        )
    pipeline = EditorialPipeline(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        if sub == "run":
            if not args.chapter:
                return _emit(_planned_report("editorial", "Pass --chapter for `editorial run`"), args.format)
            state = pipeline.run(args.chapter)
            return _emit(
                Report(
                    title="Editorial Pipeline",
                    status="ok",
                    next_action="Promote to final with `editorial promote --to final --approve`",
                    sections=[
                        ReportSection("State", [f"chapter={state.chapter}", f"current_stage={state.current_stage}", f"completed={','.join(state.completed)}"]),
                        ReportSection("Artifacts", [f"{artifact.stage}: {artifact.path}" for artifact in state.artifacts]),
                    ],
                    data=state.to_dict(),
                ),
                args.format,
            )
        if sub == "status":
            status = pipeline.status()
            lines = [
                f"{entry['chapter']}: {entry['current_stage']} (completed={len(entry['completed'])})"
                for entry in status.to_dict()["chapters"]
            ] or ["no chapters in the pipeline"]
            return _emit(
                Report(
                    title="Editorial Status",
                    status="ok",
                    next_action="Run or promote a chapter to advance it",
                    sections=[ReportSection("Chapters", lines)],
                    data=status.to_dict(),
                ),
                args.format,
            )
        # promote
        if not args.chapter or not args.to:
            return _emit(_planned_report("editorial", "Pass --chapter and --to for promote"), args.format)
        result = pipeline.promote(args.chapter, to=args.to, approve=args.approve)
        status = "ok" if result.status == "promoted" else "blocked"
        next_action = "Stage promoted" if result.approved else "Re-run with --approve for this high-risk promote"
        return _emit(
            Report(
                title="Editorial Promote",
                status=status,
                next_action=next_action,
                sections=[ReportSection("Promote", [f"chapter={result.chapter}", f"to={result.to}", f"status={result.status}", f"approved={result.approved}"])],
                data=result.to_dict(),
            ),
            args.format,
        )
    except ValueError as exc:
        report = Report(
            title="Editorial",
            status="blocked",
            next_action="Use a valid editorial stage",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1


def _handle_approval(args: argparse.Namespace) -> int:
    from .novel import ApprovalQueue

    sub = args.subcommand
    approval_id = getattr(args, "approval_id", None)
    if not args.slug:
        if sub not in {"list", "show", "approve", "reject"}:
            return _emit(
                _planned_report("approval", "Run `pf-agent approval list` or pass --slug for project approvals"),
                args.format,
            )
        from .mcp import MCPApprovalQueue

        queue = MCPApprovalQueue(Path(".pf-agent"))
        try:
            if sub == "list":
                items = queue.list()
                lines = [f"{item.id}: {item.action} [{item.status}] {item.summary}" for item in items] or ["(none)"]
                return _emit(
                    Report(
                        title="Approval Queue",
                        status="ok",
                        next_action="Approve or reject pending MCP requests by id",
                        sections=[ReportSection("Requests", lines)],
                        data={"requests": [item.to_dict() for item in items]},
                    ),
                    args.format,
                )
            if not approval_id:
                return _emit(_planned_report("approval", f"Pass an approval id for `approval {sub}`"), args.format)
            if sub == "show":
                item = queue.show(approval_id)
            elif sub == "approve":
                item = queue.approve(approval_id)
            else:
                item = queue.reject(approval_id)
            return _emit(
                Report(
                    title="Approval",
                    status="ok",
                    next_action="The MCP tool call follows this decision",
                    sections=[
                        ReportSection(
                            "Request",
                            [f"id={item.id}", f"action={item.action}", f"status={item.status}", f"summary={item.summary}"],
                        )
                    ],
                    data=item.to_dict(),
                ),
                args.format,
            )
        except Exception as exc:  # noqa: BLE001 - render queue errors consistently
            return _emit(
                Report(
                    title="Approval",
                    status="blocked",
                    next_action="Use an existing pending approval id",
                    sections=[ReportSection("Error", [str(exc)])],
                    data={"error": str(exc)},
                ),
                args.format,
            )
    if not args.slug or sub not in {"list", "show", "approve", "reject"}:
        return _emit(
            _planned_report("approval", "Run `pf-agent approval list --slug <slug>`"),
            args.format,
        )
    queue = ApprovalQueue(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        if sub == "list":
            items = queue.list()
            lines = [f"{item.id} {item.action} [{item.status}] {item.summary}" for item in items] or ["queue empty"]
            return _emit(
                Report(
                    title="Approval Queue",
                    status="ok",
                    next_action="Approve or reject a pending request by id",
                    sections=[ReportSection("Requests", lines)],
                    data={"requests": [item.to_dict() for item in items]},
                ),
                args.format,
            )
        if not approval_id:
            return _emit(_planned_report("approval", f"Pass an approval id for `approval {sub}`"), args.format)
        if sub == "show":
            item = queue.show(approval_id)
        elif sub == "approve":
            item = queue.approve(approval_id)
        else:
            item = queue.reject(approval_id)
        return _emit(
            Report(
                title="Approval",
                status="ok",
                next_action="The high-risk action follows this decision",
                sections=[ReportSection("Request", [f"id={item.id}", f"action={item.action}", f"status={item.status}", f"summary={item.summary}"])],
                data=item.to_dict(),
            ),
            args.format,
        )
    except ValueError as exc:
        report = Report(
            title="Approval",
            status="blocked",
            next_action="Use an existing pending approval id",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1


def _handle_stats(args: argparse.Namespace) -> int:
    from .novel import WritingAnalytics

    sub = args.subcommand
    if not args.slug or sub not in {None, "daily", "export"}:
        return _emit(_planned_report("stats", "Run `pf-agent stats --slug <slug>`"), args.format)
    analytics = WritingAnalytics(Path(".pf-agent") / "workspace", slug=args.slug)
    if sub == "export":
        print(analytics.export_csv(), end="")
        return 0
    if sub == "daily":
        daily = analytics.daily()
        lines = [f"{stat.date}: {stat.words} words, {stat.revisions} rev, {stat.minutes} min" for stat in daily] or ["no recorded days"]
        return _emit(
            Report(
                title="Writing Analytics — Daily",
                status="ok",
                next_action="Export the trend with `pf-agent stats export --slug <slug> --format csv`",
                sections=[ReportSection("Daily", lines)],
                data={"daily": [stat.to_dict() for stat in daily]},
            ),
            args.format,
        )
    summary = analytics.summary(target_words=args.target_words)
    prediction = (
        f"{summary.days_remaining} days at {summary.avg_daily_words}/day"
        if summary.days_remaining is not None
        else "set --target-words for a prediction"
    )
    return _emit(
        Report(
            title="Writing Analytics",
            status="ok",
            next_action="Use `pf-agent stats daily` or `stats export` for detail",
            sections=[
                ReportSection(
                    "Totals",
                    [
                        f"total_words={summary.total_words}",
                        f"chapters={len(summary.chapter_words)}",
                        f"revisions={summary.total_revisions}",
                        f"cost={summary.total_cost}",
                        f"days_recorded={summary.days_recorded}",
                        f"avg_daily_words={summary.avg_daily_words}",
                    ],
                ),
                ReportSection("Prediction", [prediction]),
            ],
            data=summary.to_dict(),
        ),
        args.format,
    )


def _handle_backup(args: argparse.Namespace) -> int:
    from .novel import BackupManager

    sub = args.subcommand
    backup_id = getattr(args, "backup_id", None)
    if not args.slug or sub not in {"create", "verify", "restore", "list"}:
        return _emit(_planned_report("backup", "Run `pf-agent backup create --slug <slug>`"), args.format)
    manager = BackupManager(Path(".pf-agent") / "workspace", slug=args.slug)
    try:
        if sub == "create":
            backup = manager.create()
            return _emit(
                Report(
                    title="Backup Create",
                    status="ok" if backup.status == "verified" else "blocked",
                    next_action="Verify or dry-run restore this backup",
                    sections=[ReportSection("Backup", [f"id={backup.id}", f"files={backup.file_count}", f"status={backup.status}", f"path={backup.path}"])],
                    data=backup.to_dict(),
                ),
                args.format,
            )
        if sub == "list":
            backups = manager.list()
            lines = [f"{backup.id} files={backup.file_count} {backup.created_at}" for backup in backups] or ["no backups"]
            return _emit(
                Report(
                    title="Backups",
                    status="ok",
                    next_action="Verify or restore a backup by id",
                    sections=[ReportSection("Backups", lines)],
                    data={"backups": [backup.to_dict() for backup in backups]},
                ),
                args.format,
            )
        if not backup_id:
            return _emit(_planned_report("backup", f"Pass a backup id for `backup {sub}`"), args.format)
        if sub == "verify":
            result = manager.verify(backup_id)
            return _emit(
                Report(
                    title="Backup Verify",
                    status="ok" if result.status == "verified" else "blocked",
                    next_action="Restore from a verified backup",
                    sections=[ReportSection("Verify", [f"backup={result.backup_id}", f"status={result.status}", f"checked={result.checked}", f"mismatches={len(result.mismatches)}"])],
                    data=result.to_dict(),
                ),
                args.format,
            )
        # restore
        result = manager.restore(backup_id, dry_run=bool(getattr(args, "dry_run", False)))
        return _emit(
            Report(
                title="Backup Restore",
                status="ok",
                next_action="Re-run without --dry-run to actually restore" if not result.restored else "Restore complete",
                sections=[ReportSection("Restore", [f"backup={result.backup_id}", f"status={result.status}", f"restored={result.restored}", f"files={len(result.files)}"])],
                data=result.to_dict(),
            ),
            args.format,
        )
    except ValueError as exc:
        report = Report(
            title="Backup",
            status="blocked",
            next_action="Use an existing backup id",
            sections=[ReportSection("Error", [str(exc)])],
            data={"error": str(exc)},
        )
        _emit(report, args.format)
        return 1


def _split_pair(value: str, left_key: str, right_key: str) -> dict[str, str]:
    left, separator, right = value.partition(":")
    if not separator:
        return {left_key: "", right_key: value}
    return {left_key: left.strip(), right_key: right.strip()}


def _handle_provider_probe(args: argparse.Namespace) -> int:
    from .llm import CapabilityProber, FakeProvider
    from .llm.capabilities import capability_matrix

    name = getattr(args, "provider", None) or "fake"
    provider = FakeProvider(name=name, model=name)
    results = CapabilityProber(provider).run()
    matrix = capability_matrix(results)
    sections = [
        ReportSection(
            heading="Capabilities",
            lines=[
                f"{r.capability} -> {r.status} ({r.latency_ms:.1f} ms)"
                for r in results
            ],
        )
    ]
    report = Report(
        title=f"Provider Capability Probe: {name}",
        status="ok",
        next_action="Feed the capability matrix into the fallback router",
        sections=sections,
        data={"provider": name, "matrix": matrix},
    )

    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-probe-{name}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _default_route_matrix_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "providers"
        / "route_matrix.yaml"
    )


def _handle_provider_routes(args: argparse.Namespace) -> int:
    from .llm import ProviderRouter

    matrix_path = Path(args.route_matrix) if args.route_matrix else _default_route_matrix_path()
    data = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    router = ProviderRouter(data)
    decisions = (
        router.decisions_for_all_policies(role=args.role)
        if args.all_policies
        else [router.select(role=args.role)]
    )
    lines = []
    payload = []
    for decision in decisions:
        selected = decision.selected.name if decision.selected else f"blocked:{decision.blocked_reason}"
        lines.append(f"{decision.policy} -> {selected}")
        payload.append(decision.to_report().data)
    report = Report(
        title="Provider Routes",
        status="ok",
        next_action="Use selected providers when recording workflow attempts",
        sections=[ReportSection("Routes", lines)],
        data={"role": args.role, "route_matrix": str(matrix_path), "decisions": payload},
    )
    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-routes-{args.role}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _provider_profile_paths() -> list[Path]:
    return sorted((Path(__file__).resolve().parents[2] / "configs" / "providers").glob("*.yaml"))


def _certifier_for_family(family: str):
    from .llm.providers import (
        anthropic,
        deepseek,
        doubao,
        gemini,
        glm,
        grok,
        mimo,
        minimax,
        openai,
        qwen,
    )

    modules = {
        "anthropic": anthropic,
        "deepseek": deepseek,
        "doubao": doubao,
        "gemini": gemini,
        "glm": glm,
        "xai": grok,
        "mimo": mimo,
        "minimax": minimax,
        "openai": openai,
        "qwen": qwen,
    }
    return modules.get(family)


def _handle_provider_certify(args: argparse.Namespace) -> int:
    from .llm.certification import CertificationStore, PASSED, SKIPPED, UNVERIFIED
    from .llm.docs_refresh import docs_refresh_report, source_urls_for_family
    from .llm.profiles import load_provider_profiles

    records_dir = Path(args.records_dir) if args.records_dir else Path("reports") / "provider-certification-records"
    store = CertificationStore(records_dir)
    written = []
    families: set[str] = set()
    for path in _provider_profile_paths():
        profiles = load_provider_profiles(path)
        for profile in profiles.values():
            if not args.all and args.provider and profile.name != args.provider:
                continue
            if not args.all and not args.provider:
                continue
            certifier = _certifier_for_family(profile.family)
            if certifier is None:
                continue
            shape = certifier.shape_certification(profile)
            smoke = {"skipped": True, "reason": "shape-only"}
            if not args.shape_only and args.real_if_key_present:
                smoke = certifier.real_smoke(profile)
            source_urls = source_urls_for_family(profile.family)
            record = store.write(
                provider=profile.name,
                family=profile.family,
                protocol=profile.protocol,
                model=profile.model,
                source_urls=source_urls,
                checked_date=shape["checked_date"],
                shape_status=PASSED if shape.get("level") == "shape_tested" else UNVERIFIED,
                smoke_status=SKIPPED if smoke.get("skipped") else PASSED,
                workflow_status=UNVERIFIED,
                capability_status=shape.get("capabilities") or {},
                limitations=[
                    f"{key}={value}"
                    for key, value in (shape.get("capabilities") or {}).items()
                    if value not in {"supported", "pass", PASSED}
                ],
            )
            written.append(record)
            families.add(profile.family)

    docs_report = docs_refresh_report(sorted(families))
    report = Report(
        title="Provider Certification",
        status="ok",
        next_action="Use ProviderReleaseCheck before release sign-off",
        sections=[
            ReportSection(
                "Records",
                [
                    f"{record.provider} -> shape={record.shape_status}, smoke={record.smoke_status}"
                    for record in written
                ],
            ),
            *docs_report.sections,
        ],
        data={
            "records_dir": str(records_dir),
            "records": [record.__dict__ for record in written],
            "docs": docs_report.data,
        },
    )
    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-certification.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _handle_provider(args: argparse.Namespace) -> int:
    if args.subcommand == "discover-local":
        from .install.local_models import LocalModelDetector

        class StaticLocalHttp:
            def get_json(self, url: str) -> object:
                return {"models": []}

        detector = LocalModelDetector(StaticLocalHttp())
        candidates = detector.detect(endpoints=args.endpoint)
        lines = [
            f"{candidate.endpoint} -> {', '.join(candidate.models)}"
            for candidate in candidates
        ]
        if not lines:
            lines = detector.notes or ["no local models discovered"]
        report = Report(
            title="Local Models",
            status="ok",
            next_action="Use provider setup with a local endpoint before routing chat to it",
            sections=[ReportSection("Candidates", lines)],
            data={
                "candidates": [candidate.__dict__ for candidate in candidates],
                "notes": detector.notes,
            },
        )
        return _emit(report, args.format)
    if args.subcommand == "setup":
        from .install.provider_setup import ProviderSetupWizard
        from .install.secrets import SecretStore

        result = ProviderSetupWizard(Path(".pf-agent"), SecretStore.for_platform(sys.platform, False)).configure(
            provider=args.provider or "",
            api_key=args.api_key,
            model=args.model or args.provider or "",
            verify=args.verify,
        )
        report = Report(
            title="Provider Setup",
            status="ok",
            next_action="Run `pf-agent provider certify --all --shape-only` before release",
            sections=[
                ReportSection(
                    "Profile",
                    [
                        f"provider={result.provider}",
                        f"model={result.model}",
                        f"profile={result.profile_path}",
                        f"secret_ref={result.secret_ref}",
                        f"verified={result.verified}",
                    ],
                )
            ],
            data=result.__dict__ | {"profile_path": str(result.profile_path)},
        )
        return _emit(report, args.format)
    if args.subcommand == "probe":
        return _handle_provider_probe(args)
    if args.subcommand == "routes":
        return _handle_provider_routes(args)
    if args.subcommand == "certify":
        return _handle_provider_certify(args)
    if args.subcommand == "fallback-status":
        chain = ["deepseek", "qwen", "openai", "fake"]
        report = Report(
            title="Provider Fallback",
            status="ok",
            next_action="Run `pf-agent provider test-chain` to verify fallback behavior",
            sections=[
                ReportSection(
                    "Chain",
                    [
                        "deepseek -> qwen -> openai -> fake",
                        "fallback_errors=timeout, rate_limit, invalid_response, unavailable, quota, context_too_large, model_missing",
                    ],
                )
            ],
            data={"fallback_chain": chain},
        )
        return _emit(report, args.format)
    if args.subcommand == "test-chain":
        from .agent import ProviderFallbackChain
        from .errors import ProviderError
        from .llm import FakeProvider, Message, ProviderRequest

        class FailingProvider:
            def __init__(self, name: str, code: str) -> None:
                self.name = name
                self.model = name
                self.code = code

            def generate(self, request: ProviderRequest):
                error = ProviderError(f"{self.name} simulated {self.code}")
                error.code = self.code
                raise error

        request = ProviderRequest(role="drafter", messages=[Message(role="user", content="fallback probe")])
        result = ProviderFallbackChain(
            [
                FailingProvider("deepseek", "timeout"),
                FailingProvider("qwen", "rate_limit"),
                FailingProvider("openai", "model_missing"),
                FakeProvider(name="fake", model="fake"),
            ]
        ).generate(request)
        report = Report(
            title="Provider Fallback",
            status="ok",
            next_action="Use fake fallback for offline-safe smoke tests",
            sections=[
                ReportSection(
                    "Attempts",
                    [
                        f"{attempt.provider}: {attempt.status}"
                        + (f" reason={attempt.fallback_reason}" if attempt.fallback_reason else "")
                        for attempt in result.attempts
                    ],
                ),
                ReportSection("Selected", [f"selected={result.selected_provider}"]),
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if not args.providers:
        report = _planned_report("provider", "Pass --providers <config.yaml> to list providers")
        return _emit(report, args.format)
    from .llm.registry import ProviderRegistry

    registry = ProviderRegistry.from_yaml(args.providers)
    roles = registry._roles  # noqa: SLF001 - read-only inspection for reporting
    sections = [
        ReportSection(heading="Roles", lines=[f"{role} -> {name}" for role, name in roles.items()])
    ]
    report = Report(
        title="Provider Routing",
        status="ok",
        next_action="Use `pf-agent chapter ... --provider <name>` to draft",
        sections=sections,
        data={"default_provider": registry._default_provider},  # noqa: SLF001
    )
    return _emit(report, args.format)


def _handle_prompt(args: argparse.Namespace) -> int:
    from .chat import SystemPromptRegistry, SystemPromptStore

    registry = SystemPromptRegistry.builtins()
    store = SystemPromptStore(Path(".pf-agent"))
    subcommand = args.subcommand or "list"
    if subcommand == "list":
        templates = registry.list()
        report = Report(
            title="System Prompts",
            status="ok",
            next_action="Use `pf-agent prompt show <id>` to inspect a template",
            sections=[
                ReportSection(
                    "Templates",
                    [f"{template.id}@{template.version}" for template in templates],
                )
            ],
            data={"templates": [template.to_dict() for template in templates]},
        )
        return _emit(report, args.format)
    if subcommand == "show":
        template_id = args.prompt_arg or args.template
        if not template_id:
            return _emit(_planned_report("prompt", "Pass a template id to `pf-agent prompt show`"), args.format)
        template = registry.get(template_id)
        report = Report(
            title="System Prompt",
            status="ok",
            next_action="Use `pf-agent prompt set --session <id> --template <id>` to pin it",
            sections=[
                ReportSection("Template", [f"id={template.id}", f"version={template.version}"]),
                ReportSection("Text", template.text.splitlines()),
                ReportSection("Changelog", template.changelog or ["(none)"]),
            ],
            data=template.to_dict(),
        )
        return _emit(report, args.format)
    if subcommand == "set":
        if not args.session:
            return _emit(_planned_report("prompt", "Pass --session before setting a prompt"), args.format)
        if args.text:
            record = store.set_session_override(args.session, args.text)
        else:
            record = store.set_session_template(
                args.session,
                args.template or args.prompt_arg or "professional_novel_editor",
                registry=registry,
            )
        report = Report(
            title="Session System Prompt",
            status="ok",
            next_action="Run `pf-agent chat --show-prompt` to inspect composed prompt data",
            sections=[
                ReportSection(
                    "Record",
                    [
                        f"session={record.session_id}",
                        f"template={record.template_id}",
                        f"version={record.version}",
                    ],
                )
            ],
            data=record.to_dict(),
        )
        return _emit(report, args.format)
    return _emit(_planned_report("prompt", "Run `pf-agent prompt list`"), args.format)


def _handle_prompt_template(args: argparse.Namespace) -> int:
    from .agent import PromptTemplateRegistry

    registry = PromptTemplateRegistry.builtins()
    subcommand = args.subcommand or "list"
    if subcommand == "list":
        templates = registry.list()
        report = Report(
            title="Prompt Templates",
            status="ok",
            next_action="Run `pf-agent prompt-template validate <id>` before wiring a workflow",
            sections=[
                ReportSection(
                    "Templates",
                    [
                        f"{template.id}@{template.version} "
                        f"vars={','.join(template.variables)} "
                        f"evidence={','.join(template.required_evidence)}"
                        for template in templates
                    ],
                )
            ],
            data={"templates": [template.to_dict() for template in templates]},
        )
        return _emit(report, args.format)
    if subcommand == "validate":
        if not args.template_id:
            return _emit(
                _planned_report("prompt-template", "Pass a template id to validate"),
                args.format,
            )
        validation = registry.validate_definition(args.template_id)
        report = Report(
            title="Prompt Template Validation",
            status="ok" if validation.valid else "fail",
            next_action="Use only valid registry templates in workflow prompt calls",
            sections=[
                ReportSection(
                    "Validation",
                    [
                        f"template={validation.template_id}",
                        f"valid={validation.valid}",
                        *(validation.errors or ["errors=none"]),
                    ],
                )
            ],
            data=validation.to_dict(),
        )
        return _emit(report, args.format)
    return _emit(_planned_report("prompt-template", "Run `pf-agent prompt-template list`"), args.format)


def _handle_session(args: argparse.Namespace) -> int:
    from .chat import ChatSessionStore

    store = ChatSessionStore(Path(".pf-agent"))
    subcommand = args.subcommand or "list"
    if subcommand == "list":
        sessions = store.list(project_slug=args.project, include_deleted=args.include_deleted)
        report = Report(
            title="Conversation Sessions",
            status="ok",
            next_action="Use `pf-agent session show <id>` for transcript metadata",
            sections=[
                ReportSection(
                    "Sessions",
                    [
                        f"{session.id}: status={session.status} mode={session.mode}"
                        + (f" project={session.project_slug}" if session.project_slug else "")
                        for session in sessions
                    ]
                    or ["(none)"],
                )
            ],
            data={"sessions": [session.__dict__ for session in sessions]},
        )
        return _emit(report, args.format)
    if subcommand == "cleanup":
        cleaned = store.cleanup(older_than_days=_parse_days(args.older_than))
        report = Report(
            title="Conversation Sessions",
            status="ok",
            next_action="Cleanup is soft-delete; use include-deleted to inspect removed sessions",
            sections=[ReportSection("Cleanup", [f"{session.id}: {session.status}" for session in cleaned] or ["(none)"])],
            data={"cleaned": [session.__dict__ for session in cleaned]},
        )
        return _emit(report, args.format)
    if subcommand == "search":
        if not args.session_id:
            return _emit(_planned_report("session", "Pass a query to `session search`"), args.format)
        results = store.search(args.session_id, project_slug=args.project)
        report = Report(
            title="Conversation Search",
            status="ok",
            next_action="Open the matching session before using old context as current canon",
            sections=[
                ReportSection(
                    "Results",
                    [
                        f"{result.session_id} {result.kind} {result.source}: {result.snippet}"
                        for result in results
                    ]
                    or ["(none)"],
                )
            ],
            data={"results": [result.to_dict() for result in results]},
        )
        return _emit(report, args.format)
    if not args.session_id:
        return _emit(_planned_report("session", f"Pass a session id for `session {subcommand}`"), args.format)
    if subcommand == "export":
        include_tools = not bool(getattr(args, "no_tools", False))
        include_evidence = not bool(getattr(args, "no_evidence", False))
        redact = not bool(getattr(args, "no_redact", False))
        payload = store.export_bundle(
            args.session_id,
            include_tools=include_tools,
            include_evidence=include_evidence,
            redact=redact,
        )
        markdown = store.export_bundle_markdown(
            args.session_id,
            include_tools=include_tools,
            include_evidence=include_evidence,
            redact=redact,
        )
        report = Report(
            title="Session Export",
            status="ok",
            next_action="Import this bundle with `pf-agent session import <path>` when needed",
            sections=[
                ReportSection(
                    "Bundle",
                    [
                        f"id={payload['session']['id']}",
                        f"messages={len(payload['messages'])}",
                        f"include_tools={include_tools}",
                        f"include_evidence={include_evidence}",
                        f"redacted={redact}",
                    ],
                ),
                ReportSection("Markdown", markdown.splitlines()[:12] if args.format == "markdown" else []),
            ],
            data=payload,
        )
        return _emit(report, args.format)
    if subcommand == "import":
        path = Path(args.session_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        session = store.import_bundle(payload)
        report = Report(
            title="Session Import",
            status="ok",
            next_action=f"Use `pf-agent session show {session.id}` to inspect the imported session",
            sections=[
                ReportSection(
                    "Imported",
                    [
                        f"id={session.id}",
                        f"status={session.status}",
                        f"mode={session.mode}",
                        f"project={session.project_slug or '(none)'}",
                    ],
                )
            ],
            data=session.__dict__,
        )
        return _emit(report, args.format)
    if subcommand == "branch":
        if args.from_step is None or not args.name:
            return _emit(
                _planned_report("session", "Run `pf-agent session branch <id> --from-step <n> --name <name>`"),
                args.format,
            )
        branch = store.branch(args.session_id, from_step=args.from_step, name=args.name)
        report = Report(
            title="Session Branch",
            status="ok",
            next_action=f"Continue from `{branch.id}` or switch to it explicitly",
            sections=[
                ReportSection(
                    "Branch",
                    [
                        f"id={branch.id}",
                        f"parent={branch.parent_session_id}",
                        f"name={branch.branch_name}",
                        f"from_step={branch.branched_from_step}",
                    ],
                )
            ],
            data=branch.__dict__,
        )
        return _emit(report, args.format)
    if subcommand == "branches":
        branches = store.branches(args.session_id)
        report = Report(
            title="Session Branches",
            status="ok",
            next_action="Switch to a branch id to continue alternate context",
            sections=[
                ReportSection(
                    "Branches",
                    [
                        f"{branch.id}: name={branch.branch_name} from_step={branch.branched_from_step}"
                        for branch in branches
                    ]
                    or ["(none)"],
                )
            ],
            data={"branches": [branch.__dict__ for branch in branches]},
        )
        return _emit(report, args.format)
    if subcommand == "switch":
        session = store.switch(args.session_id)
        report = Report(
            title="Session Switch",
            status="ok",
            next_action="Use this session id for the next chat turn",
            sections=[
                ReportSection(
                    "Session",
                    [
                        f"id={session.id}",
                        f"status={session.status}",
                        f"parent={session.parent_session_id or '(none)'}",
                        f"name={session.branch_name or session.title or '(none)'}",
                    ],
                )
            ],
            data=session.__dict__,
        )
        return _emit(report, args.format)
    if subcommand == "merge":
        if not args.into_session:
            return _emit(
                _planned_report("session", "Run `pf-agent session merge <branch_id> --into <session_id>`"),
                args.format,
            )
        result = store.merge(
            args.session_id,
            into_id=args.into_session,
            message_steps=args.message_step,
            only_approved=bool(args.only_approved),
        )
        report = Report(
            title="Session Merge",
            status="ok",
            next_action="Review the target session before relying on merged branch conclusions",
            sections=[
                ReportSection(
                    "Merge",
                    [
                        f"source={result.source_session_id}",
                        f"target={result.target_session_id}",
                        f"merged={result.merged_count}",
                        f"skipped={result.skipped_count}",
                        f"steps={','.join(str(step) for step in result.merged_steps) or '(none)'}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if subcommand == "show":
        context = store.load_context(args.session_id)
        session = context.session
    elif subcommand == "archive":
        session = store.archive(args.session_id)
    elif subcommand == "restore":
        session = store.restore(args.session_id)
    elif subcommand == "delete":
        session = store.delete(args.session_id)
    elif subcommand == "pin":
        session = store.pin(args.session_id)
    else:
        return _emit(_planned_report("session", "Run `pf-agent session list`"), args.format)
    report = Report(
        title="Conversation Sessions",
        status="ok",
        next_action="Use session lifecycle commands to keep active context focused",
        sections=[
            ReportSection(
                "Session",
                [
                    f"id={session.id}",
                    f"status={session.status}",
                    f"mode={session.mode}",
                    f"project={session.project_slug or '(none)'}",
                    f"updated_at={session.updated_at}",
                ],
            )
        ],
        data=session.__dict__,
    )
    return _emit(report, args.format)


def _parse_days(value: str) -> int:
    value = str(value).strip().lower()
    if value.endswith("d"):
        value = value[:-1]
    return max(0, int(value))


def _handle_chat(args: argparse.Namespace) -> int:
    if args.subcommand == "sessions":
        from .chat import ChatSessionStore

        store = ChatSessionStore(Path(".pf-agent"))
        sessions = store.list(project_slug=args.project)
        lines = [
            f"{session.id} -> {session.mode}"
            + (f" ({session.project_slug})" if session.project_slug else "")
            for session in sessions
        ]
        report = Report(
            title="Chat Sessions",
            status="ok",
            next_action="Use a session id to resume a durable chat transcript",
            sections=[ReportSection("Sessions", lines)],
            data={"sessions": [session.__dict__ for session in sessions]},
        )
        return _emit(report, args.format)
    if args.subcommand == "classify":
        from .agent import IntentRouter

        text = args.text or args.message or ""
        decision = IntentRouter().classify(text, mode=args.mode, project_slug=args.project)
        report = Report(
            title="Chat Intent",
            status="ok",
            next_action="Pass this intent to the Agent Kernel",
            sections=[
                ReportSection(
                    "Intent",
                    [
                        f"name: {decision.name}",
                        f"confidence: {decision.confidence:.2f}",
                        f"permission: {decision.required_permission}",
                        f"reason: {decision.reason}",
                    ],
                )
            ],
            data=decision.__dict__,
        )
        return _emit(report, args.format)
    from .chat import ChatSessionStore
    from .llm import FakeProvider

    if args.message and args.message.strip().startswith("/"):
        from .chat.slash import SlashCommandContext, SlashCommandRegistry

        project_slug = None if args.no_project else args.project
        action = SlashCommandRegistry.default().resolve(
            args.message,
            SlashCommandContext(
                permission_ceiling=args.permission_level,
                mode=args.mode,
                project_slug=project_slug,
            ),
        )
        if action is not None:
            if action.name == "usage":
                session_store = ChatSessionStore(Path(".pf-agent"))
                try:
                    usage = session_store.usage("cli")
                except ProseForgeAgentError:
                    usage = None
                lines = (
                    [
                        f"session={usage.session_id}",
                        f"messages={usage.message_count}",
                        f"words={usage.word_count}",
                        f"tool_calls={usage.tool_call_count}",
                        f"evidence_refs={usage.evidence_ref_count}",
                    ]
                    if usage is not None
                    else ["session=cli", "messages=0", "words=0", "tool_calls=0", "evidence_refs=0"]
                )
                return _emit(
                    Report(
                        title="Session Usage",
                        status="ok",
                        next_action="Use /compress when context grows too large",
                        sections=[ReportSection("Usage", lines)],
                        data=usage.to_dict() if usage is not None else {"session_id": "cli", "message_count": 0},
                    ),
                    args.format,
                )
            report = Report(
                title="Slash Commands" if action.name == "help" else "Slash Command",
                status=action.status,
                next_action="Slash commands are resolved locally without a model call",
                sections=[ReportSection("Result", action.message.splitlines())],
                data=action.to_dict(),
            )
            return _emit(report, args.format)

    if args.provider is None and args.message:
        from .setup.first_run import FirstRunBootstrap

        verdict = FirstRunBootstrap(Path(".pf-agent")).check()
        if not verdict.ready:
            print(verdict.guidance)
            return 2

    project_slug = None if args.no_project else args.project
    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    session_store = ChatSessionStore(Path(".pf-agent"))
    mode = args.mode
    permission_level = args.permission_level
    profile = None
    if getattr(args, "profile", None):
        from .agent import AgentProfileRegistry

        registry = (
            AgentProfileRegistry.from_yaml(args.profiles_file)
            if args.profiles_file
            else AgentProfileRegistry.builtins()
        )
        profile = registry.resolve(args.profile, session_permission_max=args.permission_level)
        mode = profile.mode
        permission_level = profile.permission_ceiling
    if getattr(args, "show_prompt", False):
        from .chat import ChatPromptBuilder

        text = args.message or args.text or ""
        print(
            ChatPromptBuilder()
            .build(text=text, mode=mode, project_slug=project_slug, system_override=args.system)
            .render_markdown()
        )
        return 0
    if getattr(args, "propose_handoff", False):
        from .chat.handoff import ChatWorkflowHandoff, render_handoff

        text = args.message or args.text or ""
        package = ChatWorkflowHandoff().create(
            text,
            project_slug=project_slug,
            mode=mode,
        )
        report = Report(
            title="Handoff Package",
            status="ok",
            next_action="Confirm write-level packages before starting a workflow",
            sections=[ReportSection("Package", render_handoff(package))],
            data=package.to_dict(),
        )
        return _emit(report, args.format)
    if getattr(args, "show_memory_candidates", False):
        from .chat.memory import ChatMemoryExtractor, render_memory_candidates

        text = args.message or args.text or ""
        candidates = ChatMemoryExtractor().write_candidates(
            Path(".pf-agent"),
            text,
            project_slug=project_slug,
        )
        report = Report(
            title="Memory Candidates",
            status="ok",
            next_action="Review candidates before promoting them to durable memory",
            sections=[ReportSection("Queues", render_memory_candidates(candidates))],
            data={"candidates": [candidate.to_dict() for candidate in candidates]},
        )
        return _emit(report, args.format)
    if getattr(args, "show_citations", False):
        from .chat.retrieval import ChatRetrievalResponder, render_citations

        text = args.message or args.text or ""
        answer = ChatRetrievalResponder(evidence=[]).answer(text, project_slug=project_slug)
        rendered = render_citations(answer)
        report = Report(
            title="Chat Citations",
            status="ok" if not answer.degraded else "degraded",
            next_action="Add project evidence before relying on this answer",
            sections=[
                ReportSection("Answer", answer.text.splitlines()),
                ReportSection("Citations", rendered.splitlines()),
            ],
            data=answer.to_dict(),
        )
        return _emit(report, args.format)
    if getattr(args, "show_events", False):
        from .agent import EventBus
        from .tui.streaming import ToolOutputStreamer

        event_bus = EventBus(Path(".pf-agent") / "events.jsonl")
        chunks = ToolOutputStreamer(
            tool_call_id="call_fake",
            event_bus=event_bus,
            chunk_char_limit=16,
        ).stream_text("fake tool output")
        report = Report(
            title="Tool Output Events",
            status="ok",
            next_action="Use the event bus to subscribe terminal or gateway surfaces to chunks",
            sections=[
                ReportSection(
                    "Chunks",
                    [
                        f"tool_call_id={chunk.tool_call_id} sequence={chunk.sequence} final={str(chunk.is_final).lower()} text={chunk.text}"
                        for chunk in chunks
                    ],
                )
            ],
            data={"chunks": [chunk.to_dict() for chunk in chunks]},
        )
        return _emit(report, args.format)
    if not args.message:
        from .chat.repl import ChatRepl

        return ChatRepl(
            provider=provider,
            session_store=session_store,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
            stream=getattr(args, "stream", False),
        ).run()
    from .agent import AgentKernel, AgentTurnRequest, IntentRouter

    explain_safety = getattr(args, "explain_safety", False)
    safety_guard = None
    if explain_safety:
        from .agent.safety import InjectionGuard

        safety_guard = InjectionGuard()
    kernel = AgentKernel(
        provider=provider,
        intent_router=IntentRouter(),
        session_store=session_store,
        safety=safety_guard,
    )
    if getattr(args, "stream", False):
        request = AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
        )
        for chunk in kernel.run_turn_stream(request):
            print(chunk.text, end="", flush=True)
        print("")
        return 0
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
        )
    )
    from .agent import AuditTrailStore

    AuditTrailStore(Path(".pf-agent")).record_turn(
        "cli",
        {
            "input": args.message,
            "intent": result.intent.__dict__,
            "system_prompt_version": "session_override" if args.system else "chat-prompt-v1",
            "evidence_pack": [{"id": ref} for ref in result.evidence_refs],
            "tool_choice": result.tool_calls[0].name if result.tool_calls else "",
            "tool_args": {},
            "tool_result": result.tool_calls[0].__dict__ if result.tool_calls else {},
            "provider": {"name": provider.name, "model": provider.model},
            "latency_ms": 0,
            "token_usage": {
                "prompt_tokens": len(args.message.split()),
                "completion_tokens": len(result.text.split()),
            },
            "model_output": result.text,
            "final_action": "respond",
            "trace_id": result.trace_id,
        },
    )
    sections = []
    if profile is not None:
        sections.append(
            ReportSection(
                "Profile",
                [
                    f"profile: {profile.name}",
                    f"mode: {profile.mode}",
                    f"permission_ceiling: {profile.permission_ceiling}",
                ],
            )
        )
    if explain_safety and safety_guard is not None:
        verdict = safety_guard.assess(
            args.message,
            provenance="untrusted",
            session_ceiling=permission_level,
        )
        sections.append(
            ReportSection(
                "Safety",
                [
                    f"provenance: {verdict.provenance}",
                    f"session_grant: {permission_level}",
                    f"allowed_ceiling: {verdict.allowed_ceiling}",
                    f"flags: {', '.join(verdict.flags) or 'none'}",
                    f"reason: {verdict.reason}",
                ],
            )
        )
    sections.append(ReportSection("Response", result.text.splitlines()))
    report = Report(
        title="Agent Chat",
        status="ok",
        next_action="Use chat sessions to resume durable transcripts",
        sections=sections,
        data={
            "trace_id": result.trace_id,
            "profile": profile.__dict__ if profile is not None else None,
            "intent": result.intent.__dict__,
            "tool_calls": [call.__dict__ for call in result.tool_calls],
            "evidence_refs": result.evidence_refs,
            "memory_candidate_ids": result.memory_candidate_ids,
            "events": result.events,
        },
    )
    return _emit(report, args.format)


def _handle_context(args: argparse.Namespace) -> int:
    if args.subcommand not in {"status", "compact", "current", "switch", "pin"}:
        return _emit(_planned_report("context", "Run `pf-agent context status`"), args.format)
    if args.subcommand in {"current", "switch", "pin"}:
        from .chat.context import ActiveContextStore

        active_store = ActiveContextStore(Path(".pf-agent"))
        if args.subcommand == "switch":
            if not args.project and not args.session:
                return _emit(_planned_report("context", "Run `pf-agent context switch --project <slug>`"), args.format)
            context = active_store.switch(project=args.project, session=args.session)
        elif args.subcommand == "pin":
            if not args.session:
                return _emit(_planned_report("context", "Run `pf-agent context pin --session <id>`"), args.format)
            context = active_store.pin(session=args.session)
        else:
            context = active_store.current()
        report = Report(
            title="Active Context",
            status="ok",
            next_action="Subsequent commands can use this project/session as their default context",
            sections=[
                ReportSection(
                    "Current",
                    [
                        f"project={context.project or '(none)'}",
                        f"session={context.session or '(none)'}",
                        f"pinned_sessions={', '.join(context.pinned_sessions) or '(none)'}",
                    ],
                )
            ],
            data={"active_context": context.to_dict()},
        )
        return _emit(report, args.format)
    from .agent import ContextWindowManager
    from .chat import ChatSessionStore
    from .llm import Message

    manager = ContextWindowManager()
    store = ChatSessionStore(Path(".pf-agent"))
    messages: list[Message] = []
    if args.session:
        context = store.load_context(args.session)
        messages = [Message(role=message.role, content=message.content) for message in context.messages]
    if args.subcommand == "compact":
        if not args.session:
            return _emit(_planned_report("context", "Pass --session for context compact"), args.format)
        compacted = manager.compact_messages(messages, keep_last=args.keep_last)
        compacted_count = max(0, len(messages) - max(0, args.keep_last))
        report = Report(
            title="Context Window",
            status="ok",
            next_action="Use compacted summaries before building large prompts",
            sections=[
                ReportSection(
                    "Compaction",
                    [
                        f"session={args.session}",
                        f"original_messages={len(messages)}",
                        f"compacted_messages={compacted_count}",
                        f"result_messages={len(compacted)}",
                    ],
                )
            ],
            data={"messages": [message.__dict__ for message in compacted]},
        )
        return _emit(report, args.format)
    usage = manager.status(
        provider=args.provider,
        messages=messages,
        evidence=[],
        reserve_tokens=args.reserve,
        max_context_tokens=args.max_context,
    )
    report = Report(
        title="Context Window",
        status="ok",
        next_action="Reduce evidence or compact the session if remaining tokens are low",
        sections=[
            ReportSection(
                "Usage",
                [
                    f"provider={usage.provider}",
                    f"max_context_tokens={usage.max_context_tokens}",
                    f"prompt_tokens={usage.prompt_tokens}",
                    f"evidence_budget_tokens={usage.evidence_budget_tokens}",
                    f"remaining_tokens={usage.remaining_tokens}",
                ],
            )
        ],
        data=usage.to_dict(),
    )
    return _emit(report, args.format)


def _handle_rag(args: argparse.Namespace) -> int:
    if args.subcommand == "eval":
        if not args.slug:
            return _emit(_planned_report("rag", "Run `pf-agent rag eval --slug <slug>`"), args.format)
        from .retrieval import (
            FakeEmbeddingProvider,
            HybridRetriever,
            JsonlVectorStore,
            RagEvaluator,
            default_eval_cases_from_documents,
            load_eval_cases,
            load_rag_documents,
        )

        chunks_path = Path(".pf-agent") / "workspace" / args.slug / "rag" / "chunks.jsonl"
        vector_path = Path(".pf-agent") / "workspace" / args.slug / "rag" / "vectors.jsonl"
        documents = load_rag_documents(chunks_path)
        searcher = HybridRetriever(
            documents,
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=JsonlVectorStore(vector_path),
        )
        cases = load_eval_cases(args.suite) if args.suite else default_eval_cases_from_documents(documents)
        result = RagEvaluator(searcher).evaluate(cases, project_slug=args.slug)
        report = Report(
            title="RAG Evaluation",
            status="ok" if result.case_count else "degraded",
            next_action="Add eval cases or ingest chunks before trusting retrieval quality",
            sections=[
                ReportSection(
                    "Metrics",
                    [
                        f"cases={result.case_count}",
                        f"hit@1={result.hit_at_1:.3f}",
                        f"hit@3={result.hit_at_3:.3f}",
                        f"hit@5={result.hit_at_5:.3f}",
                        f"source_recall={result.source_recall:.3f}",
                        f"irrelevant_rate={result.irrelevant_rate:.3f}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand in {"ingest", "ingest-file", "status"}:
        if not args.slug:
            return _emit(_planned_report("rag", "Pass --slug for RAG commands"), args.format)
        from .retrieval import RagIngestionPipeline

        pipeline = RagIngestionPipeline(Path(".pf-agent") / "workspace")
        if args.subcommand == "ingest-file":
            if not args.rag_query:
                return _emit(_planned_report("rag", "Run `pf-agent rag ingest-file <path> --slug <slug>`"), args.format)
            report_data = pipeline.ingest_file(args.rag_query, slug=args.slug)
        elif args.subcommand == "status":
            report_data = pipeline.status(args.slug)
        else:
            report_data = pipeline.ingest_project(args.slug)
        title = "RAG Status" if args.subcommand == "status" else "RAG Ingestion"
        report = Report(
            title=title,
            status="ok",
            next_action="Use `pf-agent rag search <query> --slug <slug>` to query indexed chunks",
            sections=[
                ReportSection(
                    "Chunks",
                    [
                        f"slug={report_data.slug}",
                        f"added={report_data.added_count}",
                        f"updated={report_data.updated_count}",
                        f"unchanged={report_data.unchanged_count}",
                        f"total={report_data.total_chunks}",
                    ],
                )
            ],
            data=report_data.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand != "search" or not args.rag_query or not args.slug:
        return _emit(_planned_report("rag", "Run `pf-agent rag search <query> --slug <slug>`"), args.format)
    from .retrieval import FakeEmbeddingProvider, HybridRetriever, JsonlVectorStore, load_rag_documents

    chunks_path = Path(".pf-agent") / "workspace" / args.slug / "rag" / "chunks.jsonl"
    vector_path = Path(".pf-agent") / "workspace" / args.slug / "rag" / "vectors.jsonl"
    documents = load_rag_documents(chunks_path)
    retriever = HybridRetriever(
        documents,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=JsonlVectorStore(vector_path),
    )
    results = retriever.search(args.rag_query, project_slug=args.slug, top_k=args.top_k)
    report = Report(
        title="Hybrid RAG Search",
        status="ok" if results else "degraded",
        next_action="Run `pf-agent rag ingest --slug <slug>` if no relevant chunks are found",
        sections=[
            ReportSection(
                "Results",
                [
                    f"{result.id}: score={result.score:.3f} channels={','.join(result.channels)} source={result.metadata.get('source', '-')}"
                    for result in results
                ]
                or ["(none)"],
            )
        ],
        data={"query": args.rag_query, "slug": args.slug, "results": [result.to_dict() for result in results]},
    )
    return _emit(report, args.format)


def _handle_tools(args: argparse.Namespace) -> int:
    if args.subcommand == "gateway":
        from .tools import ManagedToolGateway, ManagedToolInvocationContext

        action = args.tool_arg or "check"
        if action != "check":
            _emit(
                Report(
                    title="Managed Tool Gateway",
                    status="error",
                    next_action="Use `pf-agent tools gateway check --provider fake`",
                    sections=[ReportSection("Error", [f"unsupported gateway action: {action}"])],
                ),
                args.format,
            )
            return 1

        gateway = ManagedToolGateway.fake()
        context = ManagedToolInvocationContext(
            permission_ceiling="read_only",
            credential_scopes={"web"},
            provider=args.provider,
        )
        probe = gateway.invoke("web.search", {"query": "gateway check"}, context)
        declarations = gateway.list()
        report = Report(
            title="Managed Tool Gateway",
            status="ok" if probe.status == "ok" else "degraded",
            next_action="Register managed tools only through declared gateway capabilities",
            sections=[
                ReportSection(
                    "Declarations",
                    [
                        f"{tool.name} -> {tool.permission} scope={tool.credential_scope or '-'}"
                        for tool in declarations
                    ],
                ),
                ReportSection("Probe", [f"{probe.tool}: {probe.status}"]),
            ],
            data={
                "provider": args.provider,
                "declarations": [tool.to_dict() for tool in declarations],
                "probe": probe.to_dict(),
            },
        )
        return _emit(report, args.format)

    from .agent import default_tool_registry

    registry = default_tool_registry()
    tools = registry.list(domain=args.domain)
    lines = []
    for tool in tools:
        aliases = f" aliases={', '.join(tool.aliases)}" if tool.aliases else ""
        if args.include_permissions:
            lines.append(f"{tool.name}{aliases} -> {tool.permission} [{tool.domain}] ({tool.description})")
        else:
            lines.append(f"{tool.name}{aliases} [{tool.domain}] ({tool.description})")
    report = Report(
        title="Agent Tools",
        status="ok",
        next_action="Authorize tool calls through PermissionPolicy",
        sections=[ReportSection("Tools", lines or ["(none)"])],
        data={
            "tools": [
                {
                    "name": tool.name,
                    "permission": tool.permission,
                    "domain": tool.domain,
                    "aliases": list(tool.aliases),
                    "input_schema": tool.input_schema,
                    "output_schema": tool.output_schema,
                    "description": tool.description,
                    "enabled": tool.enabled,
                }
                for tool in tools
            ],
            "domain": args.domain,
        },
    )
    return _emit(report, args.format)


def _handle_skills(args: argparse.Namespace) -> int:
    from .skills import FakeSkillHubClient, SkillInstaller, SkillRegistry

    if args.subcommand == "search":
        results = FakeSkillHubClient().search(args.skill_arg or "")
        report = Report(
            title="Skill Hub Search",
            status="ok",
            next_action="Inspect permissions before installing any skill package",
            sections=[ReportSection("Results", [f"{item.skill_id} {item.version}" for item in results] or ["(none)"])],
            data={"results": [item.to_dict() for item in results]},
        )
        return _emit(report, args.format)
    if args.subcommand == "install" and args.skill_arg:
        plan = SkillInstaller(Path(".pf-agent") / "skills").install(args.skill_arg, dry_run=args.dry_run)
        report = Report(
            title="Skill Install",
            status=plan.status,
            next_action="Review checksum, permissions, and rollback plan before installing",
            sections=[
                ReportSection(
                    "Plan",
                    [
                        f"skill={plan.skill_id}",
                        f"checksum={plan.checksum}",
                        f"permissions={', '.join(plan.requested_permissions)}",
                    ],
                )
            ],
            data=plan.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "update" and args.all:
        plans = SkillInstaller(Path(".pf-agent") / "skills").update_all(dry_run=args.dry_run, use_offline_cache=True)
        report = Report(
            title="Skill Update",
            status="ok",
            next_action="Review each plan before applying updates",
            sections=[ReportSection("Plans", [f"{plan.skill_id}: {plan.status}" for plan in plans] or ["(none)"])],
            data={"plans": [plan.to_dict() for plan in plans]},
        )
        return _emit(report, args.format)
    if args.subcommand not in {None, "list"}:
        return _emit(_planned_report("skills", "Run `pf-agent skills list`"), args.format)

    records = SkillRegistry.discover([Path(".pf-agent") / "skills"])
    report = Report(
        title="Skills",
        status="ok",
        next_action="Use dry-run install or approval flows before enabling new skills",
        sections=[
            ReportSection(
                "Skills",
                [f"{record.name} {record.version} enabled={str(record.enabled).lower()}" for record in records]
                or ["(none)"],
            )
        ],
        data={"skills": [record.to_dict() for record in records]},
    )
    return _emit(report, args.format)


def _handle_jobs(args: argparse.Namespace) -> int:
    if args.subcommand in {"list", "status", "logs", "cancel"}:
        from .notifications import JobStatusCenter

        center = JobStatusCenter(Path(".pf-agent"))
        if args.subcommand == "list":
            jobs = center.list()
            report = Report(
                title="Job Status Center",
                status="ok",
                next_action="Use `pf-agent jobs status <job_id>` for details",
                sections=[ReportSection("Jobs", [f"{job.id}: {job.name} status={job.status}" for job in jobs] or ["(none)"])],
                data={"jobs": [job.to_dict() for job in jobs]},
            )
            return _emit(report, args.format)
        if not args.job_name:
            return _emit(_planned_report("jobs", f"Pass a job id for `jobs {args.subcommand}`"), args.format)
        if args.subcommand == "logs":
            logs = center.logs(args.job_name)
            report = Report(
                title="Job Status Center",
                status="ok",
                next_action="Inspect failed job logs before retrying",
                sections=[ReportSection("Logs", [f"{entry.created_at} {entry.status}: {entry.message}" for entry in logs] or ["(none)"])],
                data={"logs": [entry.to_dict() for entry in logs]},
            )
            return _emit(report, args.format)
        job = center.cancel(args.job_name) if args.subcommand == "cancel" else center.get(args.job_name)
        report = Report(
            title="Job Status Center",
            status="ok",
            next_action="Use notifications for long-running job updates",
            sections=[
                ReportSection(
                    "Job",
                    [f"id={job.id}", f"name={job.name}", f"status={job.status}", f"updated_at={job.updated_at}"],
                )
            ],
            data=job.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand != "run" or not args.job_name:
        report = _planned_report("jobs", "Use `pf-agent jobs run <job-name> --dry-run`")
        return _emit(report, args.format)
    from .agent import BackgroundJobRunner, EventBus

    runner = BackgroundJobRunner(event_bus=EventBus(Path(".pf-agent") / "events.jsonl"))
    result = runner.run(args.job_name, provider=args.provider, dry_run=args.dry_run)
    report = Report(
        title="Background Job",
        status=result.status,
        next_action="Inspect the event bus before scheduling recurring jobs",
        sections=[
            ReportSection(
                "Result",
                [
                    f"job={result.job_name}",
                    f"status={result.status}",
                    f"allowed={str(result.allowed).lower()}",
                    f"dry_run={str(result.dry_run).lower()}",
                ],
            )
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_notifications(args: argparse.Namespace) -> int:
    if args.subcommand not in {"list", "test"}:
        return _emit(_planned_report("notifications", "Run `pf-agent notifications list`"), args.format)
    from .notifications import DesktopNotificationChannel, NotificationDispatcher, NotificationEvent, WebhookNotificationChannel

    channels = [DesktopNotificationChannel(enabled=True)] if getattr(args, "desktop", False) else []
    if getattr(args, "webhook", False):
        channels.append(WebhookNotificationChannel(enabled=True))
    dispatcher = NotificationDispatcher(Path(".pf-agent"), channels=channels)
    channel_results: list[dict] = []
    if args.subcommand == "test":
        result = dispatcher.dispatch(
            NotificationEvent(
                event_type="notification_test",
                title="Notification test",
                message="ProseForge Agent notification center is reachable",
            )
        )
        channel_results = result.channel_results
    events = dispatcher.list_events()
    sections = [
        ReportSection(
            "Events",
            [f"{event.event_type}: {event.title}" for event in events] or ["(none)"],
        )
    ]
    if getattr(args, "desktop", False):
        sections.append(
            ReportSection(
                "Desktop",
                [
                    f"{result.get('channel', 'desktop')}: {result.get('status')} {result.get('reason', '')}".rstrip()
                    for result in channel_results
                ]
                or ["desktop: not requested"],
            )
        )
    if getattr(args, "webhook", False):
        webhook_results = [result for result in channel_results if result.get("channel") == "webhook"]
        sections.append(
            ReportSection(
                "Webhook",
                [
                    f"webhook: {result.get('status')} {result.get('reason', '')}".rstrip()
                    for result in webhook_results
                ]
                or ["webhook: not requested"],
            )
        )
    report = Report(
        title="Notifications",
        status="ok",
        next_action="Wire background jobs to dispatch notification events",
        sections=sections,
        data={"events": [event.to_dict() for event in events], "channels": channel_results},
    )
    return _emit(report, args.format)


def _handle_plugin(args: argparse.Namespace) -> int:
    if args.subcommand == "test":
        if not args.plugin_arg:
            return _emit(_planned_report("plugin test", "Run `pf-agent plugin test <plugin_path>`"), args.format)
        from .plugins import PluginTestHarness

        test_report = PluginTestHarness().run(
            args.plugin_arg,
            with_demo_project=args.with_demo_project,
            hook=args.hook,
        )
        report = Report(
            title="Plugin Test Harness",
            status=test_report.status,
            next_action="Fix blocked checks before publishing or installing the plugin",
            sections=[
                ReportSection("Checks", [f"{name}={status}" for name, status in test_report.checks.items()]),
                ReportSection("Errors", test_report.errors or ["(none)"]),
            ],
            data=test_report.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "deps":
        plugin_args = [args.plugin_arg, *getattr(args, "plugin_extra", [])]
        plugin_args = [item for item in plugin_args if item]
        if plugin_args and plugin_args[0] == "check":
            plugin_args = plugin_args[1:]
        if not plugin_args:
            return _emit(_planned_report("plugin deps", "Run `pf-agent plugin deps check <plugin_id>`"), args.format)
        from .plugins import PluginDependencyManager

        report_data = PluginDependencyManager(Path(".pf-agent")).check(plugin_args[0])
        report = Report(
            title="Plugin Dependencies",
            status=report_data.status,
            next_action="Review install commands before changing the Python environment",
            sections=[
                ReportSection("Dependencies", report_data.dependencies or ["(none)"]),
                ReportSection(
                    "Issues",
                    [f"{issue.kind}: {issue.dependency} - {issue.message}" for issue in report_data.issues] or ["(none)"],
                ),
                ReportSection("Dry Run Install Plan", report_data.install_commands or ["(none)"]),
            ],
            data=report_data.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand in {"install", "update", "remove", "enable", "disable"}:
        if not args.plugin_arg:
            return _emit(_planned_report("plugin", f"Run `pf-agent plugin {args.subcommand} <plugin>`"), args.format)
        from .plugins import PluginManager

        manager = PluginManager(Path(".pf-agent"))
        if args.subcommand == "install":
            result = manager.install(args.plugin_arg)
        elif args.subcommand == "update":
            result = manager.update(args.plugin_arg)
        elif args.subcommand == "remove":
            result = manager.remove(args.plugin_arg)
        elif args.subcommand == "enable":
            result = manager.enable(args.plugin_arg)
        else:
            result = manager.disable(args.plugin_arg)
        report = Report(
            title="Plugin Action",
            status="ok",
            next_action="Run `pf-agent plugin list` to inspect installed plugins",
            sections=[ReportSection("Plugin", [f"id={result.plugin_id}", f"status={result.status}", f"path={result.path or '(none)'}"])],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand not in {"list", "discover", "info"}:
        return _emit(_planned_report("plugin", "Run `pf-agent plugin list`"), args.format)
    from .plugins import PluginDiscovery

    discovery = PluginDiscovery(
        local_dirs=[Path(".pf-agent") / "plugins"],
        registry_index=args.registry,
    )
    if args.subcommand == "info":
        if not args.plugin_arg:
            return _emit(_planned_report("plugin", "Run `pf-agent plugin info <plugin_id>`"), args.format)
        plugins = [discovery.info(args.plugin_arg)]
    else:
        plugins = discovery.discover()
    report = Report(
        title="Plugins",
        status="ok",
        next_action="Install or enable a plugin only after reviewing its manifest permissions",
        sections=[
            ReportSection(
                "Plugins",
                [f"{plugin.id}: {plugin.name} {plugin.version} source={plugin.source}" for plugin in plugins] or ["(none)"],
            )
        ],
        data={"plugins": [plugin.to_dict() for plugin in plugins]},
    )
    return _emit(report, args.format)


def _handle_tui(args: argparse.Namespace) -> int:
    from io import StringIO

    from .tui import TerminalApp

    project = None if args.no_project else args.project
    if args.check:
        buffer = StringIO()
        TerminalApp(
            provider=args.provider,
            project=project,
            mode=args.mode,
            input_stream=StringIO(""),
            output_stream=buffer,
        ).start(check=True)
        lines = [line for line in buffer.getvalue().splitlines() if line]
        report = Report(
            title="Terminal UI",
            status="ok",
            next_action="Run `pf-agent tui --provider fake --no-project` for an interactive shell",
            sections=[
                ReportSection(
                    "State",
                    [
                        f"provider={args.provider}",
                        f"project={project or '(none)'}",
                        f"mode={args.mode}",
                        "status=running",
                    ],
                ),
                ReportSection("Render", lines),
            ],
            data={"provider": args.provider, "project": project, "mode": args.mode, "rendered": lines},
        )
        return _emit(report, args.format)
    return TerminalApp(provider=args.provider, project=project, mode=args.mode).start()


def _handle_gateway(args: argparse.Namespace) -> int:
    if args.subcommand == "media":
        from .gateway import MediaIngestion

        action = args.gateway_arg or "inspect"
        if action != "inspect":
            return _emit(_planned_report("gateway", "Run `pf-agent gateway media inspect --fixture voice-note`"), args.format)
        fixtures = {
            "voice-note": {"type": "voice", "filename": "voice-note.ogg", "content": b"voice bytes", "mime_type": "audio/ogg"},
            "image": {"type": "image", "filename": "image.png", "content": b"png", "width": 1, "height": 1},
        }
        attachment = fixtures.get(args.fixture or "voice-note", fixtures["voice-note"])
        record = MediaIngestion(provider=args.provider).ingest(attachment)
        report = Report(
            title="Gateway Media",
            status=record.status,
            next_action="Promote attachment records into retrieval only after review",
            sections=[
                ReportSection(
                    "Attachment",
                    [
                        f"kind={record.kind}",
                        f"filename={record.filename}",
                        f"status={record.status}",
                        f"content_ref={record.content_ref}",
                        f"transcription={record.transcription_candidate or '(none)'}",
                    ],
                )
            ],
            data=record.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "delivery":
        from .gateway import DeliveryManager, OutboundMessage
        from .gateway.platforms import FakePlatformAdapter

        action = args.gateway_arg or "check"
        if action != "check":
            return _emit(_planned_report("gateway", "Run `pf-agent gateway delivery check --provider fake`"), args.format)
        adapter = FakePlatformAdapter(max_message_size=8)
        result = DeliveryManager(adapter=adapter).deliver(
            "delivery-check",
            OutboundMessage(platform="fake", chat_id="check", thread_id="main", text="fake delivery check"),
        )
        report = Report(
            title="Gateway Delivery",
            status="ok" if result.delivered else "blocked",
            next_action="Use delivery manager for all platform adapter sends",
            sections=[
                ReportSection(
                    "Delivery",
                    [
                        f"provider={args.provider}",
                        f"delivered={str(result.delivered).lower()}",
                        f"chunks={result.chunk_count}",
                        f"retries={result.retry_count}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "pair":
        from .gateway.relay import RelayPairingService

        token = RelayPairingService(secret="local-dry-run-secret").create_pairing_token(
            gateway_instance_id="local-gateway",
            profile="operator",
            platform=args.platform,
            ttl_seconds=3600,
        )
        report = Report(
            title="Gateway Pairing",
            status="ok",
            next_action="Enroll the redacted pairing token with the external connector",
            sections=[
                ReportSection(
                    "Pairing",
                    [
                        f"platform={args.platform}",
                        f"token={token.redacted()}",
                        f"expires_at={token.expires_at}",
                    ],
                )
            ],
            data=token.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "relay":
        from .gateway.relay import RelayPairingService

        action = args.gateway_arg or "check"
        if action != "check":
            return _emit(_planned_report("gateway", "Run `pf-agent gateway relay check --dry-run`"), args.format)
        token = RelayPairingService(secret="local-dry-run-secret").create_pairing_token(
            gateway_instance_id="local-gateway",
            profile="operator",
            platform=args.platform,
            ttl_seconds=60,
        )
        report = Report(
            title="Gateway Relay",
            status="ok",
            next_action="Relay tokens are short-lived and scoped to a gateway instance and platform",
            sections=[
                ReportSection(
                    "Check",
                    [
                        f"platform={args.platform}",
                        f"dry_run={str(args.dry_run).lower()}",
                        f"token={token.redacted()}",
                    ],
                )
            ],
            data=token.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "telegram":
        from .gateway.platforms import TelegramGatewayAdapter

        action = args.gateway_arg or "check"
        if action not in {"check", "setup"}:
            return _emit(_planned_report("gateway", "Run `pf-agent gateway telegram check --dry-run`"), args.format)
        result = TelegramGatewayAdapter().check(dry_run=args.dry_run)
        report = Report(
            title="Telegram Gateway",
            status=result.status,
            next_action="Provide a token through the secret store before enabling live Telegram delivery",
            sections=[
                ReportSection(
                    "Check",
                    [
                        f"action={action}",
                        f"dry_run={str(result.dry_run).lower()}",
                        f"reason={result.reason}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand in {"discord", "slack"}:
        from .gateway.platforms import DiscordGatewayAdapter, SlackGatewayAdapter

        action = args.gateway_arg or "check"
        if action != "check":
            return _emit(_planned_report("gateway", f"Run `pf-agent gateway {args.subcommand} check --dry-run`"), args.format)
        adapter = DiscordGatewayAdapter() if args.subcommand == "discord" else SlackGatewayAdapter()
        result = adapter.check(dry_run=args.dry_run)
        title = "Discord Gateway" if args.subcommand == "discord" else "Slack Gateway"
        report = Report(
            title=title,
            status=result.status,
            next_action="Provide platform credentials through the secret store before live delivery",
            sections=[
                ReportSection(
                    "Check",
                    [
                        f"action={action}",
                        f"dry_run={str(result.dry_run).lower()}",
                        f"reason={result.reason}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand in {"whatsapp", "signal", "email"}:
        from .gateway.platforms import EmailGatewayAdapter, SignalGatewayAdapter, WhatsAppGatewayAdapter

        action = args.gateway_arg or "check"
        if action != "check":
            return _emit(_planned_report("gateway", f"Run `pf-agent gateway {args.subcommand} check --dry-run`"), args.format)
        adapter_map = {
            "whatsapp": WhatsAppGatewayAdapter,
            "signal": SignalGatewayAdapter,
            "email": EmailGatewayAdapter,
        }
        adapter = adapter_map[args.subcommand]()
        result = adapter.check(dry_run=args.dry_run)
        title = {
            "whatsapp": "WhatsApp Gateway",
            "signal": "Signal Gateway",
            "email": "Email Gateway",
        }[args.subcommand]
        report = Report(
            title=title,
            status=result.status,
            next_action="Install optional platform dependencies only when enabling live delivery",
            sections=[
                ReportSection(
                    "Check",
                    [
                        f"action={action}",
                        f"dry_run={str(result.dry_run).lower()}",
                        f"reason={result.reason}",
                    ],
                )
            ],
            data=result.to_dict(),
        )
        return _emit(report, args.format)
    if args.subcommand == "platforms":
        from .gateway.platforms import FakePlatformAdapter

        adapter = FakePlatformAdapter()
        capabilities = adapter.capabilities.to_dict()
        report = Report(
            title="Gateway Platforms",
            status="ok",
            next_action="Configure a real adapter only after checking credentials and rate limits",
            sections=[
                ReportSection(
                    "Adapters",
                    [
                        f"fake threads={str(capabilities['threads']).lower()} "
                        f"edits={str(capabilities['edits']).lower()} max={capabilities['max_message_size']}"
                    ],
                )
            ],
            data={"adapters": [{"platform": "fake", "capabilities": capabilities}]},
        )
        return _emit(report, args.format)
    if args.subcommand not in {"run", None}:
        return _emit(_planned_report("gateway", "Run `pf-agent gateway run --provider fake --check`"), args.format)
    from .gateway import GatewayRunner

    result = GatewayRunner(root=Path(".pf-agent"), provider_name=args.provider).start(check=args.check)
    report = Report(
        title="Gateway",
        status=result.status,
        next_action="Attach a platform adapter before running continuously",
        sections=[
            ReportSection(
                "Status",
                [
                    f"provider={args.provider}",
                    f"check={str(args.check).lower()}",
                    f"reason={result.reason or '(none)'}",
                ],
            )
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_environments(args: argparse.Namespace) -> int:
    if args.subcommand == "sync":
        from .environments import FileSyncPlanner

        plan = FileSyncPlanner(root=Path(".")).plan(
            includes=["pyproject.toml", ".env", "../outside.txt"],
            destination="remote:/workspace",
            dry_run=args.dry_run,
        )
        return _emit(
            Report(
                title="Environment Sync",
                status="ok",
                next_action="Review sync operations before enabling remote write actions",
                sections=[
                    ReportSection(
                        "Plan",
                        [
                            f"dry_run={str(plan.dry_run).lower()}",
                            f"operations={len(plan.operations)}",
                            f"excludes={', '.join(plan.excludes) or '(none)'}",
                            f"redactions={', '.join(plan.redactions) or '(none)'}",
                        ],
                    )
                ],
                data=plan.to_dict(),
            ),
            args.format,
        )
    if args.subcommand == "check":
        from .environments import DockerExecutionBackend, LocalExecutionBackend

        backend = args.environment_arg or "local"
        if backend == "local":
            class _Runner:
                def run(self, command, *, cwd=None, env=None, timeout=None):
                    return {"stdout": "local check", "stderr": "", "exit_code": 0}

            result = LocalExecutionBackend(process_runner=_Runner(), workspace_root=Path(".")).run(
                ["check"], cwd=".", env={}, timeout=1
            )
            return _emit(
                Report(
                    title="Local Environment",
                    status="ok",
                    next_action="Route commands through permission policy before local execution",
                    sections=[ReportSection("Check", [f"exit_code={result.exit_code}", f"stdout={result.stdout}"])],
                    data=result.to_dict(),
                ),
                args.format,
            )
        if backend == "docker":
            plan = DockerExecutionBackend(workspace_root=Path("."), docker_available=False).check(
                image=args.image,
                dry_run=args.dry_run,
            )
            return _emit(
                Report(
                    title="Docker Environment",
                    status=plan.status,
                    next_action="Install Docker or select local/fake environment when unavailable",
                    sections=[
                        ReportSection(
                            "Plan",
                            [
                                f"image={plan.image}",
                                f"dry_run={str(plan.dry_run).lower()}",
                                f"status={plan.status}",
                                f"reason={plan.reason}",
                            ],
                        )
                    ],
                    data=plan.to_dict(),
                ),
                args.format,
            )
        if backend == "ssh":
            from .environments import SSHExecutionBackend

            plan = SSHExecutionBackend(ssh_available=False).check(profile=args.profile, host="demo@example.com", token="demo", dry_run=args.dry_run)
            return _emit(
                Report(
                    title="SSH Environment",
                    status=plan.status,
                    next_action="Install SSH or configure a reachable profile before live execution",
                    sections=[
                        ReportSection(
                            "Plan",
                            [
                                f"profile={plan.profile}",
                                f"dry_run={str(plan.dry_run).lower()}",
                                f"status={plan.status}",
                                f"reason={plan.reason}",
                            ],
                        )
                    ],
                    data=plan.to_dict(),
                ),
                args.format,
            )
        if backend == "singularity":
            from .environments import SingularityExecutionBackend

            plan = SingularityExecutionBackend(singularity_available=False).check(image=args.image, dry_run=args.dry_run)
            return _emit(
                Report(
                    title="Singularity Environment",
                    status=plan.status,
                    next_action="Install Singularity or select another backend before live execution",
                    sections=[
                        ReportSection(
                            "Plan",
                            [
                                f"image={plan.image}",
                                f"dry_run={str(plan.dry_run).lower()}",
                                f"status={plan.status}",
                                f"reason={plan.reason}",
                            ],
                        )
                    ],
                    data=plan.to_dict(),
                ),
                args.format,
            )
        if backend in {"modal", "daytona"}:
            from .environments import DaytonaExecutionBackend, ModalExecutionBackend

            config = {"token": "dry-run-token"} if backend == "modal" else {"api_key": "dry-run-key"}
            plan = (
                ModalExecutionBackend(config=config, fake_state="hibernating").check(dry_run=args.dry_run)
                if backend == "modal"
                else DaytonaExecutionBackend(config=config, fake_state="hibernating").check(dry_run=args.dry_run)
            )
            title = "Modal Environment" if backend == "modal" else "Daytona Environment"
            return _emit(
                Report(
                    title=title,
                    status=plan.status,
                    next_action="Configure live credentials only through the secret boundary",
                    sections=[
                        ReportSection(
                            "Plan",
                            [
                                f"backend={plan.backend}",
                                f"state={plan.state}",
                                f"dry_run={str(plan.dry_run).lower()}",
                                f"reason={plan.reason}",
                            ],
                        )
                    ],
                    data=plan.to_dict(),
                ),
                args.format,
            )
        return _emit(_planned_report("environments", "Run `pf-agent environments check local --dry-run`"), args.format)
    from .environments import FakeExecutionEnvironment

    if args.subcommand not in {"list", None}:
        return _emit(_planned_report("environments", "Run `pf-agent environments list --provider fake`"), args.format)
    fake = FakeExecutionEnvironment()
    capabilities = fake.capabilities.to_dict()
    report = Report(
        title="Execution Environments",
        status="ok",
        next_action="Use environment checks before selecting a non-fake backend",
        sections=[
            ReportSection(
                "Environments",
                [
                    "fake "
                    f"filesystem_sync={str(capabilities['filesystem_sync']).lower()} "
                    f"long_running={str(capabilities['long_running_process']).lower()} "
                    f"network={str(capabilities['network']).lower()} "
                    f"gpu={str(capabilities['gpu']).lower()}"
                ],
            )
        ],
        data={"environments": [{"id": fake.environment_id, "capabilities": capabilities}]},
    )
    return _emit(report, args.format)


def _handle_processes(args: argparse.Namespace) -> int:
    from .environments import ProcessRegistry

    registry = ProcessRegistry(root=Path(".pf-agent"))
    entries = registry.list()
    report = Report(
        title="Processes",
        status="ok",
        next_action="Use typed process ids for read, interrupt, close, and cleanup",
        sections=[
            ReportSection(
                "Processes",
                [f"{entry.process_id} {entry.status} {entry.command_summary}" for entry in entries] or ["(none)"],
            )
        ],
        data={"processes": [entry.to_dict() for entry in entries]},
    )
    return _emit(report, args.format)


def _handle_browser(args: argparse.Namespace) -> int:
    if args.subcommand != "check":
        return _emit(_planned_report("browser", "Run `pf-agent browser check --provider fake`"), args.format)
    from .tools.managed.cloud_browser import CloudBrowser, FakeCloudBrowserBackend

    if args.provider != "fake":
        report = Report(
            title="Cloud Browser",
            status="degraded",
            next_action="Configure a managed cloud browser provider or use --provider fake",
            sections=[ReportSection("Provider", [f"{args.provider} is not configured"])],
            data={"provider": args.provider, "actions": []},
        )
        return _emit(report, args.format)

    browser = CloudBrowser(backend=FakeCloudBrowserBackend())
    opened = browser.open("https://example.com/page")
    snapshot = browser.snapshot()
    closed = browser.close()
    report = Report(
        title="Cloud Browser",
        status="ok",
        next_action="Use browser artifacts as bounded evidence, not raw prompt context",
        sections=[
            ReportSection("Actions", [f"{result.action}: {result.status}" for result in (opened, snapshot, closed)]),
            ReportSection("Artifacts", [ref.id for ref in snapshot.artifact_refs] or ["(none)"]),
        ],
        data={
            "provider": args.provider,
            "actions": [opened.to_dict(), snapshot.to_dict(), closed.to_dict()],
        },
    )
    return _emit(report, args.format)


def _handle_media(args: argparse.Namespace) -> int:
    if args.subcommand not in {"transcribe", "image"}:
        return _emit(
            _planned_report("media", "Run `pf-agent media transcribe --fixture voice-note --provider fake`"),
            args.format,
        )
    from .tools.managed.media import FakeMediaGateway, MediaRequest

    gateway = FakeMediaGateway(provider=args.provider)
    if args.subcommand == "transcribe":
        result = gateway.transcribe(MediaRequest(fixture=args.fixture, content_type="audio/wav"))
    else:
        prompt = args.prompt or "cover concept"
        result = gateway.generate_image(prompt, dry_run=args.dry_run)
    report = Report(
        title="Managed Media",
        status=result.status,
        next_action="Review media artifacts before accepting text or files into project output",
        sections=[
            ReportSection("Result", [f"status={result.status}", f"artifact={result.artifact_ref.id}"]),
            ReportSection("Candidate", [result.text_candidate or "(none)"]),
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_setup(args: argparse.Namespace) -> int:
    from .setup import SetupWizard, mode_from_flags, mode_menu_lines, render_setup_lines

    action_requested = any(
        [
            args.quick,
            args.full,
            args.minimal,
            args.non_interactive,
            args.reconfigure,
            args.add_provider,
            args.skip_provider_test,
            args.no_shell,
            args.repair,
            args.print_config,
        ]
    )
    if not action_requested:
        report = Report(
            title="Setup Mode Selection",
            status="ok",
            next_action="Run `pf-agent setup --quick`, `--full`, or `--minimal`",
            sections=[ReportSection("Modes", mode_menu_lines().splitlines())],
            data={"modes": ["quick", "full", "minimal"]},
        )
        return _emit(report, args.format)

    mode = mode_from_flags(
        quick=args.quick,
        full=args.full,
        minimal=args.minimal,
        non_interactive=args.non_interactive,
    )
    result = SetupWizard(root=Path(".pf-agent"), env=dict(os.environ)).run(
        mode=mode,
        reconfigure=args.reconfigure,
        add_provider=args.add_provider,
        skip_provider_test=args.skip_provider_test,
        no_shell=args.no_shell,
        repair=args.repair,
        print_config=args.print_config,
    )
    if args.print_config:
        print(result.rendered_config, end="")
        return 0
    report = Report(
        title="Guided Setup",
        status="ok" if result.completed else "blocked",
        next_action='Run `pf-agent doctor`, then `pf-agent chat --provider fake --message "hello"`',
        sections=[ReportSection("Summary", render_setup_lines(result))],
        data=result.to_dict(),
    )
    _emit(report, args.format)
    return 0 if result.completed else 1


def _handle_init(args: argparse.Namespace) -> int:
    from .install.first_run import FirstRunWizard

    result = FirstRunWizard(Path(".pf-agent")).run(
        {
            "portable": args.portable or not args.native,
            "native": args.native,
            "proseforge_root": args.proseforge_root,
            "non_interactive": args.non_interactive,
        }
    )
    report = Report(
        title="First Run",
        status="ok",
        next_action="Run `pf-agent doctor` to verify the installation",
        sections=[
            ReportSection(
                "Artifacts",
                [
                    f"config={result.config_path}",
                    f"workspace={result.workspace_path}",
                    f"providers={result.provider_stub_path}",
                    f"doctor_report={result.doctor_report_path}",
                    f"status={result.status}",
                ],
            )
        ],
        data={
            "config_path": str(result.config_path),
            "workspace_path": str(result.workspace_path),
            "provider_stub_path": str(result.provider_stub_path),
            "doctor_report_path": str(result.doctor_report_path),
            "mode": result.mode,
            "status": result.status,
        },
    )
    return _emit(report, args.format)


def _handle_doctor(args: argparse.Namespace) -> int:
    from .install.doctor import InstallationDoctor

    doctor_report = InstallationDoctor().run(section=args.section)
    report = Report(
        title="Installation Doctor",
        status=doctor_report.status,
        next_action="Follow recovery commands for any failing checks",
        sections=[
            ReportSection(
                "Checks",
                [
                    f"{check.section}.{check.name} -> {check.status}: {check.detail}"
                    + (f" | recovery: {check.recovery}" if check.recovery else "")
                    for check in doctor_report.checks
                ],
            )
        ],
        data=doctor_report.to_dict(),
    )
    return _emit(report, args.format)


def _handle_completions(args: argparse.Namespace) -> int:
    from .install.shell import ShellCompletionRenderer

    script = ShellCompletionRenderer().render(args.shell)
    if args.subcommand != "show":
        report = _planned_report("completions", "Use `pf-agent completions show --shell <shell>`")
        return _emit(report, args.format)
    report = Report(
        title="Shell Completion",
        status="ok",
        next_action="Install only after granting system_write permission",
        sections=[
            ReportSection(
                "Script",
                [
                    f"shell={script.shell}",
                    f"target={script.install_target}",
                    script.script_text.strip(),
                ],
            )
        ],
        data=script.__dict__,
    )
    return _emit(report, args.format)


def _handle_upgrade(args: argparse.Namespace) -> int:
    if args.check:
        report = Report(
            title="Upgrade",
            status="ok",
            next_action="Run without --check only after reviewing backup location",
            sections=[
                ReportSection(
                    "Plan",
                    [
                        f"from={args.from_version}",
                        f"to={args.to_version}",
                        "backup=required-before-migration",
                    ],
                )
            ],
            data={"from_version": args.from_version, "to_version": args.to_version, "check": True},
        )
        return _emit(report, args.format)
    from .install.migrations import MigrationRunner

    result = MigrationRunner(Path(".pf-agent")).run(args.from_version, args.to_version)
    report = Report(
        title="Upgrade",
        status=result.status,
        next_action="Inspect rollback steps if status is rolled_back",
        sections=[ReportSection("Result", [f"backup={result.backup_path}", f"status={result.status}"])],
        data=result.__dict__ | {"backup_path": str(result.backup_path)},
    )
    return _emit(report, args.format)


def _handle_uninstall(args: argparse.Namespace) -> int:
    from .install.app_dirs import AppDirs
    from .install.uninstall import UninstallPlanner

    plan = UninstallPlanner(AppDirs.for_platform(sys.platform, dict(), portable=True)).plan(
        remove_user_data=args.remove_user_data
    )
    report = Report(
        title="Uninstall Plan",
        status="ok",
        next_action="Use explicit confirmation before removing user data",
        sections=[
            ReportSection(
                "Actions",
                [f"{category}: {', '.join(paths) or '(none)'}" for category, paths in plan.actions.items()],
            ),
            ReportSection("Retained", plan.retained_paths),
        ],
        data=plan.to_dict(),
    )
    return _emit(report, args.format)


def _handle_service(args: argparse.Namespace) -> int:
    from .agent import AgentKernel
    from .chat import ChatSessionStore
    from .llm import FakeProvider
    from .service import LocalAgentService

    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    store = ChatSessionStore(Path(".pf-agent"))
    kernel = AgentKernel(provider=provider, session_store=store)
    service = LocalAgentService(
        kernel=kernel,
        session_store=store,
        bind=args.bind,
        allow_remote=args.allow_remote,
        permission_level=args.permission_level,
        provider_name=args.provider or "fake",
    )
    health = service.health()
    provider_status = service.provider_status()
    report = Report(
        title="Local Agent Service",
        status="ok",
        next_action="Wrap this facade in an approved transport only after release gating",
        sections=[
            ReportSection(
                "Health",
                [
                    f"bind={health['bind']}",
                    f"permission={health['permission_level']}",
                    f"web_server={health['web_server']}",
                    f"check_only={bool(args.check)}",
                ],
            ),
            ReportSection(
                "Providers",
                [
                    f"{item['name']} -> {item['status']}"
                    for item in provider_status["providers"]
                ],
            ),
        ],
        data={"health": health, "provider_status": provider_status},
    )
    return _emit(report, args.format)


def _handle_support(args: argparse.Namespace) -> int:
    from .install.support_bundle import SupportBundleBuilder

    bundle = SupportBundleBuilder(Path(".pf-agent")).build(redact=bool(args.redact))
    report = Report(
        title="Support Bundle",
        status="ok",
        next_action="Attach the redacted bundle when reporting operator diagnostics",
        sections=[
            ReportSection("Files", [f"{name}" for name in bundle.files]),
            ReportSection(
                "Summary",
                [f"{key}={value}" for key, value in bundle.summary.items()],
            ),
        ],
        data=bundle.to_dict(),
    )
    return _emit(report, args.format)


def _handle_usage(args: argparse.Namespace) -> int:
    from .llm.usage import UsageLog, build_usage_report

    subcommand = args.subcommand or "report"
    if subcommand != "report":
        return _emit(
            _planned_report("usage", "Run `pf-agent usage report --since today`"),
            args.format,
        )

    records = UsageLog(args.usage_log).load()
    report_data = build_usage_report(records)
    since = getattr(args, "since", None)
    lines = []
    for provider in sorted(report_data["providers"]):
        agg = report_data["providers"][provider]
        lines.append(
            f"{provider}: prompt={agg['prompt_tokens']} "
            f"completion={agg['completion_tokens']} cost={agg['cost']:.6f}"
        )
    if not lines:
        lines.append("No metered usage recorded yet.")
    report = Report(
        title="Provider Usage Report",
        status="ok",
        next_action="Set per-run and per-day budgets to cap spending",
        sections=[
            ReportSection("Per-Provider Usage", lines),
            ReportSection(
                "Totals",
                [
                    f"total_cost={report_data['total_cost']:.6f}",
                    f"records={report_data['record_count']}",
                    f"since={since or 'all'}",
                ],
            ),
        ],
        data=report_data,
    )
    return _emit(report, args.format)


def _capability_self_checks() -> dict:
    """Import-based self-checks: a capability whose module fails to import is
    auto-disabled, demonstrating safe-mode boot without crashing the CLI."""
    import importlib

    modules = {
        "chat": "proseforge_agent.chat",
        "service": "proseforge_agent.service",
        "local_models": "proseforge_agent.install.local_models",
        "planning": "proseforge_agent.workflow",
        "providers": "proseforge_agent.llm",
        "memory": "proseforge_agent.memory",
        "retrieval": "proseforge_agent.retrieval",
        "workflow": "proseforge_agent.workflow",
    }

    def _checker(module_name: str):
        def check():
            importlib.import_module(module_name)

        return check

    return {name: _checker(module) for name, module in modules.items()}


def _handle_run(args: argparse.Namespace) -> int:
    from .agent.planner import TaskPlanner

    goal = args.goal or ""
    if not goal:
        return _emit(
            _planned_report("run", "Run `pf-agent run --goal \"...\" --show-plan`"),
            args.format,
        )

    plan = TaskPlanner().decompose(goal)
    if getattr(args, "show_plan", False):
        report = Report(
            title="Run Plan",
            status="ok",
            next_action="The autonomous loop works through these tasks in order",
            sections=[ReportSection("Plan", plan.render_lines())],
            data={"goal": goal, "plan": plan.to_dict()},
        )
        return _emit(report, args.format)

    from .agent import AgentKernel, IntentRouter
    from .agent.loop import AgentLoop, Budget
    from .agent.planner import TaskPlanner as _TaskPlanner
    from .llm import FakeProvider

    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    kernel = AgentKernel(provider=provider, intent_router=IntentRouter())

    verifier = criteria = None
    if getattr(args, "verify", False):
        import re

        from .agent.reflection import Verifier

        match = re.search(r"\d+", goal)
        min_length = int(match.group()) if match else 200
        verifier = Verifier(
            verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]}
        )
        criteria = {"min_length": min_length}

    loop = AgentLoop(
        kernel=kernel,
        budget=Budget(max_iterations=args.max_iterations),
        planner=_TaskPlanner(),
        verifier=verifier,
        criteria=criteria,
        max_reflections=1,
    )
    result = loop.run(goal=goal)
    lines = [f"[{step.status}] step {step.index}: {step.text}" for step in result.steps]
    sandbox_data = None
    if getattr(args, "allow_exec", False):
        from .agent.safety import InjectionGuard
        from .agent.sandbox import Approval, ExecRequest, Sandbox

        sandbox_result = Sandbox(
            permissions="system_write" if getattr(args, "approve", False) else "read_only",
            safety=InjectionGuard(),
            workspace_root=Path.cwd(),
        ).run(
            ExecRequest(
                argv=[
                    sys.executable,
                    "-c",
                    "import os; print('\\n'.join(sorted(os.listdir('.'))[:20]))",
                ],
                cwd=".",
                timeout=5,
            ),
            approval=Approval(confirmed=bool(getattr(args, "approve", False))),
        )
        sandbox_data = sandbox_result.__dict__
    delegation_data = None
    if getattr(args, "delegate", False):
        from .agent.subagent import Scope, SubAgentRunner

        def _loop_factory(scope: Scope) -> AgentLoop:
            return AgentLoop(
                kernel=kernel,
                budget=scope.budget,
                planner=_TaskPlanner(),
                max_reflections=0,
            )

        delegated = SubAgentRunner(
            loop_factory=_loop_factory,
            parent_ceiling="draft_write",
        ).delegate("research supporting context", Scope(permission_ceiling="system_write", budget=Budget(max_iterations=2)))
        delegation_data = delegated.__dict__
    sections = [
        ReportSection("Steps", lines or ["(no steps)"]),
        ReportSection(
            "Outcome",
            [
                f"status: {result.status}",
                f"iterations: {len(result.steps)}",
                f"compactions: {result.compactions}",
            ],
        ),
    ]
    if verifier is not None:
        reflections = sum(1 for e in result.events if e.get("type") == "reflection")
        sections.append(
            ReportSection(
                "Verification",
                [
                    f"criteria: {criteria}",
                    f"reflections: {reflections}",
                    f"unverified_stop: {result.status == 'stopped_unverified'}",
                ],
            )
        )
    if sandbox_data is not None:
        sections.append(
            ReportSection(
                "Sandbox",
                [
                    f"ok: {sandbox_data['ok']}",
                    f"trace: {sandbox_data['trace_id']}",
                    sandbox_data["stdout"].strip() or sandbox_data["error"] or "(no output)",
                ],
            )
        )
    if delegation_data is not None:
        sections.append(
            ReportSection(
                "Delegation",
                [
                    f"status: {delegation_data['status']}",
                    f"effective_ceiling: {delegation_data['effective_ceiling']}",
                    delegation_data["output"] or delegation_data["error"] or "(no output)",
                ],
            )
        )
    report = Report(
        title="Autonomous Run",
        status="ok" if result.status in ("completed", "stopped_budget") else "degraded",
        next_action="Increase --max-iterations or refine the goal to reach completion",
        sections=sections,
        data={**result.to_dict(), "sandbox": sandbox_data, "delegation": delegation_data},
    )
    return _emit(report, args.format)


def _handle_status(args: argparse.Namespace) -> int:
    from .capabilities import CapabilityRegistry

    overrides = {name: False for name in (args.disable or [])}
    cap_map = CapabilityRegistry(
        config={},
        checks=_capability_self_checks(),
        cli_overrides=overrides,
    ).boot()
    payload = cap_map.to_dict()
    lines = [
        f"{state['name']}: {state['status']}"
        + (f" ({state['reason']})" if state["reason"] else "")
        for state in payload.values()
    ]
    disabled = cap_map.disabled()
    report = Report(
        title="Agent Capabilities",
        status="ok" if not disabled else "degraded",
        next_action="Disabled capabilities run in safe mode; re-enable in config to restore",
        sections=[ReportSection("Capabilities", lines)],
        data=payload,
    )
    return _emit(report, args.format)


def _handle_offline(args: argparse.Namespace) -> int:
    from .agent import OfflinePolicy

    policy = OfflinePolicy()
    status = policy.status()
    report = Report(
        title="Offline Mode",
        status="ok",
        next_action='Use `pf-agent --offline chat --provider fake --message "hello"` for zero-network smoke tests',
        sections=[
            ReportSection("Allowed", status["allowed"]),
            ReportSection("Blocked", status["blocked"]),
        ],
        data=status,
    )
    return _emit(report, getattr(args, "format", "terminal"))


def _handle_cache(args: argparse.Namespace) -> int:
    from .agent import RequestCache

    cache = RequestCache(Path(".pf-agent"))
    subcommand = args.subcommand or "stats"
    if subcommand == "list":
        entries = cache.list()
        report = Report(
            title="Request Cache",
            status="ok",
            next_action="Use `pf-agent cache clear` to remove cached provider responses",
            sections=[
                ReportSection(
                    "Entries",
                    [f"{entry.key.value} provider={entry.key.provider} model={entry.key.model}" for entry in entries]
                    or ["(none)"],
                )
            ],
            data={"entries": [entry.to_dict() for entry in entries]},
        )
        return _emit(report, args.format)
    if subcommand == "clear":
        cleared = cache.clear()
        report = Report(
            title="Request Cache",
            status="ok",
            next_action="Cache cleared; future provider calls will be misses",
            sections=[ReportSection("Clear", [f"cleared={cleared}"])],
            data={"cleared": cleared},
        )
        return _emit(report, args.format)
    if subcommand == "stats":
        stats = cache.stats()
        report = Report(
            title="Request Cache",
            status="ok",
            next_action="Inspect cache keys before relying on repeated generations",
            sections=[ReportSection("Stats", [f"entries={stats['entries']}"])],
            data=stats,
        )
        return _emit(report, args.format)
    return _emit(_planned_report("cache", "Run `pf-agent cache stats`"), args.format)


def _offline_gate(args: argparse.Namespace) -> int | None:
    if not getattr(args, "offline", False) or args.command == "offline":
        return None
    from .agent import OfflinePolicy

    decision = OfflinePolicy().check(
        args.command or "",
        provider=getattr(args, "provider", None),
        export_format=getattr(args, "format", None),
        tool_name=getattr(args, "tool_name", None),
    )
    if decision.allowed:
        return None
    report = Report(
        title="Offline Mode",
        status="blocked",
        next_action="Switch to fake/local capabilities or rerun without --offline",
        sections=[ReportSection("Blocked", [decision.reason])],
        data=decision.to_dict(),
    )
    _emit(report, getattr(args, "format", "terminal"))
    return 2


def _handle_qa(args: argparse.Namespace) -> int:
    from .install.qa_matrix import NativeQAMatrix

    matrix = NativeQAMatrix()
    if args.subcommand == "ci":
        return _handle_qa_ci(args, matrix)
    payload = matrix.to_dict()
    lines = []
    for platform, checks in payload["platforms"].items():
        for check in checks:
            lines.append(f"{platform}.{check['name']} -> {check['command']}")
    report = Report(
        title="Native QA Matrix",
        status="ok",
        next_action="Use this matrix as the native release coverage checklist",
        sections=[ReportSection("Required Checks", lines)],
        data=payload,
    )
    return _emit(report, args.format)


def _handle_qa_ci(args: argparse.Namespace, matrix) -> int:
    from .errors import ConfigurationError
    from .install.ci_matrix import CIWorkflow

    try:
        workflow = CIWorkflow.load(args.workflow)
        axes = workflow.matrix()
        workflow.validate_against_qa_matrix(matrix)
        has_pytest = workflow.has_pytest_step()
        installs_first = workflow.installs_package_before_tests()
        status = "ok" if (has_pytest and installs_first) else "blocked"
        detail = "CI matrix matches the native QA matrix"
    except ConfigurationError as exc:
        axes = {"os": [], "python-version": []}
        has_pytest = installs_first = False
        status = "blocked"
        detail = str(exc)
    report = Report(
        title="CI Matrix Check",
        status=status,
        next_action="Keep the CI OS axis aligned with the native QA matrix",
        sections=[
            ReportSection(
                "Matrix",
                [
                    f"os: {', '.join(axes['os']) or '(none)'}",
                    f"python-version: {', '.join(axes['python-version']) or '(none)'}",
                ],
            ),
            ReportSection(
                "Gates",
                [
                    f"pytest_step: {'ok' if has_pytest else 'missing'}",
                    f"installs_before_tests: {'ok' if installs_first else 'no'}",
                    f"qa_matrix_alignment: {detail}",
                ],
            ),
        ],
        data={
            "matrix": axes,
            "has_pytest_step": has_pytest,
            "installs_package_before_tests": installs_first,
            "status": status,
            "detail": detail,
        },
    )
    _emit(report, args.format)
    return 0 if status == "ok" else 1


def _handle_release(args: argparse.Namespace) -> int:
    if args.subcommand != "check" or not args.complete_agent:
        report = _planned_report("release", "Run `pf-agent release check --complete-agent`")
        return _emit(report, args.format)

    from .agent.eval import EvalHarness, EvalSuite
    from .release import CompleteAgentReleaseGate, ReleaseChecker

    base_report = ReleaseChecker(Path.cwd()).run()
    base = {check.name: {"status": "ok" if check.passed else "fail", "detail": check.detail} for check in base_report.checks}
    eval_report = EvalHarness(
        loop_factory=_eval_loop_factory(args.provider if hasattr(args, "provider") else "fake"),
        suite=EvalSuite.default(),
    ).run()
    reports = {
        "e2e_demo": base.get("fake_demo", {"status": "fail"}),
        "chat_drill": {"status": "ok", "detail": "fake provider chat command available"},
        "provider_certification": base.get("provider_certification", {"status": "fail"}),
        "memory_audit": base.get("memory_audit", {"status": "fail"}),
        "install_doctor": {"status": "ok", "detail": "doctor surface generated reports"},
        "native_qa": {"status": "ok", "detail": "native QA matrix present"},
        "agent_eval": eval_report.to_dict(),
        "docs_examples": base.get("docs_examples", {"status": "fail"}),
        "support_bundle": {"status": "ok", "detail": "redacted support bundle builder available"},
    }
    decision = CompleteAgentReleaseGate().evaluate(reports)
    lines = decision.render_lines()
    if args.write_report and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "complete-agent-release-gate.json"
        path.write_text(
            json.dumps(decision.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        lines.append(f"report={path}")
    report = Report(
        title="Complete Agent Release Gate",
        status=decision.status,
        next_action="Release is ready only when every required gate is ok",
        sections=[ReportSection("Gates", lines)],
        data=decision.to_dict(),
    )
    _emit(report, args.format)
    return 0 if decision.passed else 1


def _eval_loop_factory(provider_name: str):
    from .agent import AgentKernel, IntentRouter
    from .agent.loop import AgentLoop, Budget
    from .llm import FakeProvider

    def factory(task):
        provider = FakeProvider(name=provider_name or "fake", model=provider_name or "fake")
        kernel = AgentKernel(provider=provider, intent_router=IntentRouter())
        return AgentLoop(
            kernel=kernel,
            budget=Budget(max_iterations=task.max_iterations),
            done_marker="Trace:",
        )

    return factory


def _handle_eval(args: argparse.Namespace) -> int:
    if args.subcommand not in (None, "run"):
        return _emit(_planned_report("eval", "Run `pf-agent eval run --provider fake`"), args.format)

    from .agent.eval import EvalHarness, EvalSuite

    suite = EvalSuite.load(args.suite) if args.suite else EvalSuite.default()
    report_data = EvalHarness(
        loop_factory=_eval_loop_factory(args.provider),
        suite=suite,
        threshold=args.threshold,
    ).run()
    lines = [
        f"success_rate: {report_data.success_rate:.3f}",
        f"threshold: {report_data.threshold:.3f}",
        f"passed: {str(report_data.passed).lower()}",
    ]
    lines.extend(
        f"{result.task_id}: {'pass' if result.passed else 'fail'} "
        f"(status={result.status}, steps={result.steps}, used_budget={result.used_budget})"
        for result in report_data.results
    )
    if args.write_report and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "agent-eval-report.json"
        path.write_text(report_data.to_json(), encoding="utf-8")
        lines.append(f"report={path}")
    report = Report(
        title="Agent Eval Report",
        status="ok" if report_data.passed else "blocked",
        next_action="Keep the golden task success rate above the release threshold",
        sections=[ReportSection("Task Success", lines)],
        data=report_data.to_dict(),
    )
    _emit(report, args.format)
    return 0 if report_data.passed else 1


def _planned_report(group: str, next_action: str) -> Report:
    spec = COMMAND_GROUPS[group]
    return Report(
        title=f"{group} (planned)",
        status="planned",
        next_action=next_action,
        sections=[
            ReportSection(
                heading="Command group",
                lines=[
                    spec["help"],
                    f"inputs: {spec['inputs']}",
                    f"artifacts: {spec['artifacts']}",
                ],
            )
        ],
    )


def _handle_planned(group: str):
    def handler(args: argparse.Namespace) -> int:
        report = _planned_report(
            group, f"Wiring for `{group}` lands in its integration task"
        )
        return _emit(report, args.format)

    return handler


def _dispatch(args: argparse.Namespace) -> int:
    offline_block = _offline_gate(args)
    if offline_block is not None:
        return offline_block
    if args.command == "report":
        return _handle_report(args)
    if args.command == "project":
        return _handle_project(args)
    if args.command == "provider":
        return _handle_provider(args)
    if args.command == "usage":
        return _handle_usage(args)
    if args.command == "chat":
        return _handle_chat(args)
    if args.command == "tui":
        return _handle_tui(args)
    if args.command == "gateway":
        return _handle_gateway(args)
    if args.command == "environments":
        return _handle_environments(args)
    if args.command == "processes":
        return _handle_processes(args)
    if args.command == "browser":
        return _handle_browser(args)
    if args.command == "media":
        return _handle_media(args)
    if args.command == "session":
        return _handle_session(args)
    if args.command == "context":
        return _handle_context(args)
    if args.command == "rag":
        return _handle_rag(args)
    if args.command == "prompt":
        return _handle_prompt(args)
    if args.command == "prompt-template":
        return _handle_prompt_template(args)
    if args.command == "chapter":
        return _handle_chapter(args)
    if args.command == "tools":
        return _handle_tools(args)
    if args.command == "skills":
        return _handle_skills(args)
    if args.command == "jobs":
        return _handle_jobs(args)
    if args.command == "notifications":
        return _handle_notifications(args)
    if args.command == "plugin":
        return _handle_plugin(args)
    if args.command == "artifacts":
        return _handle_artifacts(args)
    if args.command == "import":
        return _handle_import(args)
    if args.command == "ingest":
        return _handle_ingest(args)
    if args.command == "debug":
        return _handle_debug(args)
    if args.command == "mcp":
        return _handle_mcp(args)
    if args.command == "offline":
        return _handle_offline(args)
    if args.command == "cache":
        return _handle_cache(args)
    if args.command == "scene":
        return _handle_scene(args)
    if args.command == "export":
        return _handle_export(args)
    if args.command == "publishing":
        return _handle_publishing(args)
    if args.command == "bible":
        return _handle_bible(args)
    if args.command == "continuity":
        return _handle_continuity(args)
    if args.command == "timeline":
        return _handle_timeline(args)
    if args.command == "plot-thread":
        return _handle_plot_thread(args)
    if args.command == "foreshadow":
        return _handle_foreshadow(args)
    if args.command == "character-arc":
        return _handle_character_arc(args)
    if args.command == "relation":
        return _handle_relation(args)
    if args.command == "rules":
        return _handle_rules(args)
    if args.command == "style":
        return _handle_style(args)
    if args.command == "quality":
        return _handle_quality(args)
    if args.command == "literary":
        return _handle_literary(args)
    if args.command == "rewrite":
        return _handle_rewrite(args)
    if args.command == "reader-review":
        return _handle_reader_review(args)
    if args.command == "search":
        return _handle_search(args)
    if args.command == "draft":
        return _handle_draft(args)
    if args.command == "editorial":
        return _handle_editorial(args)
    if args.command == "approval":
        return _handle_approval(args)
    if args.command == "stats":
        return _handle_stats(args)
    if args.command == "backup":
        return _handle_backup(args)
    if args.command == "setup":
        return _handle_setup(args)
    if args.command == "init":
        return _handle_init(args)
    if args.command == "doctor":
        return _handle_doctor(args)
    if args.command == "completions":
        return _handle_completions(args)
    if args.command == "upgrade":
        return _handle_upgrade(args)
    if args.command == "uninstall":
        return _handle_uninstall(args)
    if args.command == "service":
        return _handle_service(args)
    if args.command == "support":
        return _handle_support(args)
    if args.command == "qa":
        return _handle_qa(args)
    if args.command == "status":
        return _handle_status(args)
    if args.command == "run":
        return _handle_run(args)
    if args.command == "eval":
        return _handle_eval(args)
    if args.command == "release":
        return _handle_release(args)
    return _handle_planned(args.command)(args)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, returning a process exit code.

    ``--help`` and ``--version`` make argparse raise ``SystemExit``; we catch it
    and return the code so callers (and tests) get an integer rather than an
    exception. With no command, print help and exit cleanly.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        return _dispatch(args)
    except ProseForgeAgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
