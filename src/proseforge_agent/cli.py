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
    "chat": {
        "help": "Run one-shot agent chat and intent classification",
        "inputs": "message, mode, provider",
        "artifacts": "agent turn report",
    },
    "tools": {
        "help": "List internal tools and permission levels",
        "inputs": "tool registry",
        "artifacts": "tool registry report",
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

    shared = _output_parser()
    subparsers = parser.add_subparsers(dest="command", metavar="<group>")
    for name, spec in COMMAND_GROUPS.items():
        group = subparsers.add_parser(
            name,
            parents=[shared],
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
            group.add_argument("--provider", default="fake", help="chat provider")
            group.add_argument("--no-project", action="store_true", help="do not bind a project")
            group.add_argument("--project", default=None, help="project slug")
            group.add_argument("--mode", default="general_chat", help="conversation mode")
            group.add_argument(
                "--permission-level",
                default="read_only",
                help="maximum permission level for this turn",
            )
        if name == "tools":
            group.add_argument(
                "--include-permissions",
                action="store_true",
                help="include permission levels in the tool list",
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
    if args.subcommand == "probe":
        return _handle_provider_probe(args)
    if args.subcommand == "routes":
        return _handle_provider_routes(args)
    if args.subcommand == "certify":
        return _handle_provider_certify(args)
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
    if not args.message:
        report = _planned_report("chat", "Pass --message for one-shot chat")
        return _emit(report, args.format)
    from .agent import AgentKernel, AgentTurnRequest, IntentRouter
    from .llm import FakeProvider

    project_slug = None if args.no_project else args.project
    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    kernel = AgentKernel(provider=provider, intent_router=IntentRouter())
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=args.mode,
            project_slug=project_slug,
            permission_level=args.permission_level,
        )
    )
    report = Report(
        title="Agent Chat",
        status="ok",
        next_action="Use chat sessions in Task 34 for durable transcripts",
        sections=[ReportSection("Response", result.text.splitlines())],
        data={
            "trace_id": result.trace_id,
            "intent": result.intent.__dict__,
            "tool_calls": [call.__dict__ for call in result.tool_calls],
            "evidence_refs": result.evidence_refs,
            "memory_candidate_ids": result.memory_candidate_ids,
            "events": result.events,
        },
    )
    return _emit(report, args.format)


def _handle_tools(args: argparse.Namespace) -> int:
    from .agent import default_tool_registry

    registry = default_tool_registry()
    lines = []
    for tool in registry.list():
        if args.include_permissions:
            lines.append(f"{tool.name} -> {tool.permission} ({tool.description})")
        else:
            lines.append(f"{tool.name} ({tool.description})")
    report = Report(
        title="Agent Tools",
        status="ok",
        next_action="Authorize tool calls through PermissionPolicy",
        sections=[ReportSection("Tools", lines)],
        data={
            "tools": [
                {
                    "name": tool.name,
                    "permission": tool.permission,
                    "description": tool.description,
                    "enabled": tool.enabled,
                }
                for tool in registry.list()
            ]
        },
    )
    return _emit(report, args.format)


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
    if args.command == "report":
        return _handle_report(args)
    if args.command == "provider":
        return _handle_provider(args)
    if args.command == "chat":
        return _handle_chat(args)
    if args.command == "tools":
        return _handle_tools(args)
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
